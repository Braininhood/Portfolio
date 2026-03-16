import { Check, CheckCheck } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/hooks/useChat";

interface ChatBubbleProps {
  message: ChatMessage;
  isOwn: boolean;
}

export function ChatBubble({ message, isOwn }: ChatBubbleProps) {
  const formattedTime = format(new Date(message.created_at), "HH:mm");
  const isUnread = !isOwn && !message.is_read;

  return (
    <div className={cn("flex", isOwn ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] sm:max-w-[70%] rounded-2xl px-4 py-2.5 shadow-sm relative",
          isOwn
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md",
          isUnread && "ring-2 ring-primary/50 ring-offset-1 ring-offset-background"
        )}
      >
        {/* Unread indicator dot */}
        {isUnread && (
          <span className="absolute -left-1 -top-1 h-2.5 w-2.5 rounded-full bg-primary animate-pulse" />
        )}

        {!isOwn && (
          <p className="text-xs font-medium mb-1 opacity-70">
            {message.sender_name}
          </p>
        )}

        <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
        </p>

        {message.file_url && (
          <a
            href={message.file_url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "text-xs underline mt-2 block",
              isOwn ? "text-primary-foreground/80" : "text-foreground/80"
            )}
          >
            📎 {message.file_name || "Attachment"}
          </a>
        )}

        <div
          className={cn(
            "flex items-center gap-1.5 mt-1.5",
            isOwn ? "justify-end" : "justify-start"
          )}
        >
          <span className="text-[10px] opacity-60">{formattedTime}</span>

          {isOwn && (
            <span className="opacity-60">
              {message.is_read ? (
                <CheckCheck className="h-3.5 w-3.5 text-blue-400" />
              ) : message.delivered_at ? (
                <CheckCheck className="h-3.5 w-3.5" />
              ) : (
                <Check className="h-3.5 w-3.5" />
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
