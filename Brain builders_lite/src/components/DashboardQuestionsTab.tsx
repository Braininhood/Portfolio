import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { VideoAnswerPlayer } from "@/components/VideoAnswerPlayer";
import { Clock, CheckCircle2, MessageCircle, Play } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Question {
  id: string;
  question_text: string;
  status: string;
  created_at: string;
  mentor_id: string;
  mentor_video_answers?: Array<{
    video_url: string;
    duration_seconds: number;
    created_at: string;
  }>;
}

interface MentorProfile {
  name: string;
  image_url: string | null;
}

interface DashboardQuestionsTabProps {
  userId: string;
}

export const DashboardQuestionsTab = ({ userId }: DashboardQuestionsTabProps) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [mentorProfiles, setMentorProfiles] = useState<Record<string, MentorProfile>>({});
  const [loading, setLoading] = useState(true);
  const [expandedVideo, setExpandedVideo] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (userId) {
      loadQuestions();
    }
  }, [userId]);

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
          mentor_id,
          mentor_video_answers!mentor_video_answers_question_id_fkey (video_url, duration_seconds, created_at)
        `)
        .eq("user_id", userId)
        .order("created_at", { ascending: false })
        .limit(10);

      if (error) throw error;

      const mentorIds = [...new Set(data?.map(q => q.mentor_id) || [])];
      const { data: mentors } = await supabase
        .from("mentor_profiles")
        .select("id, name, image_url")
        .in("id", mentorIds);

      const mentorMap: Record<string, MentorProfile> = {};
      mentors?.forEach(m => {
        mentorMap[m.id] = { name: m.name, image_url: m.image_url };
      });
      setMentorProfiles(mentorMap);

      const transformedQuestions = (data || []).map(q => ({
        ...q,
        mentor_video_answers: Array.isArray(q.mentor_video_answers) 
          ? q.mentor_video_answers 
          : q.mentor_video_answers 
            ? [q.mentor_video_answers] 
            : []
      }));

      console.log("Dashboard loaded questions:", transformedQuestions);
      setQuestions(transformedQuestions);
    } catch (error) {
      console.error("Error loading questions:", error);
    } finally {
      setLoading(false);
    }
  };

  const pendingQuestions = questions.filter(q => q.status === "submitted");
  const answeredQuestions = questions.filter(q => q.status === "answered");
  const hasNewAnswers = answeredQuestions.some(q => {
    const answer = q.mentor_video_answers?.[0];
    if (!answer) return false;
    const answerDate = new Date(answer.created_at);
    const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return answerDate > dayAgo;
  });

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              My Questions
              {hasNewAnswers && (
                <Badge variant="default" className="animate-pulse">New!</Badge>
              )}
            </CardTitle>
            <CardDescription>Questions you've asked mentors and their video answers</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => navigate("/learner/my-questions")}>
            View All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {questions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageCircle className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No questions yet</p>
            <Button className="mt-4" onClick={() => navigate("/mentors")}>
              Ask a Mentor
            </Button>
          </div>
        ) : (
          <Tabs defaultValue={answeredQuestions.length > 0 ? "answered" : "pending"}>
            <TabsList className="mb-4">
              <TabsTrigger value="answered" className="gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Answered ({answeredQuestions.length})
              </TabsTrigger>
              <TabsTrigger value="pending" className="gap-2">
                <Clock className="h-4 w-4" />
                Pending ({pendingQuestions.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="answered" className="space-y-4">
              {answeredQuestions.length === 0 ? (
                <p className="text-center py-4 text-muted-foreground">No answered questions yet</p>
              ) : (
                answeredQuestions.slice(0, 3).map((question) => (
                  <div key={question.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      {mentorProfiles[question.mentor_id]?.image_url && (
                        <img
                          src={mentorProfiles[question.mentor_id].image_url!}
                          alt={mentorProfiles[question.mentor_id].name}
                          className="h-10 w-10 rounded-full object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium">{mentorProfiles[question.mentor_id]?.name}</p>
                        <p className="text-sm text-muted-foreground line-clamp-2">{question.question_text}</p>
                      </div>
                      <Badge variant="secondary" className="shrink-0">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Answered
                      </Badge>
                    </div>

                    {question.mentor_video_answers?.[0] && (
                      <>
                        {expandedVideo === question.id ? (
                          <VideoAnswerPlayer
                            videoUrl={question.mentor_video_answers[0].video_url}
                            questionId={question.id}
                            durationSeconds={question.mentor_video_answers[0].duration_seconds}
                          />
                        ) : (
                          <Button
                            variant="outline"
                            className="w-full"
                            onClick={() => setExpandedVideo(question.id)}
                          >
                            <Play className="h-4 w-4 mr-2" />
                            Watch Video Answer
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                ))
              )}
            </TabsContent>

            <TabsContent value="pending" className="space-y-4">
              {pendingQuestions.length === 0 ? (
                <p className="text-center py-4 text-muted-foreground">No pending questions</p>
              ) : (
                pendingQuestions.slice(0, 3).map((question) => (
                  <div key={question.id} className="border rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      {mentorProfiles[question.mentor_id]?.image_url && (
                        <img
                          src={mentorProfiles[question.mentor_id].image_url!}
                          alt={mentorProfiles[question.mentor_id].name}
                          className="h-10 w-10 rounded-full object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium">{mentorProfiles[question.mentor_id]?.name}</p>
                        <p className="text-sm text-muted-foreground line-clamp-2">{question.question_text}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Asked {formatDistanceToNow(new Date(question.created_at), { addSuffix: true })}
                        </p>
                      </div>
                      <Badge variant="outline" className="shrink-0">
                        <Clock className="h-3 w-3 mr-1" />
                        Waiting
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
};
