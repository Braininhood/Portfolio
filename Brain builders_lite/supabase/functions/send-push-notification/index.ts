import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.3";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

const handler = async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Authentication check - require valid JWT
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      console.error("Missing or invalid authorization header");
      return new Response(
        JSON.stringify({ error: "Unauthorized" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Verify the JWT token using anon key client
    const supabaseAuth = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: userError } = await supabaseAuth.auth.getUser();
    
    if (userError || !user) {
      console.error("Invalid token:", userError?.message);
      return new Response(
        JSON.stringify({ error: "Unauthorized" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const callerId = user.id;
    console.log("Authenticated caller:", callerId);

    // Use service role client for database operations
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const { recipientId, title, body, conversationId } = await req.json();

    // Validate required fields
    if (!recipientId || !title || !body) {
      return new Response(
        JSON.stringify({ error: "Missing required fields: recipientId, title, body" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    console.log("Sending push notification to user:", recipientId);

    // Authorization check: Verify caller has permission to notify the recipient
    // They must share a conversation (either as student or mentor)
    if (conversationId) {
      // Check if the conversation exists and involves both caller and recipient
      const { data: conversation, error: convError } = await supabaseClient
        .from("conversations")
        .select("id, user_id, mentor_id")
        .eq("id", conversationId)
        .single();

      if (convError || !conversation) {
        console.error("Conversation not found:", convError?.message);
        return new Response(
          JSON.stringify({ error: "Forbidden - Invalid conversation" }),
          { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      // Check if the caller is a mentor for this conversation
      const { data: callerMentorProfile } = await supabaseClient
        .from("mentor_profiles")
        .select("id")
        .eq("user_id", callerId)
        .maybeSingle();

      const callerMentorId = callerMentorProfile?.id;
      
      // Verify caller is part of this conversation
      const callerIsStudent = conversation.user_id === callerId;
      const callerIsMentor = callerMentorId && conversation.mentor_id === callerMentorId;
      
      if (!callerIsStudent && !callerIsMentor) {
        console.error("Caller is not part of this conversation");
        return new Response(
          JSON.stringify({ error: "Forbidden - Not authorized for this conversation" }),
          { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      // Verify recipient is the other party in the conversation
      // Get the recipient's mentor profile if they are a mentor
      const { data: recipientMentorProfile } = await supabaseClient
        .from("mentor_profiles")
        .select("id")
        .eq("user_id", recipientId)
        .maybeSingle();

      const recipientMentorId = recipientMentorProfile?.id;
      
      const recipientIsStudent = conversation.user_id === recipientId;
      const recipientIsMentor = recipientMentorId && conversation.mentor_id === recipientMentorId;

      if (!recipientIsStudent && !recipientIsMentor) {
        console.error("Recipient is not part of this conversation");
        return new Response(
          JSON.stringify({ error: "Forbidden - Recipient not in conversation" }),
          { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
    } else {
      // Without a conversationId, verify they share at least one conversation or booking
      // Check if they share any conversation
      const { data: callerMentorProfile } = await supabaseClient
        .from("mentor_profiles")
        .select("id")
        .eq("user_id", callerId)
        .maybeSingle();

      const { data: recipientMentorProfile } = await supabaseClient
        .from("mentor_profiles")
        .select("id")
        .eq("user_id", recipientId)
        .maybeSingle();

      // Build query to find shared conversations
      let hasSharedConversation = false;

      // Case 1: Caller is student, recipient might be mentor
      if (!callerMentorProfile && recipientMentorProfile) {
        const { data: sharedConv } = await supabaseClient
          .from("conversations")
          .select("id")
          .eq("user_id", callerId)
          .eq("mentor_id", recipientMentorProfile.id)
          .limit(1);
        hasSharedConversation = (sharedConv?.length ?? 0) > 0;
      }
      
      // Case 2: Caller is mentor, recipient is student
      if (callerMentorProfile && !recipientMentorProfile) {
        const { data: sharedConv } = await supabaseClient
          .from("conversations")
          .select("id")
          .eq("user_id", recipientId)
          .eq("mentor_id", callerMentorProfile.id)
          .limit(1);
        hasSharedConversation = (sharedConv?.length ?? 0) > 0;
      }

      // Case 3: Both are students - check bookings or other relationships
      // For now, require a conversation relationship

      if (!hasSharedConversation) {
        console.error("Caller and recipient do not share a conversation");
        return new Response(
          JSON.stringify({ error: "Forbidden - No relationship with recipient" }),
          { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
    }

    // Get user's push subscriptions
    const { data: subscriptions, error } = await supabaseClient
      .from("push_subscriptions")
      .select("subscription")
      .eq("user_id", recipientId);

    if (error) {
      console.error("Error fetching subscriptions:", error);
      throw error;
    }

    if (!subscriptions || subscriptions.length === 0) {
      console.log("No push subscriptions found for user");
      return new Response(
        JSON.stringify({ message: "No subscriptions found" }),
        {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Send push notification to all user's devices
    const notifications = subscriptions.map(async (sub) => {
      const subscription = sub.subscription as unknown as PushSubscription;
      
      const payload = JSON.stringify({
        title,
        body,
        conversationId,
        url: `/messages/${conversationId}`,
      });

      try {
        // Use Web Push API to send notification
        // Note: In production, you'd use a proper web-push library
        const response = await fetch(subscription.endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "TTL": "86400",
          },
          body: payload,
        });

        if (!response.ok) {
          console.error("Failed to send push notification:", await response.text());
        }

        return response.ok;
      } catch (error) {
        console.error("Error sending push notification:", error);
        return false;
      }
    });

    await Promise.all(notifications);

    return new Response(
      JSON.stringify({ success: true, message: "Notifications sent" }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error: any) {
    console.error("Error in send-push-notification function:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
};

serve(handler);
