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

async function updateCalendarEvent(
  accessToken: string,
  calendarId: string,
  eventId: string,
  updates: {
    summary?: string;
    description?: string;
    start?: { dateTime: string; timeZone: string };
    end?: { dateTime: string; timeZone: string };
  }
) {
  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events/${eventId}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    }
  );

  const data = await response.json();
  
  if (data.error) {
    throw new Error(data.error.message || "Failed to update calendar event");
  }

  return data;
}

async function deleteCalendarEvent(
  accessToken: string,
  calendarId: string,
  eventId: string
) {
  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events/${eventId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok && response.status !== 204 && response.status !== 410) {
    const data = await response.json();
    throw new Error(data.error?.message || "Failed to delete calendar event");
  }

  return true;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[UPDATE-CALENDAR-EVENT] Request received");
    
    const {
      action, // 'update' or 'delete'
      bookingId,
      mentorId,
      eventId,
      // For updates only:
      title,
      description,
      startDate,
      startTime,
      duration,
      timeZone = "UTC",
    } = await req.json();

    console.log("[UPDATE-CALENDAR-EVENT] Action:", action, "BookingId:", bookingId, "EventId:", eventId);

    if (!action || !bookingId || !mentorId) {
      throw new Error("Missing required parameters");
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Get mentor's calendar connection
    const { data: connection } = await supabase
      .from("mentor_calendar_connections")
      .select("*")
      .eq("mentor_id", mentorId)
      .single();

    if (!connection || !connection.sync_enabled) {
      return new Response(
        JSON.stringify({ 
          success: false, 
          message: "Mentor does not have calendar connected" 
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Get or refresh access token
    let accessToken = connection.access_token;
    const tokenExpiry = new Date(connection.token_expires_at);
    
    if (tokenExpiry < new Date()) {
      console.log("[UPDATE-CALENDAR-EVENT] Refreshing expired token...");
      const newTokens = await refreshAccessToken(connection.refresh_token);
      if (newTokens) {
        accessToken = newTokens.access_token;
        await supabase
          .from("mentor_calendar_connections")
          .update({
            access_token: accessToken,
            token_expires_at: new Date(Date.now() + newTokens.expires_in * 1000).toISOString(),
          })
          .eq("mentor_id", mentorId);
      }
    }

    const calendarId = connection.calendar_id || "primary";

    if (action === "delete") {
      // Delete calendar event
      console.log("[UPDATE-CALENDAR-EVENT] Deleting event:", eventId);
      
      if (eventId) {
        try {
          await deleteCalendarEvent(accessToken, calendarId, eventId);
          console.log("[UPDATE-CALENDAR-EVENT] Event deleted successfully");
          
          // Clear event ID from booking
          await supabase
            .from("bookings")
            .update({ mentor_calendar_event_id: null })
            .eq("id", bookingId);
        } catch (error) {
          console.error("[UPDATE-CALENDAR-EVENT] Failed to delete event:", error);
          // Don't fail if event already deleted (410 Gone)
        }
      }

      return new Response(
        JSON.stringify({ 
          success: true, 
          action: "deleted" 
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "update") {
      // Update calendar event
      if (!eventId) {
        throw new Error("Event ID required for update");
      }

      console.log("[UPDATE-CALENDAR-EVENT] Updating event:", eventId);

      const [hours, minutes] = startTime.split(":");
      const start = new Date(`${startDate}T${hours}:${minutes}:00`);
      const end = new Date(start.getTime() + (duration || 60) * 60 * 1000);

      const updates = {
        summary: title,
        description: description || "",
        start: {
          dateTime: start.toISOString(),
          timeZone,
        },
        end: {
          dateTime: end.toISOString(),
          timeZone,
        },
      };

      try {
        const updatedEvent = await updateCalendarEvent(accessToken, calendarId, eventId, updates);
        console.log("[UPDATE-CALENDAR-EVENT] Event updated successfully");

        return new Response(
          JSON.stringify({ 
            success: true, 
            action: "updated",
            eventId: updatedEvent.id 
          }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      } catch (error) {
        console.error("[UPDATE-CALENDAR-EVENT] Failed to update event:", error);
        throw error;
      }
    }

    throw new Error("Invalid action. Must be 'update' or 'delete'");

  } catch (error: unknown) {
    console.error("[UPDATE-CALENDAR-EVENT] Error:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
