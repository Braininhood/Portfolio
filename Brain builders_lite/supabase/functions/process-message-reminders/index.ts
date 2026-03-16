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

    console.log('Processing message reminders...');

    // Get pending reminders that are due
    const { data: reminders, error: fetchError } = await supabase
      .from('message_reminders')
      .select(`
        *,
        messages (
          content,
          sender_name,
          conversation_id
        )
      `)
      .eq('status', 'pending')
      .lte('reminder_time', new Date().toISOString())
      .order('reminder_time', { ascending: true });

    if (fetchError) {
      console.error('Error fetching reminders:', fetchError);
      throw fetchError;
    }

    console.log(`Found ${reminders?.length || 0} reminders to process`);

    let processedCount = 0;
    let sentCount = 0;
    let failedCount = 0;

    for (const reminder of reminders || []) {
      try {
        processedCount++;
        
        // Send push notification to the user
        const { data: subscription } = await supabase
          .from('push_subscriptions')
          .select('subscription')
          .eq('user_id', reminder.user_id)
          .maybeSingle();

        if (subscription) {
          const messageContent = (reminder.messages as any)?.content || 'Message reminder';
          const senderName = (reminder.messages as any)?.sender_name || 'Someone';
          
          await supabase.functions.invoke('send-push-notification', {
            body: {
              subscription: subscription.subscription,
              title: `Reminder: Message from ${senderName}`,
              body: reminder.note || messageContent.substring(0, 100),
              data: {
                url: `/messages?conversation=${reminder.conversation_id}`,
                conversationId: reminder.conversation_id,
                messageId: reminder.message_id,
              },
            },
          });
        }

        // Update reminder status to sent
        const { error: updateError } = await supabase
          .from('message_reminders')
          .update({
            status: 'sent',
            sent_at: new Date().toISOString(),
          })
          .eq('id', reminder.id);

        if (updateError) {
          console.error(`Error updating reminder ${reminder.id}:`, updateError);
          failedCount++;
        } else {
          sentCount++;
          console.log(`Reminder ${reminder.id} sent successfully`);
        }
      } catch (error) {
        console.error(`Error processing reminder ${reminder.id}:`, error);
        failedCount++;
      }
    }

    console.log(`Processed ${processedCount} reminders: ${sentCount} sent, ${failedCount} failed`);

    return new Response(
      JSON.stringify({
        success: true,
        processed: processedCount,
        sent: sentCount,
        failed: failedCount,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Error in process-message-reminders function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
