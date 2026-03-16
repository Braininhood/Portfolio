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
    console.log("[CREATE-STRIPE-CONNECT] Starting Connect account creation");

    // Authenticate user (accept both header casings)
    const authHeader = req.headers.get("Authorization") ?? req.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    console.log(`[CREATE-STRIPE-CONNECT] User authenticated: ${user.id}`);

    // Get mentor profile
    const { data: mentorProfile, error: profileError } = await supabaseClient
      .from("mentor_profiles")
      .select("id, name")
      .eq("user_id", user.id)
      .single();

    if (profileError || !mentorProfile) {
      return new Response(
        JSON.stringify({ error: "Mentor profile not found" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 404 }
      );
    }

    console.log(`[CREATE-STRIPE-CONNECT] Mentor profile found: ${mentorProfile.id}`);

    // Check if Stripe account already exists
    const { data: existingAccount } = await supabaseClient
      .from("stripe_accounts")
      .select("*")
      .eq("mentor_id", mentorProfile.id)
      .maybeSingle();

    if (existingAccount) {
      console.log(`[CREATE-STRIPE-CONNECT] Account exists: ${existingAccount.stripe_account_id}`);
      return new Response(
        JSON.stringify({
          accountId: existingAccount.stripe_account_id,
          exists: true,
          onboardingCompleted: existingAccount.onboarding_completed,
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Country from request body (user choice) or env fallback
    let body: { country?: string } = {};
    try {
      body = (await req.json()) || {};
    } catch {
      // no body
    }
    const country =
      (body.country && /^[A-Z]{2}$/.test(body.country) ? body.country : null) ||
      Deno.env.get("STRIPE_CONNECT_COUNTRY") ||
      "GB";

    const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") || "", {
      apiVersion: "2023-10-16",
      httpClient: Stripe.createFetchHttpClient(),
    });

    // Create Stripe Connect account (metadata values must be strings)
    // Stripe shows country-specific payout fields (bank, tax, etc.) in onboarding
    const account = await stripe.accounts.create({
      type: "express",
      country,
      email: user.email ?? undefined,
      capabilities: {
        card_payments: { requested: true },
        transfers: { requested: true },
      },
      business_type: "individual",
      metadata: {
        mentor_id: mentorProfile.id,
        user_id: user.id,
        mentor_name: String(mentorProfile.name ?? ""),
      },
    });

    console.log(`[CREATE-STRIPE-CONNECT] Stripe account created: ${account.id}`);

    // Use service role to insert stripe account
    const supabaseAdmin = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Save to database
    const now = new Date().toISOString();
    const { error: insertError } = await supabaseAdmin
      .from("stripe_accounts")
      .insert({
        mentor_id: mentorProfile.id,
        stripe_account_id: account.id,
        account_status: "created",
        onboarding_completed: false,
        charges_enabled: false,
        payouts_enabled: false,
        updated_at: now,
      });

    if (insertError) {
      console.error("[CREATE-STRIPE-CONNECT] Database insert error:", insertError);
      return new Response(
        JSON.stringify({ error: "Failed to save account", details: insertError.message }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 502 }
      );
    }

    console.log("[CREATE-STRIPE-CONNECT] Account saved to database");

    return new Response(
      JSON.stringify({
        accountId: account.id,
        exists: false,
        onboardingCompleted: false,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error: any) {
    console.error("[CREATE-STRIPE-CONNECT] Error:", error);
    return new Response(
      JSON.stringify({ error: error.message || "Failed to create Connect account" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});
