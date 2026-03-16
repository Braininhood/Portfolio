import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Send, Bot, User, Loader2, Calendar, Video, BookOpen, Lock, Volume2, Square, Type } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  streaming?: boolean;
}

interface AvatarChatInterfaceProps {
  avatarId: string;
  mentorId?: string;
  mentorName?: string;
  avatarName?: string;
  onBookingClick?: () => void;
  /** When true, card fills parent height (for page layout with internal scroll only) */
  fillContainer?: boolean;
}

export const AvatarChatInterface = ({ avatarId, mentorId, mentorName, onBookingClick, fillContainer }: AvatarChatInterfaceProps) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [avatar, setAvatar] = useState<any>(null);
  const [mentor, setMentor] = useState<any>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [responseMode, setResponseMode] = useState<"text" | "voice" | "both">("both");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const hasInitiallyScrolled = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasSetInitialVoice = useRef(false);
  // Web Speech API: load voices (may be async in Chrome)
  useEffect(() => {
    const loadVoices = () => {
      const list = window.speechSynthesis.getVoices();
      setVoices(list);
      if (list.length > 0 && !hasSetInitialVoice.current) {
        hasSetInitialVoice.current = true;
        const defaultVoice = list.find((v) => v.default) || list.find((v) => v.lang.startsWith("en")) || list[0];
        setSelectedVoice(defaultVoice);
      }
    };
    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const speak = (text: string, messageId: string) => {
    if (!text.trim() || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    if (selectedVoice) utterance.voice = selectedVoice;
    utterance.onend = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);
    setSpeakingMessageId(messageId);
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setSpeakingMessageId(null);
  };

  useEffect(() => {
    checkAuthAndRole();
    fetchAvatarData();
  }, [avatarId]);

  const checkAuthAndRole = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    setCurrentUser(user);
    if (user) {
      const { data: rolesData } = await supabase
        .from("user_roles")
        .select("role")
        .eq("user_id", user.id);
      const roles = (rolesData ?? []).map((r) => r.role);
      const isAdmin = roles.includes("admin");
      const isMentor = roles.includes("mentor");
      setUserRole(isAdmin ? "admin" : isMentor ? "mentor" : "learner");
      // Learners and admins can chat; mentors (who are not admin) cannot
      if (!isMentor || isAdmin) {
        initializeConversation(user.id);
      }
    }
    setAuthChecked(true);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    const container = messagesContainerRef.current;
    if (!container || !messagesEndRef.current) return;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
    // Scroll on first load with messages, or when user is already near bottom
    if (!hasInitiallyScrolled.current && messages.length > 0) {
      hasInitiallyScrolled.current = true;
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    } else if (isNearBottom) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  const fetchAvatarData = async () => {
    const { data: avatarData } = await supabase
      .from("mentor_avatars")
      .select("*, mentor_profiles(*)")
      .eq("id", avatarId)
      .single();

    if (avatarData) {
      setAvatar(avatarData);
      setMentor(avatarData.mentor_profiles);
    }
  };

  const initializeConversation = async (userId: string) => {
    const { data: existingConv } = await supabase
      .from("avatar_conversations")
      .select("id")
      .eq("user_id", userId)
      .eq("avatar_id", avatarId)
      .maybeSingle();

    if (existingConv) {
      setConversationId(existingConv.id);
      loadMessages(existingConv.id);
    } else {
      const { data: newConv, error } = await supabase
        .from("avatar_conversations")
        .insert({ user_id: userId, avatar_id: avatarId })
        .select()
        .single();

      if (error) {
        console.error("Error creating conversation:", error);
        toast.error("Failed to start conversation");
      } else {
        setConversationId(newConv.id);
        sendWelcomeMessage(newConv.id);
      }
    }
  };

  const loadMessages = async (convId: string) => {
    const { data, error } = await supabase
      .from("avatar_messages")
      .select("*")
      .eq("conversation_id", convId)
      .order("created_at", { ascending: true });

    if (!error && data) {
      setMessages(data.map((msg) => ({
        id: msg.id,
        role: msg.role as "user" | "assistant",
        content: msg.content,
        created_at: msg.created_at,
      })));
    }
  };

  const sendWelcomeMessage = async (convId: string) => {
    const welcomeContent = `Hi! I'm ${avatar?.avatar_name || "your AI assistant"}. I'm here to help answer your questions. What would you like to know?`;

    const { data } = await supabase
      .from("avatar_messages")
      .insert({ conversation_id: convId, role: "assistant", content: welcomeContent })
      .select()
      .single();

    if (data) {
      setMessages([{ id: data.id, role: "assistant", content: data.content, created_at: data.created_at }]);
      if (responseMode === "voice" && data.content && "speechSynthesis" in window) {
        setTimeout(() => speak(data.content, data.id), 100);
      }
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setIsLoading(true);

    // Add user message to UI immediately
    const tempUserId = `temp-user-${Date.now()}`;
    const tempAssistantId = `temp-assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: tempUserId, role: "user", content: userMessage, created_at: new Date().toISOString() },
      { id: tempAssistantId, role: "assistant", content: "", created_at: new Date().toISOString(), streaming: true },
    ]);

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;
      if (!accessToken) throw new Error("Not authenticated");

      const supabaseUrl = (supabase as any).supabaseUrl as string;
      const response = await fetch(
        `${supabaseUrl}/functions/v1/chat-with-avatar-stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ avatarId, conversationId, message: userMessage }),
        }
      );

      if (!response.ok) {
        const err = await response.json().catch(() => ({ error: "Unknown error" }));
        if (response.status === 429) {
          // Remove streaming placeholders
          setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId && m.id !== tempUserId));
          // Show limit message as assistant bubble
          setMessages((prev) => [
            ...prev,
            {
              id: `limit-${Date.now()}`,
              role: "assistant",
              content: err.message || "You've reached the message limit for this avatar. Book a session with the mentor for personalized help.",
              created_at: new Date().toISOString(),
            },
          ]);
          return;
        }
        throw new Error(err.error || `HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let streamedConvId = conversationId;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const parsed = JSON.parse(line.slice(6));

            if (parsed.type === "start" && parsed.conversationId) {
              streamedConvId = parsed.conversationId;
              setConversationId(parsed.conversationId);
            } else if (parsed.type === "delta" && parsed.content) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === tempAssistantId
                    ? { ...m, content: m.content + parsed.content }
                    : m
                )
              );
            } else if (parsed.type === "done") {
              // Mark streaming complete
              setMessages((prev) => {
                const updated = prev.map((m) =>
                  m.id === tempAssistantId ? { ...m, streaming: false } : m
                );
                const msg = updated.find((m) => m.id === tempAssistantId);
                if (msg?.content && responseMode === "voice") {
                  setTimeout(() => speak(msg.content, tempAssistantId), 50);
                }
                return updated;
              });
              // Reload messages from DB to get real IDs
              if (streamedConvId) {
                setTimeout(() => loadMessages(streamedConvId!), 300);
              }
            }
          } catch {
            // skip malformed
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
      // Remove the streaming placeholder on error
      setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId && m.id !== tempUserId));
      toast.error("Failed to send message", {
        description: error instanceof Error ? error.message : "Please try again",
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Not logged in — show sign-in gate
  if (authChecked && !currentUser) {
    return (
      <Card className="flex flex-col h-[400px] items-center justify-center text-center p-8">
        <Lock className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="font-semibold text-lg mb-2">Sign in to chat</h3>
        <p className="text-sm text-muted-foreground mb-6 max-w-xs">
          Create a free account or sign in to chat with {mentorName || "this mentor"}'s AI avatar.
        </p>
        <div className="flex gap-3">
          <Button onClick={() => navigate(`/auth?redirect=${encodeURIComponent(window.location.pathname + window.location.hash)}`)}>
            Sign In
          </Button>
          <Button variant="outline" onClick={() => navigate(`/auth?mode=signup&redirect=${encodeURIComponent(window.location.pathname + window.location.hash)}`)}>
            Create Account
          </Button>
        </div>
      </Card>
    );
  }

  // Mentor role (and not admin) — cannot chat; admins can test any avatar
  if (authChecked && userRole === "mentor") {
    return (
      <Card className="flex flex-col h-[300px] items-center justify-center text-center p-8">
        <Bot className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="font-semibold text-lg mb-2">Avatar chat is for learners</h3>
        <p className="text-sm text-muted-foreground mb-4 max-w-xs">
          As a mentor, you can view and manage this avatar from your dashboard.
        </p>
        <Button variant="outline" onClick={() => navigate("/mentor/dashboard?tab=avatars")}>
          Go to Dashboard
        </Button>
      </Card>
    );
  }

  return (
    <Card className={cn("flex flex-col", fillContainer ? "h-full min-h-[400px]" : "h-[600px]")}>
      <CardHeader className="border-b py-3 px-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarImage src={avatar?.photo_urls?.[0] || mentor?.image_url} />
            <AvatarFallback><Bot size={18} /></AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{avatar?.avatar_name || "AI Assistant"}</CardTitle>
            <p className="text-xs text-muted-foreground truncate">{mentor?.name}</p>
          </div>
          <Badge variant="secondary" className="flex items-center gap-1 shrink-0">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            Online
          </Badge>
          <ToggleGroup
            type="single"
            value={responseMode}
            onValueChange={(v) => v && setResponseMode(v as "text" | "voice" | "both")}
            className="shrink-0 gap-0"
          >
            <ToggleGroupItem value="text" size="sm" className="text-xs px-2 h-7" title="Text only">
              <Type size={12} />
            </ToggleGroupItem>
            <ToggleGroupItem value="voice" size="sm" className="text-xs px-2 h-7" title="Voice (auto-play)">
              <Volume2 size={12} />
            </ToggleGroupItem>
            <ToggleGroupItem value="both" size="sm" className="text-xs px-2 h-7" title="Text and voice">
              <Type size={12} className="mr-0.5" />
              <Volume2 size={12} />
            </ToggleGroupItem>
          </ToggleGroup>
          {voices.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" title="Voice settings">
                  <Volume2 size={16} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="max-h-[300px] overflow-y-auto w-56">
                {(voices.filter((v) => v.lang.startsWith("en")).length > 0
                  ? voices.filter((v) => v.lang.startsWith("en"))
                  : voices.slice(0, 12)
                ).map((v) => (
                  <DropdownMenuItem
                    key={v.name + v.lang}
                    onClick={() => setSelectedVoice(v)}
                    className={selectedVoice?.name === v.name ? "bg-accent" : ""}
                  >
                    {v.name} ({v.lang})
                  </DropdownMenuItem>
                ))}
                {voices.filter((v) => v.lang.startsWith("en")).length > 0 &&
                  voices.filter((v) => !v.lang.startsWith("en")).length > 0 && (
                  <>
                    <div className="px-2 py-1.5 text-xs text-muted-foreground border-t mt-1 pt-1">Other languages</div>
                    {voices.filter((v) => !v.lang.startsWith("en")).slice(0, 8).map((v) => (
                      <DropdownMenuItem
                        key={v.name + v.lang}
                        onClick={() => setSelectedVoice(v)}
                        className={selectedVoice?.name === v.name ? "bg-accent" : ""}
                      >
                        {v.name} ({v.lang})
                      </DropdownMenuItem>
                    ))}
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </CardHeader>

      <CardContent ref={messagesContainerRef} className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-4 space-y-4 scrollbar-chat">
        {messages.map((message, index) => (
          <div
            key={message.id || index}
            className={`flex items-start gap-2.5 ${message.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <Avatar className="h-7 w-7 flex-shrink-0 mt-0.5">
              {message.role === "user" ? (
                <AvatarFallback><User size={14} /></AvatarFallback>
              ) : (
                <>
                  <AvatarImage src={avatar?.photo_urls?.[0]} />
                  <AvatarFallback><Bot size={14} /></AvatarFallback>
                </>
              )}
            </Avatar>
            <div
              className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground rounded-tr-sm"
                  : "bg-muted rounded-tl-sm"
              }`}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  {message.content ? (
                    <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  ) : (
                    <span className="flex gap-1 items-center py-0.5">
                      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:0ms]" />
                      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:150ms]" />
                      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:300ms]" />
                    </span>
                  )}
                  {message.streaming && message.content && (
                    <span className="inline-block w-0.5 h-3.5 bg-current ml-0.5 animate-pulse align-middle" />
                  )}
                </div>
                {message.role === "assistant" && message.content && !message.streaming && "speechSynthesis" in window && (responseMode === "voice" || responseMode === "both") && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 text-muted-foreground hover:text-foreground"
                    onClick={() =>
                      speakingMessageId === (message.id || String(index))
                        ? stopSpeaking()
                        : speak(message.content, message.id || String(index))
                    }
                    title={speakingMessageId === (message.id || String(index)) ? "Stop" : "Listen"}
                  >
                    {speakingMessageId === (message.id || String(index)) ? (
                      <Square size={14} fill="currentColor" />
                    ) : (
                      <Volume2 size={14} />
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </CardContent>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t bg-muted/30 flex gap-2 flex-wrap">
        <Button variant="outline" size="sm" onClick={onBookingClick ?? (() => mentorId && navigate(`/mentors/${mentorId}#booking`))} className="text-xs h-7">
          <Calendar size={12} className="mr-1" />
          Book Session
        </Button>
        <Button variant="outline" size="sm" onClick={() => mentorId && navigate(`/learner/my-questions?mentor=${mentorId}`)} className="text-xs h-7">
          <Video size={12} className="mr-1" />
          Video Answers
        </Button>
        {mentorId && (
          <Button variant="outline" size="sm" onClick={() => navigate(`/mentors/${mentorId}`)} className="text-xs h-7">
            <BookOpen size={12} className="mr-1" />
            View Profile
          </Button>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            disabled={isLoading}
            className="text-sm"
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()} size="icon">
            {isLoading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
          </Button>
        </div>
      </div>
    </Card>
  );
};
