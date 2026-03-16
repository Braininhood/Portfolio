import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import Stripe from "https://esm.sh/stripe@18.5.0";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";
import { Resend } from "https://esm.sh/resend@4.0.0";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Signed URL expiration: 1 hour (3600 seconds)
const SIGNED_URL_EXPIRATION = 3600;

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[VERIFY-PRODUCT-PURCHASE] Starting verification");

    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";

    // Prefer service role for server-side writes (bypasses RLS). If not available, fall back to
    // an anon client that forwards the user's JWT (RLS enforced).
    const supabaseAdmin = serviceRoleKey
      ? createClient(supabaseUrl, serviceRoleKey)
      : null;

    const authHeader = req.headers.get("Authorization") ?? "";
    const supabaseUser = createClient(supabaseUrl, anonKey, {
      global: {
        headers: authHeader ? { Authorization: authHeader } : {},
      },
    });

    const db = supabaseAdmin ?? supabaseUser;

    console.log("[VERIFY-PRODUCT-PURCHASE] Admin key present:", Boolean(serviceRoleKey));

    // Initialize Resend for email notifications
    const resendKey = Deno.env.get("RESEND_API_KEY");
    const resend = resendKey ? new Resend(resendKey) : null;

    // Get auth user for re-download requests
    let authUserId: string | null = null;

    if (authHeader) {
      const { data: { user }, error: authError } = await supabaseUser.auth.getUser(
        authHeader.replace("Bearer ", "")
      );

      if (authError) {
        console.error("[VERIFY-PRODUCT-PURCHASE] Auth error:", authError);
      }

      authUserId = user?.id || null;
    }

    const { sessionId, productId: redownloadProductId, redownload } = await req.json();

    // Handle re-download request
    if (redownload && redownloadProductId && authUserId) {
      console.log("[VERIFY-PRODUCT-PURCHASE] Re-download request for product:", redownloadProductId);
      
      // Verify the user has purchased this product
      const { data: purchase, error: purchaseError } = await db
        .from("product_purchases")
        .select("*, mentor_products(*)")
        .eq("product_id", redownloadProductId)
        .eq("buyer_id", authUserId)
        .eq("status", "completed")
        .maybeSingle();

      if (purchaseError || !purchase) {
        throw new Error("Purchase not found or not completed");
      }

      const product = purchase.mentor_products;
      
      // Generate signed URL for download with 1 hour expiration
      const filePath = product.file_url.includes("/product-files/") 
        ? product.file_url.split("/product-files/")[1]
        : product.file_url;
        
      const { data: signedUrlData } = await db.storage
        .from("product-files")
        .createSignedUrl(filePath, SIGNED_URL_EXPIRATION);

      return new Response(
        JSON.stringify({
          success: true,
          productTitle: product.title,
          downloadUrl: signedUrlData?.signedUrl || product.file_url,
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 200,
        }
      );
    }

    // Original flow: verify new purchase via Stripe session
    if (!sessionId) {
      throw new Error("Session ID is required");
    }

    console.log("[VERIFY-PRODUCT-PURCHASE] Session ID:", sessionId);

    // Initialize Stripe
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeKey) {
      throw new Error("Stripe key not configured");
    }

    const stripe = new Stripe(stripeKey);

    // Verify Stripe session
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    console.log("[VERIFY-PRODUCT-PURCHASE] Session status:", session.payment_status);

    if (session.payment_status !== "paid") {
      throw new Error("Payment not completed");
    }

    const productId = session.metadata?.product_id;
    const buyerId = session.metadata?.buyer_id;

    if (!productId || !buyerId) {
      throw new Error("Invalid session metadata");
    }

    // Check if this purchase was already verified (idempotency)
    const { data: existingPurchase } = await db
      .from("product_purchases")
      .select("*")
      .eq("stripe_session_id", sessionId)
      .eq("status", "completed")
      .maybeSingle();

    if (existingPurchase) {
      console.log("[VERIFY-PRODUCT-PURCHASE] Purchase already verified, returning existing data");
      
      // Get product for download URL
      const { data: product } = await db
        .from("mentor_products")
        .select("*")
        .eq("id", productId)
        .single();

      if (product) {
        const filePath = product.file_url.includes("/product-files/") 
          ? product.file_url.split("/product-files/")[1]
          : product.file_url;
          
        const { data: signedUrlData } = await db.storage
          .from("product-files")
          .createSignedUrl(filePath, SIGNED_URL_EXPIRATION);

        return new Response(
          JSON.stringify({
            success: true,
            productTitle: product.title,
            downloadUrl: signedUrlData?.signedUrl || product.file_url,
          }),
          {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
            status: 200,
          }
        );
      }
    }

    // Get product details with mentor info
    const { data: product, error: productError } = await db
      .from("mentor_products")
      .select(`
        *,
        mentor_profiles!inner(name, user_id)
      `)
      .eq("id", productId)
      .single();

    if (productError || !product) {
      throw new Error("Product not found");
    }

    // Get buyer email from purchase record or session
    const { data: purchaseRecord } = await db
      .from("product_purchases")
      .select("id, buyer_email")
      .eq("stripe_session_id", sessionId)
      .maybeSingle();

    const buyerEmail = purchaseRecord?.buyer_email || session.customer_email;

    // Update or create purchase record
    if (purchaseRecord) {
      // Update existing record
      const { error: updateError } = await db
        .from("product_purchases")
        .update({
          status: "completed",
          stripe_payment_intent_id: session.payment_intent as string,
        })
        .eq("stripe_session_id", sessionId);

      if (updateError) {
        console.error("[VERIFY-PRODUCT-PURCHASE] Update error:", updateError);
      }
    } else {
      // Create the purchase record if it doesn't exist (fallback for edge cases)
      console.log("[VERIFY-PRODUCT-PURCHASE] No pending purchase found, creating record");
      const { error: insertError } = await db
        .from("product_purchases")
        .insert({
          product_id: productId,
          buyer_id: buyerId,
          buyer_email: session.customer_email || "",
          amount: product.price,
          stripe_session_id: sessionId,
          stripe_payment_intent_id: session.payment_intent as string,
          status: "completed",
        });

      if (insertError) {
        console.error("[VERIFY-PRODUCT-PURCHASE] Insert error:", insertError);
        throw new Error("Could not record the purchase. Please contact support.");
      }
    }

    // Update product sales count and earnings
    const { error: productUpdateError } = await db
      .from("mentor_products")
      .update({
        sales_count: product.sales_count + 1,
        total_earnings: Number(product.total_earnings) + Number(product.price),
      })
      .eq("id", productId);

    if (productUpdateError) {
      console.error("[VERIFY-PRODUCT-PURCHASE] Product update error:", productUpdateError);
    }

    console.log("[VERIFY-PRODUCT-PURCHASE] Purchase verified successfully");

    // Generate signed URL for download with 1 hour expiration
    const filePath = product.file_url.includes("/product-files/") 
      ? product.file_url.split("/product-files/")[1]
      : product.file_url;
      
    const { data: signedUrlData } = await db.storage
      .from("product-files")
      .createSignedUrl(filePath, SIGNED_URL_EXPIRATION);

    // Get origin for dashboard link
    const origin = req.headers.get("origin") || "https://gcreators.me";
    const downloadUrl = signedUrlData?.signedUrl || product.file_url;

    // Send notification emails
    if (resend && buyerEmail) {
      // Send buyer confirmation email with download link
      try {
        const buyerHtml = `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <title>Purchase Confirmation</title>
          </head>
          <body style="margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f6f9fc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
              <h1 style="color: #0A0A0A; font-size: 28px; text-align: center; margin: 0 0 24px;">
                Thank You for Your Purchase! 🎉
              </h1>
              
              <p style="color: #333; font-size: 16px; line-height: 24px;">
                Your digital product is now available for download.
              </p>

              <div style="background-color: #f0f9ff; border-radius: 8px; padding: 24px; margin: 24px 0;">
                <h2 style="color: #0A0A0A; font-size: 20px; margin: 0 0 16px;">Order Details</h2>
                
                <p style="color: #333; font-size: 16px; margin: 8px 0;">
                  <strong>Product:</strong> ${product.title}
                </p>
                
                <p style="color: #333; font-size: 16px; margin: 8px 0;">
                  <strong>Seller:</strong> ${product.mentor_profiles.name}
                </p>
                
                <p style="color: #333; font-size: 16px; margin: 8px 0;">
                  <strong>Amount:</strong> $${Number(product.price).toFixed(2)}
                </p>
              </div>

              <div style="text-align: center; margin: 32px 0;">
                <a href="${downloadUrl}" 
                   style="display: inline-block; background-color: #0A0A0A; color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600;">
                  📥 Download Your Product
                </a>
              </div>

              <p style="color: #666; font-size: 14px; line-height: 22px; text-align: center;">
                This download link expires in 1 hour. You can always download again from your 
                <a href="${origin}/dashboard" style="color: #0066cc;">dashboard</a>.
              </p>

              <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
                Brain Bulders - Empowering personal and professional growth
              </p>
            </div>
          </body>
          </html>
        `;

        await resend.emails.send({
          from: 'Brain Bulders <onboarding@resend.dev>',
          to: [buyerEmail],
          subject: `Purchase Confirmed: ${product.title} - Download Inside`,
          html: buyerHtml,
        });
        console.log("[VERIFY-PRODUCT-PURCHASE] Buyer confirmation email sent with download link");
      } catch (emailError) {
        console.error("[VERIFY-PRODUCT-PURCHASE] Buyer email error:", emailError);
      }

      // Send mentor notification email
      try {
        // Get mentor's email from auth.users via their user_id
         const { data: mentorAuth } = supabaseAdmin
            ? await supabaseAdmin.auth.admin.getUserById(product.mentor_profiles.user_id)
            : { data: null };

        if (mentorAuth?.user?.email) {
          const mentorHtml = `
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>New Sale Notification</title>
            </head>
            <body style="margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f6f9fc;">
              <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
                <h1 style="color: #0A0A0A; font-size: 28px; text-align: center; margin: 0 0 24px;">
                  You Made a Sale! 💰
                </h1>
                
                <p style="color: #333; font-size: 16px; line-height: 24px;">
                  Great news! Someone just purchased your digital product.
                </p>

                <div style="background-color: #ecfdf5; border-radius: 8px; padding: 24px; margin: 24px 0;">
                  <h2 style="color: #0A0A0A; font-size: 20px; margin: 0 0 16px;">Sale Details</h2>
                  
                  <p style="color: #333; font-size: 16px; margin: 8px 0;">
                    <strong>Product:</strong> ${product.title}
                  </p>
                  
                  <p style="color: #333; font-size: 16px; margin: 8px 0;">
                    <strong>Amount Earned:</strong> $${Number(product.price).toFixed(2)}
                  </p>
                  
                  <p style="color: #333; font-size: 16px; margin: 8px 0;">
                    <strong>Total Sales:</strong> ${product.sales_count + 1}
                  </p>
                </div>

                <p style="color: #333; font-size: 16px; line-height: 24px;">
                  View all your sales and earnings in your Mentor Cabinet.
                </p>

                <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
                  Brain Bulders - Empowering personal and professional growth
                </p>
              </div>
            </body>
            </html>
          `;

          await resend.emails.send({
            from: 'Brain Bulders <onboarding@resend.dev>',
            to: [mentorAuth.user.email],
            subject: `New Sale: ${product.title}`,
            html: mentorHtml,
          });
          console.log("[VERIFY-PRODUCT-PURCHASE] Mentor notification email sent");
        }
      } catch (emailError) {
        console.error("[VERIFY-PRODUCT-PURCHASE] Mentor email error:", emailError);
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        productTitle: product.title,
        downloadUrl: signedUrlData?.signedUrl || product.file_url,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "An error occurred";
    console.error("[VERIFY-PRODUCT-PURCHASE] Error:", error);
    return new Response(JSON.stringify({ error: errorMessage, success: false }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});