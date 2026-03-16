import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { User } from "@supabase/supabase-js";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ChatInput } from "@/components/chat/ChatInput";
import { useChat } from "@/hooks/useChat";

export default function AdminMessagesChat() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setUser(session?.user ?? null));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) =>
      setUser(session?.user ?? null)
    );
    return () => subscription.unsubscribe();
  }, []);

  const {
    messages,
    conversation,
    loading,
    sending,
    sendMessage,
    refreshMessages,
  } = useChat(conversationId ?? undefined, user);

  if (!user) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[200px]">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center gap-2 p-4 border-b bg-card shrink-0">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/admin?tab=messages">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <span className="font-medium">Chat</span>
      </div>

      <div className="flex-1 flex flex-col min-h-0 p-4">
        <ChatHeader
          conversation={conversation}
          connectionStatus="connected"
          onRefresh={refreshMessages}
        />

        <ChatMessages
          messages={messages}
          currentUserId={user.id}
          loading={loading}
        />

        <ChatInput
          onSend={sendMessage}
          sending={sending}
          disabled={!conversation}
        />
      </div>
    </div>
  );
}
