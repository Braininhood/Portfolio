import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Bot, RefreshCw, Eye, EyeOff, MessageSquare, Zap, Users,
  BookOpen, RotateCcw, AlertTriangle, ChevronDown, ChevronUp
} from "lucide-react";
import { toast } from "sonner";
import { KnowledgeBaseManager } from "@/components/KnowledgeBaseManager";
import { AvatarChatInterface } from "@/components/AvatarChatInterface";

interface AvatarRow {
  avatar_id: string;
  avatar_name: string;
  mentor_name: string;
  mentor_id: string;
  status: string;
  total_conversations: number;
  total_user_messages: number;
  unique_users: number;
  total_tokens_used: number;
  last_conversation_at: string | null;
  last_trained_at: string | null;
}

export default function AdminAvatars() {
  const [avatars, setAvatars] = useState<AvatarRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarRow | null>(null);
  const [detailTab, setDetailTab] = useState("overview");
  const [retrainingId, setRetrainingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => { fetchAvatars(); }, []);

  const fetchAvatars = async () => {
    setLoading(true);
    const { data, error } = await supabase.rpc("get_all_avatar_stats" as any);
    if (!error && data) setAvatars(data as AvatarRow[]);
    setLoading(false);
  };

  const handleToggleStatus = async (avatar: AvatarRow) => {
    const newStatus = avatar.status === "ready" ? "disabled" : "ready";
    const { error } = await supabase
      .from("mentor_avatars")
      .update({ status: newStatus })
      .eq("id", avatar.avatar_id);
    if (error) {
      toast.error("Failed to update status");
    } else {
      toast.success(`Avatar ${newStatus === "ready" ? "enabled" : "disabled"}`);
      fetchAvatars();
    }
  };

  const handleRetrain = async (avatar: AvatarRow) => {
    setRetrainingId(avatar.avatar_id);
    try {
      // Get full avatar data for bio/expertise/traits
      const { data: avatarData } = await supabase
        .from("mentor_avatars")
        .select("bio_summary, expertise_areas, personality_traits")
        .eq("id", avatar.avatar_id)
        .single();

      const { error } = await supabase.functions.invoke("train-avatar", {
        body: {
          avatarId: avatar.avatar_id,
          mentorId: avatar.mentor_id,
          bioSummary: avatarData?.bio_summary || "",
          expertiseAreas: avatarData?.expertise_areas || [],
          personalityTraits: avatarData?.personality_traits || [],
        },
      });
      if (error) throw error;
      toast.success(`${avatar.avatar_name || "Avatar"} retrained successfully`);
      fetchAvatars();
    } catch (err: any) {
      toast.error("Retraining failed", { description: err.message });
    } finally {
      setRetrainingId(null);
    }
  };

  const totalConversations = avatars.reduce((s, a) => s + Number(a.total_conversations), 0);
  const totalTokens = avatars.reduce((s, a) => s + Number(a.total_tokens_used), 0);
  const totalMessages = avatars.reduce((s, a) => s + Number(a.total_user_messages), 0);
  const readyCount = avatars.filter(a => a.status === "ready").length;

  if (loading) {
    return <div className="py-12 text-center text-muted-foreground">Loading avatars...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Bot className="h-5 w-5 mx-auto mb-1 text-primary" />
            <div className="text-2xl font-bold">{avatars.length}</div>
            <p className="text-xs text-muted-foreground">Total Avatars</p>
            <p className="text-xs text-green-600 font-medium">{readyCount} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <MessageSquare className="h-5 w-5 mx-auto mb-1 text-blue-500" />
            <div className="text-2xl font-bold">{totalConversations}</div>
            <p className="text-xs text-muted-foreground">Conversations</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Users className="h-5 w-5 mx-auto mb-1 text-green-500" />
            <div className="text-2xl font-bold">{totalMessages}</div>
            <p className="text-xs text-muted-foreground">Messages Sent</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Zap className="h-5 w-5 mx-auto mb-1 text-yellow-500" />
            <div className="text-2xl font-bold">{totalTokens.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Tokens Used</p>
          </CardContent>
        </Card>
      </div>

      {avatars.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Bot className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-40" />
            <p className="text-muted-foreground">No AI avatars created yet</p>
            <p className="text-sm text-muted-foreground mt-1">Mentors can create avatars from their dashboard</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              All Mentor Avatars
            </CardTitle>
            <CardDescription>Manage, monitor and control all AI avatars on the platform</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Avatar / Mentor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Conv.</TableHead>
                  <TableHead className="text-right">Msgs</TableHead>
                  <TableHead className="text-right">Tokens</TableHead>
                  <TableHead>Last Active</TableHead>
                  <TableHead>Last Trained</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {avatars.map((a) => (
                  <>
                    <TableRow key={a.avatar_id} className="cursor-pointer hover:bg-muted/30">
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{a.avatar_name || "Unnamed Avatar"}</p>
                          <p className="text-xs text-muted-foreground">{a.mentor_name}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={a.status === "ready" ? "default" : a.status === "training" ? "secondary" : "outline"}
                          className={a.status === "ready" ? "bg-green-500 hover:bg-green-600" : a.status === "disabled" ? "text-muted-foreground" : ""}
                        >
                          {a.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-sm">{Number(a.total_conversations)}</TableCell>
                      <TableCell className="text-right text-sm">{Number(a.total_user_messages)}</TableCell>
                      <TableCell className="text-right text-sm">{Number(a.total_tokens_used).toLocaleString()}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {a.last_conversation_at ? new Date(a.last_conversation_at).toLocaleDateString() : "Never"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {a.last_trained_at ? new Date(a.last_trained_at).toLocaleDateString() : "Never"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 justify-end">
                          <Button
                            variant="ghost" size="sm" className="h-8 w-8 p-0"
                            title="Retrain avatar"
                            disabled={retrainingId === a.avatar_id || a.status === "training"}
                            onClick={() => handleRetrain(a)}
                          >
                            <RotateCcw className={`h-3.5 w-3.5 ${retrainingId === a.avatar_id ? "animate-spin" : ""}`} />
                          </Button>
                          <Button
                            variant="ghost" size="sm" className="h-8 w-8 p-0"
                            title={a.status === "ready" ? "Disable avatar" : "Enable avatar"}
                            onClick={() => handleToggleStatus(a)}
                          >
                            {a.status === "ready"
                              ? <EyeOff className="h-3.5 w-3.5 text-muted-foreground" />
                              : <Eye className="h-3.5 w-3.5 text-green-600" />
                            }
                          </Button>
                          <Button
                            variant="ghost" size="sm" className="h-8 w-8 p-0"
                            title="Manage this avatar"
                            onClick={() => {
                              setSelectedAvatar(a);
                              setDetailTab("overview");
                            }}
                          >
                            {expandedId === a.avatar_id
                              ? <ChevronUp className="h-3.5 w-3.5" />
                              : <ChevronDown className="h-3.5 w-3.5" />
                            }
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Detail dialog */}
      <Dialog open={!!selectedAvatar} onOpenChange={(open) => { if (!open) setSelectedAvatar(null); }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              {selectedAvatar?.avatar_name || "Avatar"} — {selectedAvatar?.mentor_name}
              {selectedAvatar && (
                <Badge
                  variant={selectedAvatar.status === "ready" ? "default" : "outline"}
                  className={selectedAvatar.status === "ready" ? "bg-green-500 ml-2" : "ml-2"}
                >
                  {selectedAvatar.status}
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>

          {selectedAvatar && (
            <Tabs value={detailTab} onValueChange={setDetailTab}>
              <TabsList className="w-full">
                <TabsTrigger value="overview" className="flex-1">Overview</TabsTrigger>
                <TabsTrigger value="knowledge" className="flex-1">
                  <BookOpen className="h-4 w-4 mr-1.5" />
                  Knowledge Base
                </TabsTrigger>
                <TabsTrigger value="test" className="flex-1" disabled={selectedAvatar.status !== "ready"}>
                  <MessageSquare className="h-4 w-4 mr-1.5" />
                  Test Chat
                </TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="mt-4 space-y-4">
                {selectedAvatar.status === "disabled" && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      This avatar is disabled. Learners cannot chat with it. Enable it to make it available.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "Conversations", value: Number(selectedAvatar.total_conversations), icon: <MessageSquare className="h-4 w-4 text-blue-500" /> },
                    { label: "Messages", value: Number(selectedAvatar.total_user_messages), icon: <MessageSquare className="h-4 w-4 text-purple-500" /> },
                    { label: "Unique Users", value: Number(selectedAvatar.unique_users), icon: <Users className="h-4 w-4 text-green-500" /> },
                    { label: "Tokens Used", value: Number(selectedAvatar.total_tokens_used).toLocaleString(), icon: <Zap className="h-4 w-4 text-yellow-500" /> },
                  ].map(stat => (
                    <Card key={stat.label}>
                      <CardContent className="p-3 text-center">
                        <div className="flex justify-center mb-1">{stat.icon}</div>
                        <div className="text-xl font-bold">{stat.value}</div>
                        <p className="text-xs text-muted-foreground">{stat.label}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline" size="sm"
                    disabled={retrainingId === selectedAvatar.avatar_id}
                    onClick={() => handleRetrain(selectedAvatar)}
                  >
                    <RefreshCw className={`h-4 w-4 mr-2 ${retrainingId === selectedAvatar.avatar_id ? "animate-spin" : ""}`} />
                    {retrainingId === selectedAvatar.avatar_id ? "Retraining..." : "Retrain Avatar"}
                  </Button>
                  <Button
                    variant={selectedAvatar.status === "ready" ? "destructive" : "default"}
                    size="sm"
                    onClick={() => handleToggleStatus(selectedAvatar)}
                  >
                    {selectedAvatar.status === "ready"
                      ? <><EyeOff className="h-4 w-4 mr-2" />Disable Avatar</>
                      : <><Eye className="h-4 w-4 mr-2" />Enable Avatar</>
                    }
                  </Button>
                </div>

                <div className="text-xs text-muted-foreground space-y-1">
                  {selectedAvatar.last_trained_at && (
                    <p>Last trained: {new Date(selectedAvatar.last_trained_at).toLocaleString()}</p>
                  )}
                  {selectedAvatar.last_conversation_at && (
                    <p>Last conversation: {new Date(selectedAvatar.last_conversation_at).toLocaleString()}</p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="knowledge" className="mt-4">
                <KnowledgeBaseManager
                  mentorId={selectedAvatar.mentor_id}
                  avatarId={selectedAvatar.avatar_id}
                  onRetrain={() => handleRetrain(selectedAvatar)}
                />
              </TabsContent>

              <TabsContent value="test" className="mt-4">
                {selectedAvatar.status === "ready" ? (
                  <AvatarChatInterface
                    avatarId={selectedAvatar.avatar_id}
                    mentorName={selectedAvatar.mentor_name}
                    avatarName={selectedAvatar.avatar_name}
                  />
                ) : (
                  <div className="py-8 text-center text-muted-foreground">
                    Avatar must be in "ready" status to test chat.
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
