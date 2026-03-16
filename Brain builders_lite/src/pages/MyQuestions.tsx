import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { VideoAnswerPlayer } from "@/components/VideoAnswerPlayer";
import { Loader2, Clock, CheckCircle2 } from "lucide-react";
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

const MyQuestions = () => {
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [mentorProfiles, setMentorProfiles] = useState<Record<string, MentorProfile>>({});
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) {
      navigate("/auth");
      return;
    }

    loadQuestions(user.id);
  };

  const loadQuestions = async (userId: string) => {
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
        .order("created_at", { ascending: false });

      if (error) throw error;

      // Fetch mentor profiles separately
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

      console.log("Loaded questions:", transformedQuestions);
      setQuestions(transformedQuestions);
    } catch (error) {
      console.error("Error loading questions:", error);
      toast({
        title: "Error",
        description: "Failed to load your questions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const pendingQuestions = questions.filter(q => q.status === "submitted");
  const answeredQuestions = questions.filter(q => q.status === "answered");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8 mt-20">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">My Questions</h1>
          <p className="text-muted-foreground mt-2">
            Track your questions and video answers from mentors
          </p>
        </div>

        <Tabs defaultValue="pending" className="space-y-6">
          <TabsList>
            <TabsTrigger value="pending">
              <Clock className="h-4 w-4 mr-2" />
              Waiting ({pendingQuestions.length})
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
                  No pending questions. Ask a mentor something!
                </CardContent>
              </Card>
            ) : (
              pendingQuestions.map((question) => (
                <Card key={question.id}>
                  <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          {mentorProfiles[question.mentor_id]?.image_url && (
                            <img
                              src={mentorProfiles[question.mentor_id].image_url!}
                              alt={mentorProfiles[question.mentor_id].name}
                              className="h-10 w-10 rounded-full object-cover"
                            />
                          )}
                          <div>
                            <CardTitle className="text-lg">
                              To: {mentorProfiles[question.mentor_id]?.name}
                            </CardTitle>
                          <CardDescription>
                            Asked {formatDistanceToNow(new Date(question.created_at), { addSuffix: true })}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge variant="outline">
                        <Clock className="h-3 w-3 mr-1" />
                        Waiting
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{question.question_text}</p>
                  </CardContent>
                </Card>
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
                      <div className="flex items-center gap-3">
                        {mentorProfiles[question.mentor_id]?.image_url && (
                          <img
                            src={mentorProfiles[question.mentor_id].image_url!}
                            alt={mentorProfiles[question.mentor_id].name}
                            className="h-10 w-10 rounded-full object-cover"
                          />
                        )}
                        <div>
                          <CardTitle className="text-lg">
                            From: {mentorProfiles[question.mentor_id]?.name}
                          </CardTitle>
                          <CardDescription>
                            Answered {question.mentor_video_answers?.[0] && formatDistanceToNow(new Date(question.mentor_video_answers[0].created_at), { addSuffix: true })}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge>
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Answered
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium mb-1">Your Question:</p>
                      <p className="text-sm text-muted-foreground">{question.question_text}</p>
                    </div>
                    {question.mentor_video_answers?.[0] && (
                      <div className="space-y-3">
                        <p className="text-sm font-medium">Video Answer:</p>
                        <VideoAnswerPlayer
                          videoUrl={question.mentor_video_answers[0].video_url}
                          questionId={question.id}
                          durationSeconds={question.mentor_video_answers[0].duration_seconds}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MyQuestions;
