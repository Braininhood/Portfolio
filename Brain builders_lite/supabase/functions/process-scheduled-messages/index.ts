import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    console.log('Processing scheduled messages...');

    // Get all pending scheduled messages that are due
    const { data: scheduledMessages, error: fetchError } = await supabase
      .from('scheduled_messages')
      .select('*')
      .eq('status', 'pending')
      .lte('scheduled_for', new Date().toISOString())
      .order('scheduled_for', { ascending: true })
      .limit(50); // Process up to 50 messages per run

    if (fetchError) {
      console.error('Error fetching scheduled messages:', fetchError);
      throw fetchError;
    }

    console.log(`Found ${scheduledMessages?.length || 0} scheduled messages to process`);

    if (!scheduledMessages || scheduledMessages.length === 0) {
      return new Response(
        JSON.stringify({ processed: 0, message: 'No scheduled messages to process' }),
        { headers: { 'Content-Type': 'application/json', ...corsHeaders } }
      );
    }

    let successCount = 0;
    let failCount = 0;

    // Process each scheduled message
    for (const scheduledMsg of scheduledMessages) {
      try {
        // Insert the message into the messages table
        const { data: newMessage, error: insertError } = await supabase
          .from('messages')
          .insert({
            conversation_id: scheduledMsg.conversation_id,
            sender_id: scheduledMsg.sender_id,
            sender_name: scheduledMsg.sender_name,
            content: scheduledMsg.content,
            file_url: scheduledMsg.file_url,
            file_name: scheduledMsg.file_name,
            file_type: scheduledMsg.file_type,
          })
          .select()
          .single();

        if (insertError) {
          console.error(`Error inserting message for schedule ${scheduledMsg.id}:`, insertError);
          
          // Mark as failed
          await supabase
            .from('scheduled_messages')
            .update({
              status: 'failed',
              error_message: insertError.message,
            })
            .eq('id', scheduledMsg.id);
          
          failCount++;
          continue;
        }

        // Mark scheduled message as sent
        await supabase
          .from('scheduled_messages')
          .update({
            status: 'sent',
            sent_at: new Date().toISOString(),
          })
          .eq('id', scheduledMsg.id);

        // Try to send notification (optional, don't fail if this errors)
        try {
          const { data: conversation } = await supabase
            .from('conversations')
            .select('user_id, mentor_id')
            .eq('id', scheduledMsg.conversation_id)
            .single();

          if (conversation) {
            const recipientId = conversation.user_id === scheduledMsg.sender_id 
              ? conversation.mentor_id 
              : conversation.user_id;

            await supabase.functions.invoke('send-message-notification', {
              body: {
                messageId: newMessage.id,
                recipientId,
                senderName: scheduledMsg.sender_name,
                messageContent: scheduledMsg.content,
              },
            });
          }
        } catch (notificationError) {
          console.error('Error sending notification:', notificationError);
          // Don't fail the whole operation if notification fails
        }

        successCount++;
        console.log(`Successfully sent scheduled message ${scheduledMsg.id}`);
      } catch (error: any) {
        console.error(`Error processing scheduled message ${scheduledMsg.id}:`, error);
        
        // Mark as failed
        await supabase
          .from('scheduled_messages')
          .update({
            status: 'failed',
            error_message: error?.message || 'Unknown error',
          })
          .eq('id', scheduledMsg.id);
        
        failCount++;
      }
    }

    console.log(`Processed ${successCount + failCount} messages: ${successCount} sent, ${failCount} failed`);

    return new Response(
      JSON.stringify({
        processed: successCount + failCount,
        sent: successCount,
        failed: failCount,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      }
    );
  } catch (error: any) {
    console.error('Error in process-scheduled-messages function:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      }
    );
  }
});
