// @ts-ignore - Deno imports work at runtime
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore - Deno imports work at runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GOOGLE_CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
const GOOGLE_CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

serve(async (req) => {
  console.log("[CALLBACK] Request received");
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");

  console.log("[CALLBACK] Params:", { hasCode: !!code, hasState: !!state, error });

  let redirectUrl = "/mentor-cabinet";
  let mentorId = "";

  try {
    if (state) {
      const decoded = JSON.parse(atob(state));
      redirectUrl = decoded.redirectUrl || "/mentor-cabinet";
      mentorId = decoded.mentorId;
      console.log("[CALLBACK] Decoded state:", { redirectUrl, mentorId });
    }
  } catch (e) {
    console.error("[CALLBACK] Failed to decode state:", e);
  }

  if (error) {
    console.log("[CALLBACK] OAuth error from Google:", error);
    const redirectWithError = new URL(redirectUrl);
    redirectWithError.searchParams.set("calendar_connected", "false");
    redirectWithError.searchParams.set("error", error);
    
    return new Response(null, {
      status: 302,
      headers: { Location: redirectWithError.toString() }
    });
  }

  if (!code || !mentorId) {
    console.log("[CALLBACK] Missing required params - code:", !!code, "mentorId:", mentorId);
    const redirectWithError = new URL(redirectUrl);
    redirectWithError.searchParams.set("calendar_connected", "false");
    redirectWithError.searchParams.set("error", "Missing authorization code");
    
    return new Response(null, {
      status: 302,
      headers: { Location: redirectWithError.toString() }
    });
  }

  try {
    console.log("[CALLBACK] Exchanging code for tokens...");
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const callbackUrl = `${SUPABASE_URL}/functions/v1/google-calendar-callback`;

    // Exchange code for tokens
    const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID!,
        client_secret: GOOGLE_CLIENT_SECRET!,
        code,
        grant_type: "authorization_code",
        redirect_uri: callbackUrl,
      }),
    });

    const tokens = await tokenResponse.json();
    console.log("[CALLBACK] Token response:", { 
      hasAccessToken: !!tokens.access_token,
      hasRefreshToken: !!tokens.refresh_token,
      error: tokens.error 
    });

    if (tokens.error) {
      throw new Error(tokens.error_description || tokens.error);
    }

    // Get primary calendar ID
    console.log("[CALLBACK] Fetching calendar info...");
    const calendarResponse = await fetch(
      "https://www.googleapis.com/calendar/v3/calendars/primary",
      {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      }
    );
    
    const calendar = await calendarResponse.json();
    console.log("[CALLBACK] Calendar ID:", calendar.id);

    // Store tokens in database
    const expiresAt = new Date(Date.now() + tokens.expires_in * 1000);

    console.log("[CALLBACK] Storing tokens in database...");
    const { error: upsertError } = await supabase
      .from("mentor_calendar_connections")
      .upsert({
        mentor_id: mentorId,
        provider: "google",
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_expires_at: expiresAt.toISOString(),
        calendar_id: calendar.id || "primary",
        sync_enabled: true,
        last_synced_at: new Date().toISOString(),
      }, {
        onConflict: "mentor_id,provider"
      });

    if (upsertError) {
      console.error("[CALLBACK] Database error:", upsertError);
      throw upsertError;
    }

    console.log("[CALLBACK] Success! Redirecting...");
    // Redirect back with success
    const redirectWithSuccess = new URL(redirectUrl);
    redirectWithSuccess.searchParams.set("calendar_connected", "true");
    
    return new Response(null, {
      status: 302,
      headers: { Location: redirectWithSuccess.toString() }
    });

  } catch (err: unknown) {
    console.error("[CALLBACK] OAuth callback error:", err);
    
    const redirectWithError = new URL(redirectUrl);
    redirectWithError.searchParams.set("calendar_connected", "false");
    const errorMessage = err instanceof Error ? err.message : "Failed to connect calendar";
    redirectWithError.searchParams.set("error", errorMessage);
    
    return new Response(null, {
      status: 302,
      headers: { Location: redirectWithError.toString() }
    });
  }
});
