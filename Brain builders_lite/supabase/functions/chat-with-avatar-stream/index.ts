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

    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

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

    // Check message limit (default: 20 free messages per user per avatar)
    const MESSAGE_LIMIT = 20;
    const { data: msgCount } = await supabaseClient.rpc('get_user_message_count', {
      p_avatar_id: avatarId,
      p_user_id: user.id,
    });
    if ((msgCount || 0) >= MESSAGE_LIMIT) {
      return new Response(JSON.stringify({
        error: 'Message limit reached',
        limit: MESSAGE_LIMIT,
        message: `You've reached the limit of ${MESSAGE_LIMIT} messages with this avatar. Book a session with the mentor for personalized help.`
      }), {
        status: 429,
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

    // Generate embedding for query
    const embeddingResponse = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'text-embedding-3-small', input: message }),
    });

    let context = 'No specific knowledge found.';
    if (embeddingResponse.ok) {
      const embeddingData = await embeddingResponse.json();
      const queryEmbedding = embeddingData.data[0].embedding;

      const { data: relevantKnowledge } = await supabaseClient.rpc('match_avatar_knowledge', {
        query_embedding: queryEmbedding,
        match_threshold: 0.5,
        match_count: 5,
        avatar_id_param: avatarId
      });

      const { data: customKnowledge } = await supabaseClient
        .from('mentor_knowledge_base')
        .select('title, content, content_type')
        .eq('mentor_id', avatar.mentor_id)
        .eq('is_active', true)
        .limit(10);

      const ragContext = relevantKnowledge?.map((k: any) => k.content).join('\n\n') || '';
      const customContext = customKnowledge?.map((k: any) => `[${k.content_type.toUpperCase()}] ${k.title}:\n${k.content}`).join('\n\n') || '';
      context = [ragContext, customContext].filter(Boolean).join('\n\n---\n\n') || 'No specific knowledge found.';
    }

    // Get recent conversation history
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

Personality: ${avatar.personality_traits?.join(', ') || 'professional, helpful, knowledgeable'}
Expertise: ${avatar.expertise_areas?.join(', ') || mentor.expertise?.join(', ') || 'general mentorship'}
Bio: ${avatar.bio_summary || mentor.bio}

STRICT SCOPE RULES — YOU MUST FOLLOW THESE AT ALL TIMES:
- You ONLY answer questions directly related to: ${mentor.name}'s profile, expertise, services, courses, products, pricing, availability, and the knowledge base below.
- If a user asks about anything outside this scope (personal life advice, general world topics, coding help unrelated to mentor's expertise, news, jokes, creative writing, etc.), politely decline and redirect.
- Example refusal: "I can only help with questions about [mentor name]'s services and expertise. Would you like to know about my courses or book a session?"
- NEVER pretend to be a general-purpose AI assistant.
- NEVER answer questions about other mentors, competitors, or unrelated topics.
- NEVER provide medical, legal, or financial advice beyond what is in the knowledge base.

RESPONSE STYLE:
- Respond as if you ARE the mentor, using first person ("I", "my")
- Be concise and helpful (2-4 sentences unless more detail is needed)
- When relevant, mention courses, services, or products from the knowledge base
- If appropriate, suggest booking a session for personalized help

Knowledge base (use this to answer questions):
${context}`;

    // Call OpenAI with streaming
    const streamResponse = await fetch('https://api.openai.com/v1/chat/completions', {
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
        stream: true,
      }),
    });

    if (!streamResponse.ok) {
      const errText = await streamResponse.text();
      console.error('OpenAI stream error:', streamResponse.status, errText);
      return new Response(JSON.stringify({ error: 'AI service temporarily unavailable' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Stream the response back to client while collecting full text
    const encoder = new TextEncoder();
    let fullText = '';
    let totalTokens = 0;

    const readable = new ReadableStream({
      async start(controller) {
        // Send conversationId first so client knows which conversation to use
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ conversationId: convId, type: 'start' })}\n\n`));

        const reader = streamResponse.body!.getReader();
        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              const data = line.slice(6).trim();
              if (data === '[DONE]') continue;

              try {
                const parsed = JSON.parse(data);
                const delta = parsed.choices?.[0]?.delta?.content;
                if (delta) {
                  fullText += delta;
                  controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'delta', content: delta })}\n\n`));
                }
                if (parsed.usage) {
                  totalTokens = parsed.usage.total_tokens || 0;
                }
              } catch {
                // skip malformed chunks
              }
            }
          }
        } finally {
          reader.releaseLock();
        }

        // Save the complete assistant message to DB
        if (fullText) {
          await supabaseClient.from('avatar_messages').insert({
            conversation_id: convId,
            role: 'assistant',
            content: fullText,
            metadata: { tokens_used: totalTokens }
          });
        }

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'done', conversationId: convId })}\n\n`));
        controller.close();
      }
    });

    return new Response(readable, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Error in chat-with-avatar-stream:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
