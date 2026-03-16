import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.2";
import { Resend } from "https://esm.sh/resend@4.0.0";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

type EmailType = 
  | "booking_confirmed"
  | "booking_cancelled" 
  | "booking_rescheduled"
  | "reminder_24h"
  | "reminder_1h";

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { emailType, bookingId, recipientEmail, customData } = await req.json();

    console.log("[SEND-NOTIFICATION] Sending email:", { emailType, bookingId, recipientEmail });

    const resend = new Resend(Deno.env.get("RESEND_API_KEY") as string);
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    // Get booking details
    const { data: booking, error: bookingError } = await supabase
      .from("bookings")
      .select(`
        *,
        mentor_profiles!inner(full_name, email:user_id(email)),
        profiles!bookings_user_id_fkey(full_name)
      `)
      .eq("id", bookingId)
      .single();

    if (bookingError || !booking) {
      throw new Error("Booking not found");
    }

    const formattedDate = new Date(booking.booking_date + 'T00:00:00').toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    const learnerName = booking.profiles?.full_name || booking.user_email?.split('@')[0] || "there";
    const mentorName = booking.mentor_profiles?.full_name || "your mentor";

    let subject = "";
    let html = "";
    let attachICS = false;

    switch (emailType) {
      case "booking_confirmed":
        subject = `Session Confirmed with ${mentorName}!`;
        html = getConfirmationEmailHTML(booking, formattedDate, learnerName, mentorName);
        attachICS = true;
        break;

      case "booking_cancelled":
        subject = `Session Cancelled - ${mentorName}`;
        html = getCancellationEmailHTML(booking, formattedDate, learnerName, mentorName);
        break;

      case "booking_rescheduled":
        subject = `Session Rescheduled - ${mentorName}`;
        html = getRescheduleEmailHTML(booking, formattedDate, learnerName, mentorName, customData);
        attachICS = true;
        break;

      case "reminder_24h":
        subject = `Reminder: Session Tomorrow with ${mentorName}`;
        html = getReminder24hHTML(booking, formattedDate, learnerName, mentorName);
        break;

      case "reminder_1h":
        subject = `Reminder: Session Starting Soon with ${mentorName}`;
        html = getReminder1hHTML(booking, formattedDate, learnerName, mentorName);
        break;
    }

    const emailData: any = {
      from: 'Brain Bulders <onboarding@resend.dev>',
      to: [recipientEmail || booking.user_email],
      subject,
      html,
    };

    // Attach ICS file for confirmations and reschedules
    if (attachICS) {
      const icsContent = generateICSFile({
        title: `Mentorship Session with ${mentorName}`,
        description: `Your scheduled mentorship session with ${mentorName}`,
        startDate: booking.booking_date,
        startTime: booking.booking_time,
        duration: 60,
        attendeeEmail: booking.user_email,
        bookingId: booking.id,
      });

      emailData.attachments = [
        {
          filename: 'session.ics',
          content: Buffer.from(icsContent).toString('base64'),
        },
      ];
    }

    const { error: emailError } = await resend.emails.send(emailData);

    if (emailError) {
      console.error("[SEND-NOTIFICATION] Error sending email:", emailError);
      throw emailError;
    }

    console.log("[SEND-NOTIFICATION] Email sent successfully");

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error) {
    console.error("[SEND-NOTIFICATION] Error:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "An error occurred" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});

// Email Templates
function getConfirmationEmailHTML(booking: any, formattedDate: string, learnerName: string, mentorName: string) {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, sans-serif; background-color: #f6f9fc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
          <h1 style="color: #0A0A0A; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
            🎉 Booking Confirmed!
          </h1>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Hi ${learnerName},
          </p>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Great news! Your mentorship session has been successfully confirmed.
          </p>

          <div style="background-color: #f0f9ff; border-radius: 8px; padding: 24px; margin: 24px 0;">
            <h2 style="color: #0A0A0A; font-size: 24px; font-weight: bold; margin: 0 0 16px;">Session Details</h2>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Mentor:</strong> ${mentorName}</p>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Date:</strong> ${formattedDate}</p>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Time:</strong> ${booking.booking_time}</p>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Duration:</strong> 60 minutes</p>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Price:</strong> $${parseFloat(booking.price)}</p>
          </div>

          <div style="background-color: #fff7ed; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0;">
            <p style="color: #92400e; font-size: 14px; margin: 0;">
              📧 <strong>Calendar Invitation Attached</strong><br>
              Open the attached .ics file to add this session to your calendar automatically!
            </p>
          </div>

          <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
            <a href="https://g-creators.lovable.app" style="color: #898989;">Brain Bulders</a> - Empowering growth
          </p>
        </div>
      </body>
    </html>
  `;
}

function getCancellationEmailHTML(booking: any, formattedDate: string, learnerName: string, mentorName: string) {
  return `
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, sans-serif; background-color: #f6f9fc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
          <h1 style="color: #0A0A0A; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
            Session Cancelled
          </h1>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Hi ${learnerName},
          </p>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Your session with ${mentorName} scheduled for ${formattedDate} at ${booking.booking_time} has been cancelled.
          </p>

          <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 24px 0;">
            <p style="color: #991b1b; font-size: 14px; margin: 0;">
              A full refund has been processed and will appear in your account within 5-10 business days.
            </p>
          </div>

          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            We're sorry this session didn't work out. Feel free to browse our mentors and schedule a new session anytime!
          </p>

          <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
            <a href="https://g-creators.lovable.app" style="color: #898989;">Brain Bulders</a> - Empowering growth
          </p>
        </div>
      </body>
    </html>
  `;
}

function getRescheduleEmailHTML(booking: any, formattedDate: string, learnerName: string, mentorName: string, customData: any) {
  return `
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, sans-serif; background-color: #f6f9fc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
          <h1 style="color: #0A0A0A; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
            Session Rescheduled
          </h1>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Hi ${learnerName},
          </p>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Your session with ${mentorName} has been rescheduled to:
          </p>

          <div style="background-color: #f0fdf4; border-radius: 8px; padding: 24px; margin: 24px 0;">
            <h2 style="color: #0A0A0A; font-size: 20px; font-weight: bold; margin: 0 0 12px;">New Session Time</h2>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Date:</strong> ${formattedDate}</p>
            <p style="color: #333; font-size: 16px; margin: 8px 0;"><strong>Time:</strong> ${booking.booking_time}</p>
          </div>

          <div style="background-color: #fff7ed; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0;">
            <p style="color: #92400e; font-size: 14px; margin: 0;">
              📧 <strong>Updated Calendar Invitation Attached</strong><br>
              Open the attached .ics file to update your calendar!
            </p>
          </div>

          <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
            <a href="https://g-creators.lovable.app" style="color: #898989;">Brain Bulders</a> - Empowering growth
          </p>
        </div>
      </body>
    </html>
  `;
}

function getReminder24hHTML(booking: any, formattedDate: string, learnerName: string, mentorName: string) {
  return `
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, sans-serif; background-color: #f6f9fc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
          <h1 style="color: #0A0A0A; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
            ⏰ Session Tomorrow!
          </h1>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Hi ${learnerName},
          </p>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Just a friendly reminder that your session with <strong>${mentorName}</strong> is tomorrow!
          </p>

          <div style="background-color: #f0f9ff; border-radius: 8px; padding: 24px; margin: 24px 0; text-align: center;">
            <p style="color: #0369a1; font-size: 18px; font-weight: bold; margin: 0;">${formattedDate}</p>
            <p style="color: #0369a1; font-size: 24px; font-weight: bold; margin: 8px 0;">${booking.booking_time}</p>
            <p style="color: #64748b; font-size: 14px; margin: 8px 0;">60 minutes</p>
          </div>

          <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0;">
            <p style="color: #92400e; font-size: 14px; margin: 0;">
              💡 <strong>Preparation Tips:</strong><br>
              • Prepare your questions in advance<br>
              • Test your audio/video setup<br>
              • Be ready 5 minutes early
            </p>
          </div>

          <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
            <a href="https://g-creators.lovable.app" style="color: #898989;">Brain Bulders</a> - Empowering growth
          </p>
        </div>
      </body>
    </html>
  `;
}

function getReminder1hHTML(booking: any, formattedDate: string, learnerName: string, mentorName: string) {
  return `
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 20px 0; font-family: Inter, -apple-system, sans-serif; background-color: #f6f9fc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px;">
          <h1 style="color: #0A0A0A; font-size: 32px; font-weight: bold; text-align: center; margin: 0 0 24px;">
            🔔 Session Starting Soon!
          </h1>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Hi ${learnerName},
          </p>
          
          <p style="color: #333; font-size: 16px; line-height: 24px; margin: 16px 0;">
            Your session with <strong>${mentorName}</strong> starts in <strong>1 hour</strong>!
          </p>

          <div style="background-color: #fee2e2; border-radius: 8px; padding: 24px; margin: 24px 0; text-align: center;">
            <p style="color: #991b1b; font-size: 18px; font-weight: bold; margin: 0;">Starting at</p>
            <p style="color: #991b1b; font-size: 32px; font-weight: bold; margin: 8px 0;">${booking.booking_time}</p>
          </div>

          <div style="background-color: #dcfce7; border-left: 4px solid #16a34a; padding: 16px; margin: 24px 0;">
            <p style="color: #14532d; font-size: 14px; margin: 0;">
              ✅ <strong>Get Ready:</strong><br>
              • Join 5 minutes early<br>
              • Have your questions ready<br>
              • Good luck with your session!
            </p>
          </div>

          <p style="color: #898989; font-size: 12px; text-align: center; margin-top: 32px;">
            <a href="https://g-creators.lovable.app/dashboard" style="color: #898989;">View Dashboard</a>
          </p>
        </div>
      </body>
    </html>
  `;
}

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
  bookingId: string;
}) {
  const [hours, minutes] = startTime.split(':');
  const start = new Date(`${startDate}T${hours}:${minutes}:00`);
  const end = new Date(start.getTime() + duration * 60 * 1000);

  const formatDate = (date: Date) => {
    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };

  const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Brain Bulders//Booking//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:${bookingId}@g-creators.com
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
