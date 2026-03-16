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
    // Authenticate user from Authorization header
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    // Create Supabase client with user's auth context
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: authHeader } } }
    );

    // Verify and get authenticated user
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
      console.error("[CREATE-BOOKING] Auth error:", authError);
      return new Response(
        JSON.stringify({ error: "Authentication required" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 401 }
      );
    }

    // Use verified user data instead of client-provided values
    const userEmail = user.email;
    const userId = user.id;

    if (!userEmail) {
      return new Response(
        JSON.stringify({ error: "User email not available" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 400 }
      );
    }

    // Only accept booking details from client (not userId/userEmail)
    const { mentorId, mentorName, bookingDate, bookingTime, price } = await req.json();

    console.log("[CREATE-BOOKING] Creating booking for user:", userId, { mentorName, bookingDate, bookingTime });

    if (!mentorId || !mentorName || !bookingDate || !bookingTime || !price) {
      throw new Error("Missing required booking information");
    }

    const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") || "", {
      apiVersion: "2023-10-16",
      httpClient: Stripe.createFetchHttpClient(),
    });

    // Use service role client for database operations
    const serviceClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Create a booking record with verified user data
    const { data: booking, error: bookingError } = await serviceClient
      .from("bookings")
      .insert({
        user_email: userEmail,
        user_id: userId,
        mentor_id: mentorId,
        mentor_name: mentorName,
        booking_date: bookingDate,
        booking_time: bookingTime,
        price: price,
        status: "pending",
      })
      .select()
      .single();

    if (bookingError) {
      console.error("[CREATE-BOOKING] Error creating booking:", bookingError);
      throw new Error("Failed to create booking");
    }

    console.log("[CREATE-BOOKING] Booking created:", booking.id);

    // Check if customer exists in Stripe
    const customers = await stripe.customers.list({ email: userEmail, limit: 1 });
    let customerId;
    if (customers.data.length > 0) {
      customerId = customers.data[0].id;
      console.log("[CREATE-BOOKING] Existing customer found:", customerId);
    } else {
      console.log("[CREATE-BOOKING] Creating new customer");
    }

    // Get mentor's Stripe Connect account (if exists)
    const { data: stripeAccount } = await serviceClient
      .from("stripe_accounts")
      .select("stripe_account_id, onboarding_completed, charges_enabled")
      .eq("mentor_id", mentorId)
      .maybeSingle();

    // Calculate platform fee (15%)
    const platformFeePercent = Number(Deno.env.get("STRIPE_PLATFORM_FEE") || "0.15");
    const platformFee = Math.round(price * platformFeePercent * 100); // in cents

    // Session configuration
    const sessionConfig: any = {
      customer: customerId,
      customer_email: customerId ? undefined : userEmail,
      line_items: [
        {
          price_data: {
            currency: "usd",
            product_data: {
              name: `Mentorship Session with ${mentorName}`,
              description: `${bookingDate} at ${bookingTime}`,
            },
            unit_amount: Math.round(price * 100), // Convert to cents
          },
          quantity: 1,
        },
      ],
      mode: "payment",
      success_url: `${req.headers.get("origin")}/learner/booking-success?session_id={CHECKOUT_SESSION_ID}&booking_id=${booking.id}`,
      cancel_url: `${req.headers.get("origin")}/learner/booking-cancel`,
      metadata: {
        booking_id: booking.id,
        mentor_id: mentorId,
        user_id: userId,
      },
    };

    // If mentor has Stripe Connect account set up, use it for direct transfer
    if (stripeAccount && stripeAccount.onboarding_completed && stripeAccount.charges_enabled) {
      console.log("[CREATE-BOOKING] Using Stripe Connect for direct transfer");
      sessionConfig.payment_intent_data = {
        application_fee_amount: platformFee,
        transfer_data: {
          destination: stripeAccount.stripe_account_id,
        },
        metadata: {
          booking_id: booking.id,
          mentor_id: mentorId,
          user_id: userId,
        },
      };
    } else {
      console.log("[CREATE-BOOKING] No Connect account, funds will stay in platform account");
      // Funds will stay in platform account, can be manually transferred later
      sessionConfig.payment_intent_data = {
        metadata: {
          booking_id: booking.id,
          mentor_id: mentorId,
          user_id: userId,
        },
      };
    }

    // Create Stripe checkout session for payment
    const session = await stripe.checkout.sessions.create(sessionConfig);

    console.log("[CREATE-BOOKING] Stripe session created:", session.id);

    // Update booking with Stripe session ID
    await serviceClient
      .from("bookings")
      .update({ stripe_session_id: session.id })
      .eq("id", booking.id);

    return new Response(
      JSON.stringify({
        sessionUrl: session.url,
        bookingId: booking.id,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("[CREATE-BOOKING] Error:", error);
    return new Response(
      JSON.stringify({
        error: "An error occurred while creating the booking",
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

