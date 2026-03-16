import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import Stripe from "https://esm.sh/stripe@18.5.0";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";

type ProductRow = {
  id: string;
  mentor_id: string;
  price: number;
  title: string;
  mentor_profiles: { name?: string } | null;
};

type StripeAccountRow = {
  stripe_account_id: string;
  onboarding_completed: boolean;
  charges_enabled: boolean;
};

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[CREATE-PRODUCT-CHECKOUT] Starting checkout process");

    // Authenticate user from Authorization header (same pattern as create-booking)
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
      console.error("[CREATE-PRODUCT-CHECKOUT] Auth error:", authError);
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    console.log("[CREATE-PRODUCT-CHECKOUT] User authenticated:", user.id);

    // Use service role key for server-side operations
    const supabaseAdmin = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Parse request body
    let productId: string;
    try {
      const body = await req.json();
      productId = body?.productId;
    } catch {
      return new Response(
        JSON.stringify({ error: "Invalid request body" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 400 }
      );
    }
    if (!productId) {
      return new Response(
        JSON.stringify({ error: "Product ID is required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 400 }
      );
    }

    console.log("[CREATE-PRODUCT-CHECKOUT] Product ID:", productId);

    // Get origin for redirect URLs - prefer request origin, fallback to production URL
    const origin = req.headers.get("origin") || "https://gcreators.me";
    console.log("[CREATE-PRODUCT-CHECKOUT] Origin:", origin);

    // Fetch product details
    const { data: productData, error: productError } = await supabaseClient
      .from("mentor_products")
      .select(`
        *,
        mentor_profiles!inner(name)
      `)
      .eq("id", productId)
      .eq("is_active", true)
      .single();

    const product = productData as ProductRow | null;
    if (productError || !product) {
      console.error("[CREATE-PRODUCT-CHECKOUT] Product error:", productError);
      throw new Error("Product not found or not available");
    }

    console.log("[CREATE-PRODUCT-CHECKOUT] Product found:", product.title);

    // Check if user already purchased this product (prevent duplicates) - use admin to bypass RLS
    const { data: existingPurchase } = await supabaseAdmin
      .from("product_purchases")
      .select("id, status")
      .eq("product_id", productId)
      .eq("buyer_id", user.id)
      .eq("status", "completed")
      .maybeSingle();

    if (existingPurchase) {
      console.log("[CREATE-PRODUCT-CHECKOUT] User already purchased this product");
      return new Response(
        JSON.stringify({ error: "You have already purchased this product. Check your dashboard to download it." }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 409 }
      );
    }

    // Initialize Stripe
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeKey) {
      throw new Error("Stripe key not configured");
    }

    const stripe = new Stripe(stripeKey);

    // Check if Stripe customer exists
    const customers = await stripe.customers.list({
      email: user.email,
      limit: 1,
    });

    let customerId: string | undefined;
    if (customers.data.length > 0) {
      customerId = (customers.data[0] as { id: string }).id;
      console.log("[CREATE-PRODUCT-CHECKOUT] Existing Stripe customer:", customerId);
    }

    // Get mentor's Stripe Connect account (if exists)
    const { data: stripeAccountData } = await supabaseAdmin
      .from("stripe_accounts")
      .select("stripe_account_id, onboarding_completed, charges_enabled")
      .eq("mentor_id", product.mentor_id)
      .maybeSingle();
    const stripeAccount = stripeAccountData as StripeAccountRow | null;

    // Calculate platform fee (15%)
    const platformFeePercent = Number(Deno.env.get("STRIPE_PLATFORM_FEE") || "0.15");
    const platformFee = Math.round(Number(product.price) * platformFeePercent * 100); // in cents

    const mentorName = product.mentor_profiles?.name ?? "Mentor";
    const rawPrice = product.price;
    const priceNum = typeof rawPrice === "number" ? rawPrice : parseFloat(String(rawPrice ?? ""));
    const unitAmount = Math.round(priceNum * 100);
    if (!Number.isFinite(priceNum) || priceNum < 0) {
      console.error("[CREATE-PRODUCT-CHECKOUT] Invalid price value:", rawPrice, typeof rawPrice);
      throw new Error("Invalid product price");
    }
    if (unitAmount < 50) {
      throw new Error("Product price must be at least $0.50 for payment processing");
    }

    // Session configuration
    const sessionConfig: Record<string, unknown> = {
      customer: customerId ?? undefined,
      customer_email: customerId ? undefined : (user.email ?? undefined),
      line_items: [
        {
          price_data: {
            currency: "usd",
            product_data: {
              name: product.title,
              description: `Digital product by ${mentorName}`,
            },
            unit_amount: unitAmount,
          },
          quantity: 1,
        },
      ],
      mode: "payment",
      success_url: `${origin}/learner/purchase-success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/learner/booking-cancel`,
      metadata: {
        product_id: productId,
        buyer_id: user.id,
        mentor_id: product.mentor_id,
      },
    };

    // If mentor has Stripe Connect account set up, use it for direct transfer
    if (stripeAccount?.onboarding_completed && stripeAccount?.charges_enabled && stripeAccount?.stripe_account_id) {
      console.log("[CREATE-PRODUCT-CHECKOUT] Using Stripe Connect for direct transfer");
      sessionConfig.payment_intent_data = {
        application_fee_amount: platformFee,
        transfer_data: {
          destination: stripeAccount.stripe_account_id,
        },
        metadata: {
          product_id: productId,
          buyer_id: user.id,
          mentor_id: product.mentor_id,
        },
      };
    } else {
      console.log("[CREATE-PRODUCT-CHECKOUT] No Connect account, funds will stay in platform account");
      sessionConfig.payment_intent_data = {
        metadata: {
          product_id: productId,
          buyer_id: user.id,
          mentor_id: product.mentor_id,
        },
      };
    }

    // Create Stripe checkout session
    let session: { id: string; url: string | null };
    try {
      session = await stripe.checkout.sessions.create(sessionConfig as never);
    } catch (stripeError: unknown) {
      const msg = stripeError instanceof Error ? stripeError.message : String(stripeError);
      console.error("[CREATE-PRODUCT-CHECKOUT] Stripe error:", stripeError);
      return new Response(
        JSON.stringify({ error: "Payment setup failed", details: msg }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 502 }
      );
    }

    console.log("[CREATE-PRODUCT-CHECKOUT] Checkout session created:", session.id);

    // Create pending purchase record using admin client to bypass RLS
    const { error: purchaseError } = await supabaseAdmin
      .from("product_purchases")
      .insert({
        product_id: productId,
        buyer_id: user.id,
        buyer_email: user.email,
        amount: product.price,
        stripe_session_id: session.id,
        status: "pending",
      });

    if (purchaseError) {
      console.error("[CREATE-PRODUCT-CHECKOUT] Purchase record error:", purchaseError);
      // Don't fail the request - the purchase can still be verified via Stripe webhook
    } else {
      console.log("[CREATE-PRODUCT-CHECKOUT] Pending purchase record created");
    }

    return new Response(JSON.stringify({ url: session.url }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "An error occurred";
    const details = error instanceof Error ? String(error.stack) : String(error);
    console.error("[CREATE-PRODUCT-CHECKOUT] Error:", error);
    return new Response(
      JSON.stringify({ error: errorMessage, details }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});
