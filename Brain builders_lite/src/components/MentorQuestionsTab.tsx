import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { VideoAnswerUploader } from "@/components/VideoAnswerUploader";
import { Loader2, MessageCircle, CheckCircle2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Question {
  id: string;
  question_text: string;
  status: string;
  created_at: string;
  user_id: string;
  mentor_video_answers?: Array<{
    video_url: string;
    duration_seconds: number;
  }>;
}

interface UserProfile {
  full_name: string | null;
}

interface MentorQuestionsTabProps {
  mentorId: string;
}

export const MentorQuestionsTab = ({ mentorId }: MentorQuestionsTabProps) => {
  const [loading, setLoading] = useState(true);
  const [pendingQuestions, setPendingQuestions] = useState<Question[]>([]);
  const [answeredQuestions, setAnsweredQuestions] = useState<Question[]>([]);
  const [userProfiles, setUserProfiles] = useState<Record<string, UserProfile>>({});
  const { toast } = useToast();

  useEffect(() => {
    loadQuestions();
  }, [mentorId]);

  const loadQuestions = async () => {
    setLoading(true);

    try {
      const { data, error } = await supabase
        .from("mentor_questions")
        .select(`
          id,
          question_text,
          status,
          created_at,
          user_id,
          mentor_video_answers!mentor_video_answers_question_id_fkey (video_url, duration_seconds)
        `)
        .eq("mentor_id", mentorId)
        .order("created_at", { ascending: false });

      if (error) throw error;

      // Fetch user profiles separately
      const userIds = [...new Set(data?.map(q => q.user_id) || [])];
      if (userIds.length > 0) {
        const { data: profiles } = await supabase
          .from("profiles")
          .select("id, full_name")
          .in("id", userIds);

        const profileMap: Record<string, UserProfile> = {};
        profiles?.forEach(p => {
          profileMap[p.id] = { full_name: p.full_name };
        });
        setUserProfiles(profileMap);
      }

      const pending = (data || []).map(q => ({
        ...q,
        mentor_video_answers: Array.isArray(q.mentor_video_answers) ? q.mentor_video_answers : []
      })).filter(q => q.status === "submitted");
      
      const answered = (data || []).map(q => ({
        ...q,
        mentor_video_answers: Array.isArray(q.mentor_video_answers) ? q.mentor_video_answers : []
      })).filter(q => q.status === "answered");

      setPendingQuestions(pending);
      setAnsweredQuestions(answered);
    } catch (error) {
      console.error("Error loading questions:", error);
      toast({
        title: "Error",
        description: "Failed to load questions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Questions from Mentees</h2>
        <p className="text-muted-foreground">
          Answer questions with personalized video responses
        </p>
      </div>

      <Tabs defaultValue="pending" className="space-y-6">
        <TabsList>
          <TabsTrigger value="pending">
            <MessageCircle className="h-4 w-4 mr-2" />
            Pending ({pendingQuestions.length})
          </TabsTrigger>
          <TabsTrigger value="answered">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Answered ({answeredQuestions.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {pendingQuestions.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                No pending questions
              </CardContent>
            </Card>
          ) : (
            pendingQuestions.map((question) => (
              <div key={question.id} className="grid md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {userProfiles[question.user_id]?.full_name?.trim() || "Learner"}
                        </CardTitle>
                        <CardDescription>
                          {formatDistanceToNow(new Date(question.created_at), { addSuffix: true })}
                        </CardDescription>
                      </div>
                      <Badge variant="outline">Pending</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{question.question_text}</p>
                  </CardContent>
                </Card>
                <VideoAnswerUploader
                  questionId={question.id}
                  questionText={question.question_text}
                  onSuccess={loadQuestions}
                />
              </div>
            ))
          )}
        </TabsContent>

        <TabsContent value="answered" className="space-y-4">
          {answeredQuestions.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                No answered questions yet
              </CardContent>
            </Card>
          ) : (
            answeredQuestions.map((question) => (
              <Card key={question.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">
                        {userProfiles[question.user_id]?.full_name?.trim() || "Learner"}
                      </CardTitle>
                      <CardDescription>
                        {formatDistanceToNow(new Date(question.created_at), { addSuffix: true })}
                      </CardDescription>
                    </div>
                    <Badge>Answered</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm">{question.question_text}</p>
                  {question.mentor_video_answers?.[0] && (
                    <video
                      controls
                      className="w-full rounded-lg max-w-2xl"
                      src={question.mentor_video_answers[0].video_url}
                    />
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};
