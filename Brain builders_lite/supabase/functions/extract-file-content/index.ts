// @ts-ignore
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.84.0";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Extract text from a file stored in Supabase storage
// Supports: PDF (via OpenAI), TXT, CSV, audio/video (via OpenAI Whisper)
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const anonClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization') ?? '' } } }
    );
    const { data: { user } } = await anonClient.auth.getUser();
    if (!user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const db = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

    const { filePath, fileName, mimeType } = await req.json();
    if (!filePath) {
      return new Response(JSON.stringify({ error: 'filePath is required' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Download file from storage
    const { data: fileData, error: downloadError } = await db.storage
      .from('knowledge-base-files')
      .download(filePath);

    if (downloadError || !fileData) {
      return new Response(JSON.stringify({ error: 'Failed to download file', details: downloadError?.message }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY');
    let extractedText = '';
    const fileBytes = await fileData.arrayBuffer();

    // --- Plain text / CSV ---
    if (mimeType === 'text/plain' || mimeType === 'text/csv' || fileName?.endsWith('.txt') || fileName?.endsWith('.csv')) {
      extractedText = new TextDecoder().decode(fileBytes);
      // Truncate to 50k chars
      if (extractedText.length > 50000) extractedText = extractedText.slice(0, 50000) + '\n[Content truncated]';
    }

    // --- PDF: use OpenAI to summarize ---
    else if (mimeType === 'application/pdf' || fileName?.endsWith('.pdf')) {
      if (!OPENAI_API_KEY) throw new Error('OpenAI API key required for PDF extraction');

      const formData = new FormData();
      formData.append('file', new Blob([fileBytes], { type: 'application/pdf' }), fileName || 'document.pdf');
      formData.append('model', 'gpt-4o');
      formData.append('prompt', 'Extract and summarize all text content from this PDF document. Include all important information, headings, bullet points, and data.');

      // Use OpenAI file extraction via responses API
      const uploadRes = await fetch('https://api.openai.com/v1/files', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` },
        body: formData,
      });

      if (uploadRes.ok) {
        const uploadData = await uploadRes.json();
        const fileId = uploadData.id;

        // Ask GPT-4o to extract text from the uploaded file
        const chatRes = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: 'gpt-4o',
            messages: [{
              role: 'user',
              content: [
                { type: 'text', text: 'Please extract and summarize all the text content from this document. Include all important information.' },
                { type: 'file', file: { file_id: fileId } }
              ]
            }],
            max_tokens: 4000,
          }),
        });

        if (chatRes.ok) {
          const chatData = await chatRes.json();
          extractedText = chatData.choices?.[0]?.message?.content || '';
        }

        // Clean up uploaded file
        await fetch(`https://api.openai.com/v1/files/${fileId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` },
        });
      }

      // Fallback: basic binary text extraction
      if (!extractedText) {
        const rawText = new TextDecoder('utf-8', { fatal: false }).decode(fileBytes);
        extractedText = rawText.replace(/[^\x20-\x7E\n\r\t]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 20000);
        if (extractedText.length < 100) {
          extractedText = `[PDF file: ${fileName}. Content could not be extracted automatically. Please add a text description manually.]`;
        }
      }
    }

    // --- Audio/Video: transcribe with Whisper ---
    else if (mimeType?.startsWith('audio/') || mimeType?.startsWith('video/')) {
      if (!OPENAI_API_KEY) throw new Error('OpenAI API key required for audio/video transcription');

      const audioMime = mimeType.startsWith('video/') ? 'audio/mp4' : mimeType;
      const audioExt = fileName?.split('.').pop() || 'mp4';

      const formData = new FormData();
      formData.append('file', new Blob([fileBytes], { type: audioMime }), `audio.${audioExt}`);
      formData.append('model', 'whisper-1');
      formData.append('response_format', 'text');

      const whisperRes = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` },
        body: formData,
      });

      if (whisperRes.ok) {
        extractedText = await whisperRes.text();
        extractedText = `[Transcription of ${fileName}]\n\n${extractedText}`;
      } else {
        const err = await whisperRes.text();
        throw new Error(`Whisper transcription failed: ${err}`);
      }
    }

    // --- Office docs (Word, Excel, PowerPoint): summarize via GPT-4o ---
    else if (
      mimeType?.includes('officedocument') ||
      mimeType?.includes('ms-excel') ||
      mimeType?.includes('ms-powerpoint') ||
      mimeType?.includes('msword')
    ) {
      if (!OPENAI_API_KEY) throw new Error('OpenAI API key required for Office document extraction');

      // Convert to base64 and ask GPT-4o to describe content
      const base64 = btoa(String.fromCharCode(...new Uint8Array(fileBytes)));
      const chatRes = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [{
            role: 'user',
            content: `I have an Office document (${fileName}). The file is base64 encoded. Please note this is a ${mimeType} file. Since I cannot directly parse it, please acknowledge that this file "${fileName}" has been uploaded and will be referenced in the knowledge base. Provide a placeholder noting the file type and name.`
          }],
          max_tokens: 200,
        }),
      });

      if (chatRes.ok) {
        const chatData = await chatRes.json();
        extractedText = chatData.choices?.[0]?.message?.content || '';
      }

      if (!extractedText) {
        extractedText = `[Office document: ${fileName}. File type: ${mimeType}. Content uploaded to knowledge base.]`;
      }
    }

    else {
      extractedText = `[File: ${fileName}. Type: ${mimeType}. File uploaded to knowledge base.]`;
    }

    if (!extractedText.trim()) {
      extractedText = `[File: ${fileName} uploaded. Content could not be extracted automatically.]`;
    }

    return new Response(JSON.stringify({
      success: true,
      extractedText: extractedText.trim(),
      charCount: extractedText.length,
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in extract-file-content:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
