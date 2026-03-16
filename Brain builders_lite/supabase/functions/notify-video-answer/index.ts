import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.3";
import { Resend } from "https://esm.sh/resend@4.0.0";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface NotifyVideoAnswerRequest {
  questionId: string;
  mentorName: string;
}

const handler = async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
      {
        auth: {
          persistSession: false,
        },
      }
    );

    const { questionId, mentorName }: NotifyVideoAnswerRequest = await req.json();

    console.log("Sending video answer notification for question:", questionId);

    // Get the question to find the user
    const { data: question, error: questionError } = await supabaseClient
      .from("mentor_questions")
      .select("user_id, question_text")
      .eq("id", questionId)
      .single();

    if (questionError || !question) {
      console.error("Error fetching question:", questionError);
      throw new Error("Failed to fetch question");
    }

    // Get user's profile
    const { data: profile, error: profileError } = await supabaseClient
      .from("profiles")
      .select("full_name")
      .eq("id", question.user_id)
      .single();

    if (profileError) {
      console.error("Error fetching profile:", profileError);
    }

    // Get user's email from auth.users
    const { data: { user }, error: userError } = await supabaseClient.auth.admin.getUserById(question.user_id);

    if (userError || !user?.email) {
      console.error("Error fetching user email:", userError);
      throw new Error("Failed to fetch user email");
    }

    const recipientEmail = user.email;
    const recipientName = profile?.full_name || "there";
    const questionPreview = question.question_text.length > 100 
      ? question.question_text.substring(0, 100) + "..." 
      : question.question_text;

    // Send email notification
    const emailResponse = await resend.emails.send({
      from: "MentorMatch <onboarding@resend.dev>",
      to: [recipientEmail],
      subject: `🎬 ${mentorName} answered your question with a video!`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #333; margin-bottom: 24px;">Hi ${recipientName}! 👋</h2>
          
          <p style="color: #666; line-height: 1.6; font-size: 16px;">
            Great news! <strong>${mentorName}</strong> has recorded a personalized video answer to your question:
          </p>
          
          <div style="background-color: #f5f5f5; padding: 16px; border-radius: 8px; margin: 24px 0; border-left: 4px solid #6366f1;">
            <p style="color: #555; margin: 0; font-style: italic;">"${questionPreview}"</p>
          </div>
          
          <div style="text-align: center; margin: 32px 0;">
            <a href="${Deno.env.get("SITE_URL") || "https://mentormatch.com"}/my-questions" 
               style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
              🎥 Watch Your Video Answer
            </a>
          </div>
          
          <p style="color: #666; line-height: 1.6; font-size: 14px;">
            You can watch and download the video from your dashboard at any time.
          </p>
          
          <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;" />
          
          <p style="color: #999; font-size: 12px; text-align: center;">
            This is an automated notification from MentorMatch.<br/>
            You received this because you asked a question to a mentor.
          </p>
        </div>
      `,
    });

    console.log("Email sent successfully:", emailResponse);

    return new Response(JSON.stringify({ success: true, emailResponse }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        ...corsHeaders,
      },
    });
  } catch (error: any) {
    console.error("Error in notify-video-answer function:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      }
    );
  }
};

serve(handler);
