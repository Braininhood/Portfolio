import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
// @ts-ignore: npm specifier
import Stripe from "npm:stripe@^14.0.0";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";

// Stripe SDK types (esm.sh can expose instance only; use type import for event payloads)
type StripeCheckoutSession = { id: string; metadata?: Record<string, string>; payment_intent?: string };
type StripePaymentIntent = { id: string; metadata?: Record<string, string> };
type StripeCharge = { id: string; payment_intent?: string };
type StripeAccount = { id: string; details_submitted?: boolean; charges_enabled?: boolean; payouts_enabled?: boolean };

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") || "", {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
}) as unknown as {
  webhooks: { constructEventAsync: (body: string, sig: string, secret: string, tolerance?: number) => Promise<{ type: string; data: { object: unknown } }> };
};

serve(async (req) => {
  const signature = req.headers.get("Stripe-Signature");
  const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET");

  if (!signature || !webhookSecret) {
    console.error("[STRIPE-WEBHOOK] Missing signature or webhook secret");
    return new Response("Missing signature or webhook secret", { status: 400 });
  }

  try {
    const body = await req.text();
    const event = await stripe.webhooks.constructEventAsync(
      body,
      signature,
      webhookSecret,
      undefined
    );

    console.log(`[STRIPE-WEBHOOK] Received event: ${event.type}`);

    const supabaseAdmin = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as StripeCheckoutSession;
        console.log(`[STRIPE-WEBHOOK] Checkout session completed: ${session.id}`);

        const metadata = session.metadata;
        
        if (metadata?.booking_id) {
          // Handle consultation booking payment
          await handleBookingPayment(supabaseAdmin, session, metadata);
        } else if (metadata?.product_id) {
          // Handle digital product payment
          await handleProductPayment(supabaseAdmin, session, metadata);
        }
        break;
      }

      case "payment_intent.succeeded": {
        const paymentIntent = event.data.object as StripePaymentIntent;
        console.log(`[STRIPE-WEBHOOK] Payment succeeded: ${paymentIntent.id}`);
        break;
      }

      case "payment_intent.payment_failed": {
        const paymentIntent = event.data.object as StripePaymentIntent;
        console.log(`[STRIPE-WEBHOOK] Payment failed: ${paymentIntent.id}`);
        
        // Update booking or product purchase status to failed
        const metadata = paymentIntent.metadata;
        if (metadata?.booking_id) {
          await supabaseAdmin
            .from("bookings")
            .update({ status: "failed" })
            .eq("id", metadata.booking_id);
        }
        break;
      }

      case "charge.refunded": {
        const charge = event.data.object as StripeCharge;
        console.log(`[STRIPE-WEBHOOK] Charge refunded: ${charge.id}`);
        
        // Handle refunds
        const paymentIntentId = charge.payment_intent as string;
        if (paymentIntentId) {
          // Get booking details before updating
          const { data: booking } = await supabaseAdmin
            .from("bookings")
            .select("*")
            .eq("stripe_payment_intent_id", paymentIntentId)
            .single();

          // Update booking to refunded status
          await supabaseAdmin
            .from("bookings")
            .update({ status: "refunded" })
            .eq("stripe_payment_intent_id", paymentIntentId);

          // Delete calendar event if exists
          if (booking && booking.mentor_calendar_event_id) {
            try {
              const supabaseUrl = Deno.env.get("SUPABASE_URL");
              const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");
              
              await fetch(
                `${supabaseUrl}/functions/v1/update-calendar-event`,
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "apikey": supabaseAnonKey!,
                  },
                  body: JSON.stringify({
                    action: "delete",
                    bookingId: booking.id,
                    mentorId: booking.mentor_id,
                    eventId: booking.mentor_calendar_event_id,
                  }),
                }
              );
              console.log(`[STRIPE-WEBHOOK] Calendar event deleted for refunded booking: ${booking.id}`);
            } catch (calendarError) {
              console.error(`[STRIPE-WEBHOOK] Error deleting calendar event:`, calendarError);
            }
          }
        }
        break;
      }

      case "account.updated": {
        // Sync Connect account status to Supabase (subscribe to account.updated in Stripe Dashboard)
        const account = event.data.object as StripeAccount;
        console.log(`[STRIPE-WEBHOOK] Connect account updated: ${account.id}`);
        await syncConnectAccountToSupabase(supabaseAdmin, account);
        break;
      }

      default:
        console.log(`[STRIPE-WEBHOOK] Unhandled event type: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error) {
    console.error("[STRIPE-WEBHOOK] Error:", error);
    return new Response(
      JSON.stringify({ error: "Webhook handler failed" }),
      { headers: { "Content-Type": "application/json" }, status: 500 }
    );
  }
});

async function handleBookingPayment(
  supabaseAdmin: any,
  session: StripeCheckoutSession,
  metadata: Record<string, string>
) {
  const bookingId = metadata.booking_id;
  const paymentIntentId = session.payment_intent as string;

  console.log(`[STRIPE-WEBHOOK] Handling booking payment for: ${bookingId}`);

  // Update booking status to confirmed
  const { error: bookingError } = await supabaseAdmin
    .from("bookings")
    .update({
      status: "confirmed",
      stripe_payment_intent_id: paymentIntentId,
    })
    .eq("id", bookingId);

  if (bookingError) {
    console.error("[STRIPE-WEBHOOK] Error updating booking:", bookingError);
    throw bookingError;
  }

  // Get booking details for transaction record
  const { data: booking } = await supabaseAdmin
    .from("bookings")
    .select("*")
    .eq("id", bookingId)
    .single();

  if (booking) {
    // Calculate fees
    const grossAmount = Number(booking.price);
    const platformFeePercent = Number(Deno.env.get("STRIPE_PLATFORM_FEE") || "0.15");
    const platformFee = grossAmount * platformFeePercent;
    const stripeFee = (grossAmount * 0.029) + 0.30; // Stripe's standard fee
    const netAmount = grossAmount - platformFee - stripeFee;

    // Create transaction record
    await supabaseAdmin.from("transactions").insert({
      mentor_id: booking.mentor_id,
      user_id: booking.user_id,
      type: "booking",
      related_id: bookingId,
      gross_amount: grossAmount,
      platform_fee: platformFee,
      stripe_fee: stripeFee,
      net_amount: netAmount,
      currency: "usd",
      stripe_payment_intent_id: paymentIntentId,
      status: "completed",
    });

    console.log(`[STRIPE-WEBHOOK] Transaction record created for booking: ${bookingId}`);
    
    // Add event to Google Calendar if mentor has connected calendar
    try {
      const supabaseUrl = Deno.env.get("SUPABASE_URL");
      const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");
      
      const calendarResponse = await fetch(
        `${supabaseUrl}/functions/v1/add-calendar-event`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "apikey": supabaseAnonKey!,
          },
          body: JSON.stringify({
            mentorId: booking.mentor_id,
            learnerId: booking.user_id,
            bookingId: booking.id,
            title: `Session with ${booking.user_email?.split('@')[0] || 'Learner'}`,
            description: `Mentorship session booked through Brain Bulders`,
            startDate: booking.booking_date,
            startTime: booking.booking_time,
            duration: 60,
            timeZone: "UTC",
          }),
        }
      );
      
      if (calendarResponse.ok) {
        console.log(`[STRIPE-WEBHOOK] Calendar event added for booking: ${bookingId}`);
      } else {
        console.error(`[STRIPE-WEBHOOK] Failed to add calendar event:`, await calendarResponse.text());
      }
    } catch (calendarError) {
      console.error(`[STRIPE-WEBHOOK] Error adding calendar event:`, calendarError);
      // Don't fail the webhook if calendar event fails
    }
  }
}

async function handleProductPayment(
  supabaseAdmin: any,
  session: StripeCheckoutSession,
  metadata: Record<string, string>
) {
  const productId = metadata.product_id;
  const buyerId = metadata.buyer_id;
  const paymentIntentId = session.payment_intent as string;

  console.log(`[STRIPE-WEBHOOK] Handling product payment for: ${productId}`);

  // Update purchase status to completed
  const { error: purchaseError } = await supabaseAdmin
    .from("product_purchases")
    .update({
      status: "completed",
      stripe_payment_intent_id: paymentIntentId,
    })
    .eq("product_id", productId)
    .eq("buyer_id", buyerId)
    .eq("stripe_session_id", session.id);

  if (purchaseError) {
    console.error("[STRIPE-WEBHOOK] Error updating product purchase:", purchaseError);
    throw purchaseError;
  }

  // Update product sales count and earnings
  const { data: product } = await supabaseAdmin
    .from("mentor_products")
    .select("sales_count, total_earnings, price, mentor_id")
    .eq("id", productId)
    .single();

  if (product) {
    const newSalesCount = (product.sales_count || 0) + 1;
    const newTotalEarnings = Number(product.total_earnings || 0) + Number(product.price);

    await supabaseAdmin
      .from("mentor_products")
      .update({
        sales_count: newSalesCount,
        total_earnings: newTotalEarnings,
      })
      .eq("id", productId);

    // Calculate fees for transaction record
    const grossAmount = Number(product.price);
    const platformFeePercent = Number(Deno.env.get("STRIPE_PLATFORM_FEE") || "0.15");
    const platformFee = grossAmount * platformFeePercent;
    const stripeFee = (grossAmount * 0.029) + 0.30;
    const netAmount = grossAmount - platformFee - stripeFee;

    // Create transaction record
    await supabaseAdmin.from("transactions").insert({
      mentor_id: product.mentor_id,
      user_id: buyerId,
      type: "product_sale",
      related_id: productId,
      gross_amount: grossAmount,
      platform_fee: platformFee,
      stripe_fee: stripeFee,
      net_amount: netAmount,
      currency: "usd",
      stripe_payment_intent_id: paymentIntentId,
      status: "completed",
    });

    console.log(`[STRIPE-WEBHOOK] Product purchase completed: ${productId}`);
  }
}

async function syncConnectAccountToSupabase(
  supabaseAdmin: ReturnType<typeof createClient>,
  account: StripeAccount
) {
  const { data: row, error: findError } = await supabaseAdmin
    .from("stripe_accounts")
    .select("id, mentor_id")
    .eq("stripe_account_id", account.id)
    .maybeSingle();

  if (findError || !row) {
    console.log(`[STRIPE-WEBHOOK] No stripe_accounts row for Connect account ${account.id}, skipping sync`);
    return;
  }

  const { error: updateError } = await supabaseAdmin
    .from("stripe_accounts")
    .update({
      onboarding_completed: account.details_submitted ?? false,
      charges_enabled: account.charges_enabled ?? false,
      payouts_enabled: account.payouts_enabled ?? false,
      account_status: account.details_submitted ? "active" : "pending",
      updated_at: new Date().toISOString(),
    })
    .eq("mentor_id", row.mentor_id);

  if (updateError) {
    console.error("[STRIPE-WEBHOOK] Error syncing Connect account to Supabase:", updateError);
    throw updateError;
  }
  console.log(`[STRIPE-WEBHOOK] Synced Connect account ${account.id} to Supabase for mentor ${row.mentor_id}`);
}

