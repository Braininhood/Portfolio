import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
// @ts-ignore: npm specifier
import Stripe from "npm:stripe@^14.0.0";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";
// @ts-ignore: esm.sh
import { Resend } from "https://esm.sh/resend@4.0.0";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { sessionId, bookingId } = await req.json();

    console.log("[CONFIRM-BOOKING] Confirming booking:", { sessionId, bookingId });

    if (!sessionId || !bookingId) {
      throw new Error("Missing session ID or booking ID");
    }

    const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") || "", {
      apiVersion: "2023-10-16",
    });

    const resend = new Resend(Deno.env.get("RESEND_API_KEY") as string);

    // Create Supabase client
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Verify payment was successful
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    
    if (session.payment_status !== "paid") {
      throw new Error("Payment not completed");
    }

    console.log("[CONFIRM-BOOKING] Payment verified");

    // Update booking status
    const { data: booking, error: updateError } = await supabaseClient
      .from("bookings")
      .update({
        status: "confirmed",
        stripe_payment_intent_id: session.payment_intent as string,
      })
      .eq("id", bookingId)
      .select()
      .single();

    if (updateError) {
      console.error("[CONFIRM-BOOKING] Error updating booking:", updateError);
      throw new Error(`Failed to confirm booking: ${updateError.message}`);
    }

    console.log("[CONFIRM-BOOKING] Booking confirmed:", booking);

    // Format date for email
    const formattedDate = new Date(booking.booking_date + 'T00:00:00').toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    const userName = booking.user_email.split('@')[0];

    // Create HTML email content
    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Booking Confirmed</title>
        </head>
        <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f6f9fc;">
          <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
            <h1 style="color: #0A0A0A; font-family: Manrope, -apple-system, sans-serif; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
              Booking Confirmed! 🎉
            </h1>
            
            <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
              Hi ${userName},
            </p>
            
            <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
              Great news! Your mentorship session has been successfully confirmed.
            </p>

            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 24px; margin: 24px 0;">
              <h2 style="color: #0A0A0A; font-size: 24px; font-weight: bold; margin: 0 0 16px;">Session Details</h2>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Mentor:</strong> ${booking.mentor_name}
              </p>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Date:</strong> ${formattedDate}
              </p>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Time:</strong> ${booking.booking_time}
              </p>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Duration:</strong> 60 minutes
              </p>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Price:</strong> $${parseFloat(booking.price)}
              </p>
              
              <p style="color: #333; font-size: 16px; margin: 8px 0;">
                <strong>Booking ID:</strong> ${booking.id}
              </p>
            </div>

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">

            <div style="margin: 24px 0;">
              <h3 style="color: #0A0A0A; font-size: 20px; font-weight: bold; margin: 0 0 12px;">What's Next?</h3>
              
              <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
                • You'll receive a calendar invitation shortly
              </p>
              <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
                • Your mentor will contact you before the session
              </p>
              <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
                • Prepare any questions you'd like to discuss
              </p>
            </div>

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">

            <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
              Need to reschedule or cancel? Visit your dashboard to manage your bookings.
            </p>

            <p style="color: #898989; font-size: 12px; line-height: 20px; margin-top: 32px; text-align: center;">
              <a href="https://g-creators.lovable.app" style="color: #898989; text-decoration: underline;">Brain Bulders</a>
              <br>
              Empowering personal and professional growth
            </p>
          </div>
        </body>
      </html>
    `;

    // Generate calendar event (.ics file)
    const calendarEvent = generateICSFile({
      title: `Mentorship Session with ${booking.mentor_name}`,
      description: `Your scheduled mentorship session with ${booking.mentor_name}`,
      startDate: booking.booking_date,
      startTime: booking.booking_time,
      duration: 60,
      attendeeEmail: booking.user_email,
      bookingId: booking.id,
    });

    // Send confirmation email with ICS attachment
    const { error: emailError } = await resend.emails.send({
      from: 'Brain Bulders <onboarding@resend.dev>',
      to: [booking.user_email],
      subject: `Session Confirmed with ${booking.mentor_name}!`,
      html,
      attachments: [
        {
          filename: 'session.ics',
          content: btoa(calendarEvent),
        },
      ],
    });

    if (emailError) {
      console.error("[CONFIRM-BOOKING] Error sending email:", emailError);
      // Don't fail the request if email fails
    } else {
      console.log("[CONFIRM-BOOKING] Confirmation email sent with ICS attachment");
    }

    return new Response(
      JSON.stringify({
        success: true,
        booking: booking,
        calendarEvent: calendarEvent,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("[CONFIRM-BOOKING] Error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "An error occurred",
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

// Helper function to generate ICS calendar file
function generateICSFile({
  title,
  description,
  startDate,
  startTime,
  duration,
  attendeeEmail,
  bookingId,
}: {
  title: string;
  description: string;
  startDate: string;
  startTime: string;
  duration: number;
  attendeeEmail: string;
  bookingId?: string;
}) {
  const [hours, minutes] = startTime.split(':');
  const start = new Date(`${startDate}T${hours}:${minutes}:00`);
  const end = new Date(start.getTime() + duration * 60 * 1000);

  const formatDate = (date: Date) => {
    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };

  const uid = bookingId || Date.now().toString();

  const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Brain Bulders//Booking//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:${uid}@g-creators.com
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(start)}
DTEND:${formatDate(end)}
SUMMARY:${title}
DESCRIPTION:${description}
LOCATION:Online Meeting
ATTENDEE:mailto:${attendeeEmail}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:Session tomorrow at ${startTime}
END:VALARM
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:DISPLAY
DESCRIPTION:Session starting in 1 hour
END:VALARM
END:VEVENT
END:VCALENDAR`;

  return icsContent;
}

