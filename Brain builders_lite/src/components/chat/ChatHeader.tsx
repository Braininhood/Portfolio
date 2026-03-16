import { ArrowLeft, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import type { ChatConversation } from "@/hooks/useChat";

interface ChatHeaderProps {
  conversation: ChatConversation | null;
  connectionStatus: "connected" | "connecting" | "disconnected";
  onRefresh: () => void;
}

export function ChatHeader({ conversation, onRefresh }: ChatHeaderProps) {
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-3 p-3 sm:p-4 border-b bg-background">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => navigate(-1)}
        className="shrink-0"
      >
        <ArrowLeft className="h-5 w-5" />
      </Button>

      <div className="flex-1 min-w-0">
        <h2 className="font-semibold truncate">
          {conversation?.participant_name || "Loading..."}
        </h2>
      </div>

      <Button
        variant="ghost"
        size="icon"
        onClick={onRefresh}
        className="shrink-0"
      >
        <RefreshCw className="h-4 w-4" />
      </Button>
    </div>
  );
}
