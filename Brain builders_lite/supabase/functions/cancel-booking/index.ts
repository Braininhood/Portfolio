import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 200, headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
    if (!supabaseUrl || !serviceRoleKey || !anonKey) {
      return new Response(
        JSON.stringify({ error: "Server misconfiguration" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const authClient = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: authHeader } },
    });
    const { data: { user: caller }, error: authError } = await authClient.auth.getUser();
    if (authError || !caller) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const adminClient = createClient(supabaseUrl, serviceRoleKey);
    const body = await req.json().catch(() => ({}));
    const bookingId = typeof body?.bookingId === "string" ? body.bookingId.trim() : null;
    if (!bookingId) {
      return new Response(
        JSON.stringify({ error: "Booking ID required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const { data: booking, error: bookingError } = await adminClient
      .from("bookings")
      .select("id, user_id, mentor_id, status, user_email, mentor_name")
      .eq("id", bookingId)
      .single();

    if (bookingError || !booking) {
      return new Response(
        JSON.stringify({ error: "Booking not found" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (!["pending", "confirmed"].includes(booking.status)) {
      return new Response(
        JSON.stringify({ error: "Only pending or confirmed bookings can be cancelled" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Check: learner (owns booking) or mentor (owns the mentor slot)
    const { data: mentorRow } = await adminClient
      .from("mentor_profiles")
      .select("user_id")
      .eq("id", booking.mentor_id)
      .single();

    const isLearner = booking.user_id && booking.user_id === caller.id;
    const isMentor = mentorRow?.user_id === caller.id;

    const { data: roles } = await adminClient
      .from("user_roles")
      .select("role")
      .eq("user_id", caller.id);
    const isAdmin = roles?.some((r) => r.role === "admin") ?? false;

    if (!isLearner && !isMentor && !isAdmin) {
      return new Response(
        JSON.stringify({ error: "You do not have permission to cancel this booking" }),
        { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const { error: updateError } = await adminClient
      .from("bookings")
      .update({ status: "cancelled" })
      .eq("id", bookingId);

    if (updateError) {
      console.error("[CANCEL-BOOKING] Update error:", updateError);
      return new Response(
        JSON.stringify({ error: "Failed to cancel booking" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Notify learner (in-app)
    if (booking.user_id) {
      await fetch(`${supabaseUrl}/functions/v1/create-notification`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "apikey": anonKey },
        body: JSON.stringify({
          userId: booking.user_id,
          type: "booking_cancelled",
          title: "Session Cancelled",
          message: `Your session with ${booking.mentor_name || "your mentor"} has been cancelled.`,
          relatedBookingId: bookingId,
          actionUrl: "/learner/dashboard?tab=sessions",
        }),
      });
    }

    // Notify mentor (in-app)
    if (mentorRow?.user_id) {
      await fetch(`${supabaseUrl}/functions/v1/create-notification`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "apikey": anonKey },
        body: JSON.stringify({
          userId: mentorRow.user_id,
          type: "booking_cancelled",
          title: "Session Cancelled",
          message: `A session with ${booking.user_email} has been cancelled.`,
          relatedBookingId: bookingId,
          actionUrl: "/mentor/dashboard?tab=sessions",
        }),
      });
    }

    // Email learner
    await fetch(`${supabaseUrl}/functions/v1/send-notification-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "apikey": anonKey },
      body: JSON.stringify({
        emailType: "booking_cancelled",
        bookingId,
        recipientEmail: booking.user_email,
      }),
    });

    return new Response(
      JSON.stringify({ success: true, message: "Booking cancelled" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (err) {
    console.error("[CANCEL-BOOKING] Error:", err);
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : "An error occurred" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
