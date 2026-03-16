import { useState, useRef, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (content: string) => Promise<boolean>;
  sending: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, sending, disabled }: ChatInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    if (!content.trim() || sending || disabled) return;

    const messageToSend = content;
    setContent(""); // Clear immediately for better UX

    const success = await onSend(messageToSend);

    if (!success) {
      // Restore content if send failed
      setContent(messageToSend);
    }

    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-2 p-3 sm:p-4 border-t bg-background">
      <Textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message..."
        disabled={sending || disabled}
        className="min-h-[44px] max-h-[120px] resize-none text-base"
        rows={1}
      />

      <Button
        onClick={handleSend}
        disabled={!content.trim() || sending || disabled}
        size="icon"
        className="h-11 w-11 shrink-0"
      >
        {sending ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <Send className="h-5 w-5" />
        )}
      </Button>
    </div>
  );
}
