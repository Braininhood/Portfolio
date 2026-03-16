// @ts-ignore - Deno imports work at runtime
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore - Deno imports work at runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const GOOGLE_CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
const GOOGLE_CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

async function refreshAccessToken(refreshToken: string): Promise<{ access_token: string; expires_in: number } | null> {
  try {
    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID!,
        client_secret: GOOGLE_CLIENT_SECRET!,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      }),
    });

    const data = await response.json();
    if (data.error) {
      console.error("Token refresh error:", data);
      return null;
    }
    return data;
  } catch (error) {
    console.error("Failed to refresh token:", error);
    return null;
  }
}

async function getCalendarEvents(accessToken: string, calendarId: string): Promise<any[]> {
  const now = new Date();
  const twoWeeksLater = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

  const params = new URLSearchParams({
    timeMin: now.toISOString(),
    timeMax: twoWeeksLater.toISOString(),
    singleEvents: "true",
    orderBy: "startTime",
  });

  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events?${params}`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    }
  );

  const data = await response.json();
  
  if (data.error) {
    throw new Error(data.error.message || "Failed to fetch calendar events");
  }

  return data.items || [];
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[SYNC] Request received");
    const { mentorId, action } = await req.json();
    console.log("[SYNC] MentorId:", mentorId, "Action:", action);

    if (!mentorId) {
      throw new Error("Mentor ID is required");
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Get calendar connection
    console.log("[SYNC] Fetching calendar connection...");
    const { data: connection, error: connError } = await supabase
      .from("mentor_calendar_connections")
      .select("*")
      .eq("mentor_id", mentorId)
      .single();

    if (connError || !connection) {
      console.log("[SYNC] No connection found:", connError);
      throw new Error("No calendar connection found");
    }

    console.log("[SYNC] Connection found, sync_enabled:", connection.sync_enabled);

    if (!connection.sync_enabled) {
      return new Response(
        JSON.stringify({ message: "Sync is disabled" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Check if token needs refresh
    let accessToken = connection.access_token;
    const tokenExpiry = new Date(connection.token_expires_at);
    
    if (tokenExpiry < new Date()) {
      console.log("[SYNC] Refreshing expired token...");
      const newTokens = await refreshAccessToken(connection.refresh_token);
      
      if (!newTokens) {
        throw new Error("Failed to refresh access token. Please reconnect your calendar.");
      }

      accessToken = newTokens.access_token;
      const newExpiry = new Date(Date.now() + newTokens.expires_in * 1000);

      await supabase
        .from("mentor_calendar_connections")
        .update({
          access_token: accessToken,
          token_expires_at: newExpiry.toISOString(),
        })
        .eq("mentor_id", mentorId);
    }

    // Fetch calendar events
    console.log("[SYNC] Fetching calendar events...");
    const calendarId = connection.calendar_id || "primary";
    const events = await getCalendarEvents(accessToken, calendarId);
    console.log("[SYNC] Found", events.length, "events");

    // Process events - find busy times
    const busySlots: { date: string; start_time: string; end_time: string }[] = [];
    
    for (const event of events) {
      // Skip all-day events
      if (!event.start?.dateTime || !event.end?.dateTime) continue;
      
      const start = new Date(event.start.dateTime);
      const end = new Date(event.end.dateTime);
      
      // Only consider events during business hours (8 AM - 8 PM)
      const startHour = start.getHours();
      const endHour = end.getHours();
      
      if (startHour >= 8 && endHour <= 20) {
        busySlots.push({
          date: start.toISOString().split("T")[0],
          start_time: start.toTimeString().slice(0, 8),
          end_time: end.toTimeString().slice(0, 8),
        });
      }
    }

    console.log("[SYNC] Found", busySlots.length, "busy slots");

    // Update last sync time
    await supabase
      .from("mentor_calendar_connections")
      .update({ last_synced_at: new Date().toISOString() })
      .eq("mentor_id", mentorId);

    console.log("[SYNC] Success!");
    // Note: In a full implementation, you would use these busy slots to:
    // 1. Mark specific time slots as unavailable in mentor_time_slots
    // 2. Or store them in a separate busy_times table
    // For now, we just return the sync info

    return new Response(
      JSON.stringify({ 
        success: true, 
        eventsImported: events.length,
        busySlotsFound: busySlots.length,
        message: `Found ${busySlots.length} busy time slots from ${events.length} calendar events`
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error: unknown) {
    console.error("[SYNC] Calendar sync error:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
