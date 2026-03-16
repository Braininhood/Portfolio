import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Loader2, Send } from "lucide-react";

interface QuestionSubmissionFormProps {
  mentorId: string;
  mentorName: string;
  onSuccess?: () => void;
}

export const QuestionSubmissionForm = ({ mentorId, mentorName, onSuccess }: QuestionSubmissionFormProps) => {
  const [question, setQuestion] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) {
      toast({
        title: "Error",
        description: "Please enter your question",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        toast({
          title: "Error",
          description: "You must be logged in to ask questions",
          variant: "destructive",
        });
        return;
      }

      const { error } = await supabase
        .from("mentor_questions")
        .insert({
          user_id: user.id,
          mentor_id: mentorId,
          question_text: question,
          status: "submitted",
        });

      if (error) throw error;

      toast({
        title: "Question Submitted!",
        description: `Your question has been sent to ${mentorName}. You'll be notified when they respond.`,
      });

      setQuestion("");
      onSuccess?.();
    } catch (error) {
      console.error("Error submitting question:", error);
      toast({
        title: "Error",
        description: "Failed to submit question. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask {mentorName} a Question</CardTitle>
        <CardDescription>
          Submit a question and receive a personalized video answer (up to 10 minutes)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="question">Your Question</Label>
            <Textarea
              id="question"
              placeholder="What would you like to know?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={5}
              disabled={isSubmitting}
            />
          </div>
          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Submit Question
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
