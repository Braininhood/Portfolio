import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bot, Sparkles, Eye, RefreshCw, MessageSquare, Users, Zap, BookOpen } from "lucide-react";
import { AvatarCreationWizard } from "./AvatarCreationWizard";
import { KnowledgeBaseManager } from "./KnowledgeBaseManager";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface AvatarManagementTabProps {
  mentorId: string;
}

interface AvatarAnalytics {
  total_conversations: number;
  total_messages: number;
  unique_users: number;
  total_tokens_used: number;
  last_conversation_at: string | null;
}

export const AvatarManagementTab = ({ mentorId }: AvatarManagementTabProps) => {
  const [avatar, setAvatar] = useState<any>(null);
  const [analytics, setAnalytics] = useState<AvatarAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    fetchAvatar();
  }, [mentorId]);

  const fetchAvatar = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("mentor_avatars")
      .select("*")
      .eq("mentor_id", mentorId)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) {
      console.error("Error fetching avatar:", error);
    } else {
      setAvatar(data);
      if (data) fetchAnalytics(data.id);
    }
    setLoading(false);
  };

  const fetchAnalytics = async (avatarId: string) => {
    const { data, error } = await supabase.rpc("get_avatar_stats" as any, {
      p_avatar_id: avatarId,
    });

    if (!error && data && data.length > 0) {
      const row = data[0];
      setAnalytics({
        total_conversations: Number(row.total_conversations) || 0,
        total_messages: Number(row.total_user_messages) || 0,
        unique_users: Number(row.unique_users) || 0,
        total_tokens_used: Number(row.total_tokens_used) || 0,
        last_conversation_at: row.last_conversation_at,
      });
    } else {
      setAnalytics({ total_conversations: 0, total_messages: 0, unique_users: 0, total_tokens_used: 0, last_conversation_at: null });
    }
  };

  const handleQuickRetrain = async () => {
    if (!avatar) return;
    setRetraining(true);
    try {
      const { error } = await supabase.functions.invoke("train-avatar", {
        body: {
          avatarId: avatar.id,
          mentorId,
          bioSummary: avatar.bio_summary,
          expertiseAreas: avatar.expertise_areas || [],
          personalityTraits: avatar.personality_traits || [],
        },
      });
      if (error) throw error;
      toast.success("Avatar retrained successfully!", {
        description: "All knowledge base entries and profile data have been applied.",
      });
      fetchAvatar();
    } catch (err: any) {
      toast.error("Retraining failed", { description: err.message || "Please try again." });
    } finally {
      setRetraining(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ready":
        return <Badge className="bg-green-500 hover:bg-green-600">Ready</Badge>;
      case "training":
        return <Badge variant="secondary" className="animate-pulse">Training...</Badge>;
      case "draft":
        return <Badge variant="outline">Draft</Badge>;
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      default:
        return null;
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading...</div>;
  }

  if (showWizard) {
    return (
      <div>
        <Button variant="outline" onClick={() => setShowWizard(false)} className="mb-4">
          ← Back
        </Button>
        <AvatarCreationWizard
          mentorId={mentorId}
          existingAvatar={avatar}
          onSuccess={() => {
            fetchAvatar();
            setShowWizard(false);
            toast.success("Avatar updated successfully!");
          }}
        />
      </div>
    );
  }

  if (showPreview && avatar) {
    return (
      <div>
        <Button variant="outline" onClick={() => setShowPreview(false)} className="mb-4">
          ← Back to Dashboard
        </Button>
        <Card className="flex flex-col h-[300px] items-center justify-center text-center p-8">
          <Bot className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="font-semibold text-lg mb-2">Avatar chat is for learners</h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-md">
            As a mentor, you can view and manage this avatar from your dashboard. Learners chat with your avatar from your mentor profile.
          </p>
          <p className="text-xs text-muted-foreground">
            Use the Analytics and Knowledge Base tabs above to manage your avatar.
          </p>
        </Card>
      </div>
    );
  }

  if (!avatar) {
    return (
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto w-20 h-20 bg-accent/10 rounded-full flex items-center justify-center mb-4">
            <Bot className="text-accent" size={40} />
          </div>
          <CardTitle>Create Your AI Avatar</CardTitle>
          <CardDescription className="max-w-2xl mx-auto">
            Set up an AI-powered version of yourself that can interact with students 24/7.
            Your avatar will answer questions, recommend your content, and help users book sessions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid md:grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-2">📸 Upload Photos</h4>
              <p className="text-sm text-muted-foreground">1-5 photos to personalize your avatar</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-2">🧠 AI Training</h4>
              <p className="text-sm text-muted-foreground">Trained on your expertise and content</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-2">📚 Knowledge Base</h4>
              <p className="text-sm text-muted-foreground">Add custom FAQs and service info</p>
            </div>
          </div>
          <div className="flex justify-center">
            <Button variant="hero" size="lg" onClick={() => setShowWizard(true)} className="w-full max-w-md">
              <Sparkles className="mr-2" />
              Create AI Avatar
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Avatar Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center shrink-0 overflow-hidden">
                {avatar.photo_urls?.[0] ? (
                  <img src={avatar.photo_urls[0]} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <Bot className="text-accent" size={32} />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <CardTitle>{avatar.avatar_name || "Your AI Avatar"}</CardTitle>
                  {getStatusBadge(avatar.status)}
                </div>
                <CardDescription>{avatar.bio_summary}</CardDescription>
                {avatar.last_trained_at && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Last trained: {new Date(avatar.last_trained_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
            <div className="flex gap-2 shrink-0 flex-wrap justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPreview(true)}
                disabled={avatar.status !== "ready"}
                title="Avatar chat is for learners"
              >
                <Eye size={16} className="mr-2" />
                Learner View
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleQuickRetrain}
                disabled={retraining || avatar.status === "training"}
                title="Retrain using current settings + all knowledge base entries"
              >
                <RefreshCw size={16} className={`mr-2 ${retraining ? "animate-spin" : ""}`} />
                {retraining ? "Retraining..." : "Retrain Now"}
              </Button>
              <Button variant="outline" size="sm" onClick={() => setShowWizard(true)}>
                <Sparkles size={16} className="mr-2" />
                Edit Avatar
              </Button>
            </div>
          </div>
        </CardHeader>

        {avatar.status === "ready" && (
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {avatar.expertise_areas?.map((area: string, i: number) => (
                <Badge key={i} variant="secondary">{area}</Badge>
              ))}
              {avatar.personality_traits?.map((trait: string, i: number) => (
                <Badge key={i} variant="outline">{trait}</Badge>
              ))}
            </div>
          </CardContent>
        )}

        {avatar.status === "training" && (
          <CardContent>
            <div className="p-4 bg-muted border border-border rounded-lg">
              <p className="text-sm">🔄 Your avatar is being trained. This usually takes 1–3 minutes.</p>
            </div>
          </CardContent>
        )}

        {avatar.status === "error" && (
          <CardContent>
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">
                ❌ Training failed. Check that your OpenAI API key is configured, then click Retry.
              </p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Tabs: Analytics + Knowledge Base */}
      {avatar.status === "ready" && (
        <Tabs defaultValue="analytics">
          <TabsList>
            <TabsTrigger value="analytics">
              <Zap className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="knowledge">
              <BookOpen className="h-4 w-4 mr-2" />
              Knowledge Base
            </TabsTrigger>
          </TabsList>

          <TabsContent value="analytics" className="mt-4">
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <MessageSquare className="h-6 w-6 mx-auto mb-2 text-primary" />
                  <div className="text-2xl font-bold">{analytics?.total_conversations ?? 0}</div>
                  <p className="text-sm text-muted-foreground">Conversations</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <MessageSquare className="h-6 w-6 mx-auto mb-2 text-blue-500" />
                  <div className="text-2xl font-bold">{analytics?.total_messages ?? 0}</div>
                  <p className="text-sm text-muted-foreground">Messages Sent</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Users className="h-6 w-6 mx-auto mb-2 text-green-500" />
                  <div className="text-2xl font-bold">{analytics?.unique_users ?? 0}</div>
                  <p className="text-sm text-muted-foreground">Unique Users</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Zap className="h-6 w-6 mx-auto mb-2 text-yellow-500" />
                  <div className="text-2xl font-bold">
                    {analytics?.total_tokens_used
                      ? analytics.total_tokens_used.toLocaleString()
                      : 0}
                  </div>
                  <p className="text-sm text-muted-foreground">Tokens Used</p>
                </CardContent>
              </Card>
            </div>
            {analytics?.last_conversation_at && (
              <p className="text-xs text-muted-foreground mt-3 text-center">
                Last conversation: {new Date(analytics.last_conversation_at).toLocaleString()}
              </p>
            )}
          </TabsContent>

          <TabsContent value="knowledge" className="mt-4">
            <KnowledgeBaseManager mentorId={mentorId} avatarId={avatar.id} onRetrain={handleQuickRetrain} />
          </TabsContent>
        </Tabs>
      )}

      {/* Knowledge base always accessible even when not ready */}
      {avatar.status !== "ready" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Knowledge Base
            </CardTitle>
            <CardDescription>
              Prepare custom content before training your avatar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <KnowledgeBaseManager mentorId={mentorId} avatarId={avatar.id} onRetrain={handleQuickRetrain} />
          </CardContent>
        </Card>
      )}
    </div>
  );
};
