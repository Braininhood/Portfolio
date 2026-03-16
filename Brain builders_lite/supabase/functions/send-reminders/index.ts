import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[SEND-REMINDERS] Starting reminder check...");

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");

    const now = new Date();
    
    // Calculate time windows
    const in24Hours = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const in1Hour = new Date(now.getTime() + 60 * 60 * 1000);
    const in25Hours = new Date(now.getTime() + 25 * 60 * 60 * 1000);
    const in2Hours = new Date(now.getTime() + 2 * 60 * 60 * 1000);

    let reminders24h = 0;
    let reminders1h = 0;
    let autoCompleted = 0;

    // Find bookings for 24h reminders (between 24h and 25h from now)
    const { data: bookings24h, error: error24h } = await supabase
      .from("bookings")
      .select(`
        *,
        mentor_profiles!inner(full_name),
        profiles!bookings_user_id_fkey(full_name)
      `)
      .eq("status", "confirmed")
      .gte("booking_date", in24Hours.toISOString().split("T")[0])
      .lte("booking_date", in25Hours.toISOString().split("T")[0])
      .is("reminder_sent_24h", null);

    if (error24h) {
      console.error("[SEND-REMINDERS] Error fetching 24h bookings:", error24h);
    } else if (bookings24h && bookings24h.length > 0) {
      console.log(`[SEND-REMINDERS] Found ${bookings24h.length} bookings for 24h reminders`);

      for (const booking of bookings24h) {
        try {
          // Send email notification
          await fetch(`${supabaseUrl}/functions/v1/send-notification-email`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "apikey": supabaseAnonKey!,
            },
            body: JSON.stringify({
              emailType: "reminder_24h",
              bookingId: booking.id,
              recipientEmail: booking.user_email,
            }),
          });

          // Create in-app notification
          await fetch(`${supabaseUrl}/functions/v1/create-notification`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "apikey": supabaseAnonKey!,
            },
            body: JSON.stringify({
              userId: booking.user_id,
              type: "reminder_24h",
              title: "Session Tomorrow!",
              message: `Your session with ${booking.mentor_profiles?.full_name || "your mentor"} is tomorrow at ${booking.booking_time}`,
              relatedBookingId: booking.id,
              actionUrl: "/dashboard?tab=sessions",
            }),
          });

          // Mark reminder as sent
          await supabase
            .from("bookings")
            .update({ reminder_sent_24h: new Date().toISOString() })
            .eq("id", booking.id);

          reminders24h++;
          console.log(`[SEND-REMINDERS] Sent 24h reminder for booking ${booking.id}`);
        } catch (error) {
          console.error(`[SEND-REMINDERS] Error sending 24h reminder for ${booking.id}:`, error);
        }
      }
    }

    // Find bookings for 1h reminders (between 1h and 2h from now)
    const { data: bookings1h, error: error1h } = await supabase
      .from("bookings")
      .select(`
        *,
        mentor_profiles!inner(full_name),
        profiles!bookings_user_id_fkey(full_name)
      `)
      .eq("status", "confirmed")
      .gte("booking_date", in1Hour.toISOString().split("T")[0])
      .lte("booking_date", in2Hours.toISOString().split("T")[0])
      .is("reminder_sent_1h", null);

    if (error1h) {
      console.error("[SEND-REMINDERS] Error fetching 1h bookings:", error1h);
    } else if (bookings1h && bookings1h.length > 0) {
      console.log(`[SEND-REMINDERS] Found ${bookings1h.length} bookings for 1h reminders`);

      for (const booking of bookings1h) {
        try {
          // Send email notification
          await fetch(`${supabaseUrl}/functions/v1/send-notification-email`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "apikey": supabaseAnonKey!,
            },
            body: JSON.stringify({
              emailType: "reminder_1h",
              bookingId: booking.id,
              recipientEmail: booking.user_email,
            }),
          });

          // Create in-app notification
          await fetch(`${supabaseUrl}/functions/v1/create-notification`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "apikey": supabaseAnonKey!,
            },
            body: JSON.stringify({
              userId: booking.user_id,
              type: "reminder_1h",
              title: "Session Starting Soon!",
              message: `Your session with ${booking.mentor_profiles?.full_name || "your mentor"} starts in 1 hour at ${booking.booking_time}`,
              relatedBookingId: booking.id,
              actionUrl: "/dashboard?tab=sessions",
            }),
          });

          // Mark reminder as sent
          await supabase
            .from("bookings")
            .update({ reminder_sent_1h: new Date().toISOString() })
            .eq("id", booking.id);

          reminders1h++;
          console.log(`[SEND-REMINDERS] Sent 1h reminder for booking ${booking.id}`);
        } catch (error) {
          console.error(`[SEND-REMINDERS] Error sending 1h reminder for ${booking.id}:`, error);
        }
      }
    }

    // Auto-complete past sessions: mark confirmed bookings as completed when session time has passed
    const todayStr = now.toISOString().split("T")[0];
    const { data: pastBookings } = await supabase
      .from("bookings")
      .select("id, booking_date, booking_time")
      .eq("status", "confirmed")
      .lte("booking_date", todayStr);

    if (pastBookings && pastBookings.length > 0) {
      for (const b of pastBookings) {
        const [h = 0, m = 0] = (b.booking_time || "00:00").toString().split(":").map(Number);
        const sessionEnd = new Date(`${b.booking_date}T${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`);
        sessionEnd.setHours(sessionEnd.getHours() + 1); // 60 min session
        if (now > sessionEnd) {
          const { error: updErr } = await supabase
            .from("bookings")
            .update({ status: "completed" })
            .eq("id", b.id);
          if (!updErr) {
            autoCompleted++;
            console.log(`[SEND-REMINDERS] Auto-completed booking ${b.id}`);
          }
        }
      }
    }

    console.log(`[SEND-REMINDERS] Completed. Sent ${reminders24h} 24h, ${reminders1h} 1h reminders; auto-completed ${autoCompleted} past sessions`);

    return new Response(
      JSON.stringify({
        success: true,
        reminders24h,
        reminders1h,
        autoCompleted,
        message: `Sent ${reminders24h} 24h and ${reminders1h} 1h reminders; auto-completed ${autoCompleted} sessions`,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error) {
    console.error("[SEND-REMINDERS] Error:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "An error occurred" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});
