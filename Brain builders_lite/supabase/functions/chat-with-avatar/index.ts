// @ts-ignore
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.84.0";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

    // Auth check using anon client
    const anonClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    );

    const { data: { user } } = await anonClient.auth.getUser();
    if (!user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const { avatarId, conversationId, message } = await req.json();

    if (!avatarId || !message) {
      return new Response(JSON.stringify({ error: 'avatarId and message are required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get avatar + mentor profile
    const { data: avatar, error: avatarError } = await supabaseClient
      .from('mentor_avatars')
      .select('*, mentor_profiles(*)')
      .eq('id', avatarId)
      .single();

    if (avatarError || !avatar || avatar.status !== 'ready') {
      return new Response(JSON.stringify({ error: 'Avatar not found or not ready' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get or create conversation
    let convId = conversationId;
    if (!convId) {
      const { data: newConv, error: convError } = await supabaseClient
        .from('avatar_conversations')
        .insert({ user_id: user.id, avatar_id: avatarId })
        .select()
        .single();

      if (convError) {
        return new Response(JSON.stringify({ error: 'Failed to create conversation' }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      convId = newConv.id;
    }

    // Save user message
    await supabaseClient.from('avatar_messages').insert({
      conversation_id: convId,
      role: 'user',
      content: message
    });

    const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY');
    if (!OPENAI_API_KEY) {
      return new Response(JSON.stringify({ error: 'OpenAI API key not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Generate embedding for user query
    const embeddingResponse = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'text-embedding-3-small',
        input: message,
      }),
    });

    if (!embeddingResponse.ok) {
      console.error('OpenAI embeddings error:', await embeddingResponse.text());
      return new Response(JSON.stringify({ error: 'Failed to process query' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const embeddingData = await embeddingResponse.json();
    const queryEmbedding = embeddingData.data[0].embedding;

    // Similarity search in avatar knowledge base
    const { data: relevantKnowledge } = await supabaseClient.rpc(
      'match_avatar_knowledge',
      {
        query_embedding: queryEmbedding,
        match_threshold: 0.5,
        match_count: 5,
        avatar_id_param: avatarId
      }
    );

    // Also fetch active mentor_knowledge_base entries (custom content)
    const { data: customKnowledge } = await supabaseClient
      .from('mentor_knowledge_base')
      .select('title, content, content_type')
      .eq('mentor_id', avatar.mentor_id)
      .eq('is_active', true)
      .limit(10);

    // Build context
    const ragContext = relevantKnowledge && relevantKnowledge.length > 0
      ? relevantKnowledge.map((k: any) => k.content).join('\n\n')
      : '';

    const customContext = customKnowledge && customKnowledge.length > 0
      ? customKnowledge.map((k: any) => `[${k.content_type.toUpperCase()}] ${k.title}:\n${k.content}`).join('\n\n')
      : '';

    const fullContext = [ragContext, customContext].filter(Boolean).join('\n\n---\n\n')
      || 'No specific knowledge found for this query.';

    // Get recent conversation history (last 10 messages)
    const { data: recentMessages } = await supabaseClient
      .from('avatar_messages')
      .select('role, content')
      .eq('conversation_id', convId)
      .order('created_at', { ascending: true })
      .limit(10);

    const conversationHistory = (recentMessages || []).map((m: any) => ({
      role: m.role,
      content: m.content
    }));

    const mentor = avatar.mentor_profiles;
    const systemPrompt = `You are an AI avatar representing ${mentor.name}, a ${mentor.title}.

Your personality: ${avatar.personality_traits?.join(', ') || 'professional, helpful, knowledgeable'}
Your expertise: ${avatar.expertise_areas?.join(', ') || mentor.expertise?.join(', ') || 'general mentorship'}
Bio: ${avatar.bio_summary || mentor.bio}

INSTRUCTIONS:
- Respond as if you ARE the mentor, using first person ("I", "my")
- Be concise, helpful, and engaging
- When relevant, mention courses, services, or video answers
- If appropriate, suggest booking a consultation
- If you don't know something specific, be honest but stay in character
- Do not make up facts about the mentor's background

Knowledge base context:
${fullContext}`;

    // Call OpenAI chat completion
    const chatResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          ...conversationHistory,
          { role: 'user', content: message }
        ],
        max_tokens: 500,
        temperature: 0.7,
      }),
    });

    if (!chatResponse.ok) {
      const errText = await chatResponse.text();
      console.error('OpenAI chat error:', chatResponse.status, errText);
      return new Response(JSON.stringify({ error: 'AI service temporarily unavailable' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const chatData = await chatResponse.json();
    const assistantMessage = chatData.choices[0].message.content;
    const tokensUsed = chatData.usage?.total_tokens || 0;

    // Save assistant message
    await supabaseClient.from('avatar_messages').insert({
      conversation_id: convId,
      role: 'assistant',
      content: assistantMessage,
      metadata: { tokens_used: tokensUsed }
    });

    // Track usage
    await supabaseClient.from('avatar_usage_stats').insert({
      avatar_id: avatarId,
      conversation_id: convId,
      user_id: user.id,
      tokens_used: tokensUsed,
      messages_count: 1
    });

    return new Response(JSON.stringify({
      conversationId: convId,
      message: assistantMessage,
      mentorName: mentor.name,
      mentorImage: avatar.photo_urls?.[0] || mentor.image_url
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in chat-with-avatar:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
