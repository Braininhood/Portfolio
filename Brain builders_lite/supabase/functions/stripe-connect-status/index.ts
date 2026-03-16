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
        JSON.stringify({ error: "Missing authorization header" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    // Auth check with anon client
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

    // Use service role for all DB operations (bypasses RLS reliably)
    const db = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Get mentor profile
    const { data: mentorProfile, error: profileError } = await db
      .from("mentor_profiles")
      .select("id")
      .eq("user_id", user.id)
      .single();

    if (profileError || !mentorProfile) {
      return new Response(
        JSON.stringify({ error: "Mentor profile not found" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 404 }
      );
    }

    // Get Stripe account record
    const { data: stripeAccount } = await db
      .from("stripe_accounts")
      .select("*")
      .eq("mentor_id", mentorProfile.id)
      .maybeSingle();

    if (!stripeAccount) {
      return new Response(
        JSON.stringify({ exists: false, onboardingCompleted: false, chargesEnabled: false, payoutsEnabled: false }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
    if (!stripeKey) {
      return new Response(
        JSON.stringify({ error: "Stripe not configured" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 503 }
      );
    }

    const stripe = new Stripe(stripeKey, {
      apiVersion: "2023-10-16",
      httpClient: Stripe.createFetchHttpClient(),
    });

    let account;
    try {
      account = await stripe.accounts.retrieve(stripeAccount.stripe_account_id);
    } catch (stripeErr: any) {
      console.error("[STRIPE-CONNECT-STATUS] Stripe retrieve error:", stripeErr?.message);

      // Account doesn't exist in this Stripe key — clear stale record so mentor can start fresh
      if (stripeErr?.code === "account_invalid" || stripeErr?.statusCode === 404 || stripeErr?.message?.includes("No such account")) {
        await db.from("stripe_accounts").delete().eq("mentor_id", mentorProfile.id);
        return new Response(
          JSON.stringify({
            exists: false,
            onboardingCompleted: false,
            chargesEnabled: false,
            payoutsEnabled: false,
            _cleared: true,
          }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      return new Response(
        JSON.stringify({ error: stripeErr?.message ?? "Failed to retrieve Stripe account" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 502 }
      );
    }

    // Update DB with latest status
    await db
      .from("stripe_accounts")
      .update({
        onboarding_completed: account.details_submitted,
        charges_enabled: account.charges_enabled,
        payouts_enabled: account.payouts_enabled,
        account_status: account.details_submitted ? "active" : "pending",
        updated_at: new Date().toISOString(),
      })
      .eq("mentor_id", mentorProfile.id);

    return new Response(
      JSON.stringify({
        exists: true,
        accountId: account.id,
        onboardingCompleted: account.details_submitted,
        chargesEnabled: account.charges_enabled,
        payoutsEnabled: account.payouts_enabled,
        requirements: account.requirements,
        payoutSchedule: account.settings?.payouts?.schedule,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    console.error("[STRIPE-CONNECT-STATUS] Unhandled error:", error);
    return new Response(
      JSON.stringify({ error: error.message ?? "Internal error" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});
