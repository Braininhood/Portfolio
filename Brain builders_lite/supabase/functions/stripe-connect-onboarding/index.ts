import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
// @ts-ignore: npm specifier
import Stripe from "npm:stripe@^14.0.0";
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
    const authHeader = req.headers.get("Authorization") ?? req.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    const anonClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: authHeader } } }
    );
    const { data: { user }, error: authError } = await anonClient.auth.getUser();
    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    // Service role for DB
    const db = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const { data: mentorProfile } = await db
      .from("mentor_profiles")
      .select("id")
      .eq("user_id", user.id)
      .single();

    if (!mentorProfile) {
      return new Response(
        JSON.stringify({ error: "Mentor profile not found" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 404 }
      );
    }

    const { data: stripeAccount } = await db
      .from("stripe_accounts")
      .select("stripe_account_id")
      .eq("mentor_id", mentorProfile.id)
      .maybeSingle();

    if (!stripeAccount) {
      return new Response(
        JSON.stringify({ error: "Stripe Connect account not found. Please create one first." }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 404 }
      );
    }

    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
    if (!stripeKey) {
      return new Response(
        JSON.stringify({ error: "Stripe is not configured" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 503 }
      );
    }

    // Build redirect base — allow HTTP in test mode for local dev
    const isTestMode = stripeKey.startsWith("sk_test_");
    const origin = req.headers.get("origin") ?? "";
    const redirectBaseEnv = Deno.env.get("STRIPE_CONNECT_REDIRECT_BASE_URL") ?? "";
    const appUrl = Deno.env.get("NEXT_PUBLIC_APP_URL") ?? "";

    const candidates = [redirectBaseEnv, appUrl, origin].filter(Boolean);
    const redirectBase =
      candidates.find((u) => u.startsWith("https://")) ??
      (isTestMode ? candidates.find((u) => u.startsWith("http://")) : null) ??
      (isTestMode ? "http://localhost:8080" : null);

    if (!redirectBase) {
      return new Response(
        JSON.stringify({
          error: "Stripe Connect requires HTTPS redirect URLs in live mode",
          details: "Set STRIPE_CONNECT_REDIRECT_BASE_URL to your app's HTTPS URL in Supabase secrets.",
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 400 }
      );
    }

    const stripe = new Stripe(stripeKey, {
      apiVersion: "2023-10-16",
      httpClient: Stripe.createFetchHttpClient(),
    });

    const base = redirectBase.replace(/\/$/, "");
    const refreshUrl = `${base}/mentor/dashboard?tab=payouts&refresh=true`;
    const returnUrl = `${base}/mentor/dashboard?tab=payouts&setup=complete`;

    let accountLink;
    try {
      accountLink = await stripe.accountLinks.create({
        account: stripeAccount.stripe_account_id,
        refresh_url: refreshUrl,
        return_url: returnUrl,
        type: "account_onboarding",
      });
    } catch (stripeErr: any) {
      console.error("[STRIPE-CONNECT-ONBOARDING] Stripe error:", stripeErr?.message);

      // Stale account — clear it so mentor can create a fresh one
      if (stripeErr?.message?.includes("not connected") || stripeErr?.message?.includes("No such account") || stripeErr?.statusCode === 404) {
        await db.from("stripe_accounts").delete().eq("mentor_id", mentorProfile.id);
        return new Response(
          JSON.stringify({
            error: "Your Stripe account is no longer valid. Please set up a new one.",
            _cleared: true,
          }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 410 }
        );
      }

      return new Response(
        JSON.stringify({ error: `Stripe onboarding link failed: ${stripeErr?.message}` }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 502 }
      );
    }

    return new Response(
      JSON.stringify({ url: accountLink.url, accountId: stripeAccount.stripe_account_id }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    console.error("[STRIPE-CONNECT-ONBOARDING] Unhandled error:", error);
    return new Response(
      JSON.stringify({ error: error.message ?? "Internal error" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});
