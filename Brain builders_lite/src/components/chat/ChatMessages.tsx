import { useEffect, useRef } from "react";
import { ChatBubble } from "./ChatBubble";
import { Loader2 } from "lucide-react";
import type { ChatMessage } from "@/hooks/useChat";

interface ChatMessagesProps {
  messages: ChatMessage[];
  currentUserId: string;
  loading: boolean;
}

export function ChatMessages({ messages, currentUserId, loading }: ChatMessagesProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground px-4 text-center">
        <div>
          <p className="text-lg font-medium mb-1">No messages yet</p>
          <p className="text-sm">Send a message to start the conversation!</p>
        </div>
      </div>
    );
  }

  // Group messages by date
  const groupedMessages: { date: string; messages: ChatMessage[] }[] = [];

  messages.forEach((msg) => {
    const date = new Date(msg.created_at).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    const lastGroup = groupedMessages[groupedMessages.length - 1];

    if (lastGroup && lastGroup.date === date) {
      lastGroup.messages.push(msg);
    } else {
      groupedMessages.push({ date, messages: [msg] });
    }
  });

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-6">
      {groupedMessages.map((group, groupIndex) => (
        <div key={groupIndex}>
          <div className="flex justify-center mb-4">
            <span className="text-xs text-muted-foreground bg-muted/80 px-3 py-1.5 rounded-full">
              {group.date}
            </span>
          </div>

          <div className="space-y-3">
            {group.messages.map((message) => (
              <ChatBubble
                key={message.id}
                message={message}
                isOwn={message.sender_id === currentUserId}
              />
            ))}
          </div>
        </div>
      ))}

      <div ref={endRef} />
    </div>
  );
}
