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
    // Auth check
    const anonClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization') ?? '' } } }
    );
    const { data: { user } } = await anonClient.auth.getUser();
    if (!user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Service role for DB operations
    const db = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

    const { avatarId, mentorId, bioSummary, expertiseAreas, personalityTraits } = await req.json();

    if (!avatarId || !mentorId) {
      return new Response(JSON.stringify({ error: 'avatarId and mentorId are required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Verify mentor ownership
    const { data: mentorProfile, error: mentorError } = await db
      .from('mentor_profiles')
      .select('*')
      .eq('id', mentorId)
      .eq('user_id', user.id)
      .single();

    if (mentorError || !mentorProfile) {
      console.error('Mentor ownership check failed:', mentorError);
      return new Response(JSON.stringify({ error: 'Mentor profile not found or unauthorized' }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Mark as training
    await db.from('mentor_avatars').update({ status: 'training' }).eq('id', avatarId);

    const knowledgeEntries: { content: string; content_type: string; metadata: object }[] = [];

    // 1. Avatar bio + expertise (always present)
    knowledgeEntries.push({
      content: [
        `Bio: ${bioSummary || mentorProfile.bio}`,
        `Expertise: ${(expertiseAreas || []).join(', ')}`,
        `Personality: ${(personalityTraits || []).join(', ')}`,
      ].join('\n'),
      content_type: 'bio',
      metadata: { source: 'avatar_config' }
    });

    // 2. Full mentor profile
    knowledgeEntries.push({
      content: [
        `Name: ${mentorProfile.name}`,
        `Title: ${mentorProfile.title}`,
        `Category: ${mentorProfile.category}`,
        mentorProfile.full_bio ? `Full bio: ${mentorProfile.full_bio}` : '',
        mentorProfile.experience ? `Experience: ${mentorProfile.experience}` : '',
        mentorProfile.education ? `Education: ${mentorProfile.education}` : '',
        mentorProfile.availability ? `Availability: ${mentorProfile.availability}` : '',
        `Price per session: $${mentorProfile.price}`,
        mentorProfile.certifications?.length ? `Certifications: ${mentorProfile.certifications.join(', ')}` : '',
      ].filter(Boolean).join('\n'),
      content_type: 'profile',
      metadata: { source: 'mentor_profile' }
    });

    // 3. Courses (graceful — table may not have data)
    try {
      const { data: courses } = await db
        .from('mentor_courses')
        .select('title, description, level, duration, price')
        .eq('mentor_id', mentorId);
      (courses || []).forEach(course => {
        knowledgeEntries.push({
          content: [
            `Course: ${course.title}`,
            course.description ? `Description: ${course.description}` : '',
            course.level ? `Level: ${course.level}` : '',
            course.duration ? `Duration: ${course.duration}` : '',
            course.price != null ? `Price: $${course.price}` : '',
          ].filter(Boolean).join('\n'),
          content_type: 'course',
          metadata: { source: 'course' }
        });
      });
    } catch (e) { console.warn('Courses fetch skipped:', e); }

    // 4. Digital products
    try {
      const { data: products } = await db
        .from('mentor_products')
        .select('title, description, price, file_type')
        .eq('mentor_id', mentorId)
        .eq('is_active', true);
      (products || []).forEach(p => {
        knowledgeEntries.push({
          content: [
            `Digital Product: ${p.title}`,
            p.description ? `Description: ${p.description}` : '',
            p.file_type ? `Type: ${p.file_type}` : '',
            p.price != null ? `Price: $${p.price}` : '',
          ].filter(Boolean).join('\n'),
          content_type: 'product',
          metadata: { source: 'product' }
        });
      });
    } catch (e) { console.warn('Products fetch skipped:', e); }

    // 5. Reviews
    try {
      const { data: reviews } = await db
        .from('mentor_reviews')
        .select('rating, comment')
        .eq('mentor_id', mentorId)
        .limit(10);
      if (reviews && reviews.length > 0) {
        knowledgeEntries.push({
          content: `Student reviews:\n${reviews.map(r => `Rating: ${r.rating}/5 - ${r.comment}`).join('\n')}`,
          content_type: 'reviews',
          metadata: { source: 'reviews', count: reviews.length }
        });
      }
    } catch (e) { console.warn('Reviews fetch skipped:', e); }

    // 6. Q&A with video answers
    try {
      const { data: questions } = await db
        .from('mentor_questions')
        .select('question_text, mentor_video_answers(video_url)')
        .eq('mentor_id', mentorId);
      (questions || []).forEach((q: any) => {
        if (q.mentor_video_answers?.length > 0) {
          knowledgeEntries.push({
            content: `Q: ${q.question_text}\nVideo answer available: ${q.mentor_video_answers[0].video_url}`,
            content_type: 'video_answer',
            metadata: { source: 'video_answer' }
          });
        }
      });
    } catch (e) { console.warn('Questions fetch skipped:', e); }

    // 7. Custom knowledge base (text + extracted file content)
    try {
      const { data: kbEntries } = await db
        .from('mentor_knowledge_base')
        .select('title, content, content_type')
        .eq('mentor_id', mentorId)
        .eq('is_active', true);
      (kbEntries || []).forEach((entry: any) => {
        knowledgeEntries.push({
          content: `${entry.title}:\n${entry.content}`,
          content_type: entry.content_type,
          metadata: { source: 'knowledge_base' }
        });
      });
    } catch (e) { console.warn('Knowledge base fetch skipped:', e); }

    console.log(`Training avatar ${avatarId} with ${knowledgeEntries.length} knowledge entries`);

    // Generate embeddings
    const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY');
    if (!OPENAI_API_KEY) {
      await db.from('mentor_avatars').update({ status: 'error' }).eq('id', avatarId);
      return new Response(JSON.stringify({ error: 'OpenAI API key not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const entriesWithEmbeddings = await Promise.all(
      knowledgeEntries.map(async (entry) => {
        const response = await fetch('https://api.openai.com/v1/embeddings', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${OPENAI_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'text-embedding-3-small',
            input: entry.content.slice(0, 8000), // token limit safety
          }),
        });

        if (!response.ok) {
          const err = await response.text();
          throw new Error(`OpenAI embeddings failed: ${response.status} - ${err}`);
        }

        const data = await response.json();
        return {
          ...entry,
          embedding: JSON.stringify(data.data[0].embedding),
          avatar_id: avatarId
        };
      })
    );

    // Replace old knowledge
    await db.from('mentor_avatar_knowledge').delete().eq('avatar_id', avatarId);

    const { error: insertError } = await db
      .from('mentor_avatar_knowledge')
      .insert(entriesWithEmbeddings);

    if (insertError) {
      console.error('Insert error:', insertError);
      await db.from('mentor_avatars').update({ status: 'error' }).eq('id', avatarId);
      return new Response(JSON.stringify({ error: 'Failed to save knowledge base', details: insertError.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    await db.from('mentor_avatars').update({
      status: 'ready',
      training_completed_at: new Date().toISOString(),
      last_trained_at: new Date().toISOString()
    }).eq('id', avatarId);

    return new Response(JSON.stringify({
      success: true,
      message: 'Avatar trained successfully',
      knowledgeCount: entriesWithEmbeddings.length
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Unhandled error in train-avatar:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
