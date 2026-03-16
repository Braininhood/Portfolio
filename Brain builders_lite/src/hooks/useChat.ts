import { useState, useEffect, useCallback, useRef } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { User } from "@supabase/supabase-js";
import { logger } from "@/utils/logger";
import { messageSchema, validateData } from "@/utils/validation";
import { rateLimiter, rateLimits, formatWaitTime } from "@/utils/rateLimit";

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  created_at: string;
  is_read: boolean;
  read_at: string | null;
  delivered_at: string | null;
  file_url: string | null;
  file_name: string | null;
  file_type: string | null;
}

export interface ChatConversation {
  id: string;
  user_id: string;
  mentor_id: string;
  mentor_name: string;
  last_message_at: string | null;
  archived: boolean;
  claimed_by_admin_id: string | null;
  participant_name: string; // Display name for other participant
}

interface UseChatReturn {
  messages: ChatMessage[];
  conversation: ChatConversation | null;
  loading: boolean;
  sending: boolean;
  connectionStatus: "connected" | "connecting" | "disconnected";
  sendMessage: (content: string) => Promise<boolean>;
  refreshMessages: () => Promise<void>;
}

export function useChat(conversationId: string | undefined, user: User | null): UseChatReturn {
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "connecting" | "disconnected">("connecting");

  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);
  const processedMessageIds = useRef<Set<string>>(new Set());
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const backgroundPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const CHAT_POLL_MS = 8000;
  const BACKGROUND_POLL_MS = 5000; // Fallback: poll every 5s so recipient gets admin messages even if realtime fails

  // Load conversation details
  const loadConversation = useCallback(async () => {
    if (!conversationId || !user) return;

    logger.debug("Loading conversation", { conversationId });

    const { data, error } = await supabase
      .from("conversations")
      .select("*")
      .eq("id", conversationId)
      .maybeSingle();

    if (error) {
      logger.warn("Error loading conversation", { error: error?.message ?? error, conversationId });
      toast({
        title: "Error",
        description: "Failed to load conversation",
        variant: "destructive",
      });
      return;
    }

    if (!data) {
      logger.error("Conversation not found", undefined, { conversationId });
      return;
    }

    // Check if current user is the mentor by looking up mentor_profiles
    const { data: mentorProfile } = await supabase
      .from("mentor_profiles")
      .select("user_id")
      .eq("id", data.mentor_id)
      .maybeSingle();

    const isMentor = mentorProfile?.user_id === user.id;

    // Check if this conversation is with support (admin) via RPC — learners can't read user_roles for others
    const { data: supportRows } = await supabase.rpc("get_support_mentor_profile");
    const supportMentorId = supportRows?.[0]?.id;
    const isSupport = !!supportMentorId && data.mentor_id === supportMentorId;

    // Determine the other participant's name; show "Support" for admin/support chat
    let participantName = isSupport ? "Support" : data.mentor_name;
    if (isMentor && !isSupport) {
      const { data: profileData } = await supabase
        .from("profiles")
        .select("full_name")
        .eq("id", data.user_id)
        .maybeSingle();
      participantName = profileData?.full_name || "User";
    }

    setConversation({
      ...data,
      participant_name: participantName,
    });
  }, [conversationId, user, toast]);

  // Load messages
  const loadMessages = useCallback(async () => {
    if (!conversationId) return;

    logger.debug("Loading messages", { conversationId });

    const { data, error } = await supabase
      .from("messages")
      .select("*")
      .eq("conversation_id", conversationId)
      .order("created_at", { ascending: true });

    if (error) {
      logger.warn("Error loading messages", { error: error?.message ?? error, conversationId });
      toast({
        title: "Error",
        description: "Failed to load messages",
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    logger.debug("Messages loaded", { conversationId, count: data?.length || 0 });

    // Update processed IDs
    processedMessageIds.current = new Set((data || []).map((m) => m.id));
    setMessages(data || []);
    setLoading(false);
  }, [conversationId, toast]);

  // Mark messages as read (recipient marks sender's messages as read when viewing)
  const markAsRead = useCallback(async () => {
    if (!conversationId || !user) return;

    const { error } = await supabase
      .from("messages")
      .update({
        is_read: true,
        read_at: new Date().toISOString(),
        delivered_at: new Date().toISOString(),
      })
      .eq("conversation_id", conversationId)
      .neq("sender_id", user.id)
      .eq("is_read", false);

    if (error) {
      logger.warn("Error marking messages as read", { error: error?.message ?? error, conversationId });
    }
  }, [conversationId, user]);

  // Send message
  const sendMessage = useCallback(
    async (content: string): Promise<boolean> => {
      if (!content.trim() || !user || !conversationId || !conversation) {
        return false;
      }

      // ✅ PRIORITY 2: Rate limiting for messages (prevent spam)
      // Check per-minute limit
      const minuteLimit = rateLimiter.check(rateLimits.messageSend);
      if (!minuteLimit.allowed) {
        const waitTime = formatWaitTime(minuteLimit.waitMs);
        toast({
          title: "Sending too fast",
          description: `Please wait ${waitTime}. You can send up to ${rateLimits.messageSend.maxRequests} messages per minute.`,
          variant: "destructive",
        });
        return false;
      }

      // Check hourly limit
      const hourlyLimit = rateLimiter.check(rateLimits.messageSendHourly);
      if (!hourlyLimit.allowed) {
        const waitTime = formatWaitTime(hourlyLimit.waitMs);
        toast({
          title: "Message limit reached",
          description: `You've sent too many messages this hour. Please wait ${waitTime}.`,
          variant: "destructive",
        });
        return false;
      }

      setSending(true);
      logger.debug("Sending message", { conversationId });

        try {
          // Get mentor profile for THIS conversation (only needed to determine recipient for notifications)
          const { data: conversationMentor } = await supabase
            .from("mentor_profiles")
            .select("user_id")
            .eq("id", conversation.mentor_id)
            .maybeSingle();

          // User is the mentor ONLY if their user_id matches the mentor's user_id in this conversation
          const isMentorInThisConversation = conversationMentor?.user_id === user.id;

          // Unified identity: always use the single canonical name from the user's profile.
          // (Mentor vs user is a permission/context, not a separate identity.)
          const { data: profileData } = await supabase
            .from("profiles")
            .select("full_name")
            .eq("id", user.id)
            .maybeSingle();

          const senderName = profileData?.full_name || user.email?.split("@")[0] || "User";
          logger.debug("Sender identity resolved", { userId: user.id, senderName });

        // Validate message data
        const messageData = {
          conversation_id: conversationId,
          sender_id: user.id,
          sender_name: senderName,
          content: content.trim(),
        };
        
        const validation = validateData(messageSchema, messageData);
        if (!validation.success) {
          logger.warn("Message validation failed", { errors: validation.errors, conversationId });
          toast({
            title: "Invalid message",
            description: validation.errors[0],
            variant: "destructive",
          });
          setSending(false);
          return false;
        }

        // Insert message
        const { data: newMessage, error } = await supabase
          .from("messages")
          .insert(validation.data)
          .select()
          .single();

        if (error) {
          logger.error("Error sending message", error, { conversationId });
          toast({
            title: "Error",
            description: "Failed to send message",
            variant: "destructive",
          });
          setSending(false);
          return false;
        }

        logger.debug("Message sent successfully", { messageId: newMessage.id, conversationId });

        // Add to local state immediately
        if (!processedMessageIds.current.has(newMessage.id)) {
          processedMessageIds.current.add(newMessage.id);
          setMessages((prev) => [...prev, newMessage]);
        }

        // If this is an admin responding to a support conversation, claim it
        // Check if: 1) user is admin, 2) mentor_id is an admin mentor profile, 3) not yet claimed
        if (user?.id) {
          const { data: myRoles } = await supabase
            .from("user_roles")
            .select("role")
            .eq("user_id", user.id);
          const isUserAdmin = (myRoles ?? []).some((r) => r.role === "admin");

          if (isUserAdmin && conversation && !conversation.claimed_by_admin_id) {
            // Check if this is a support conversation (mentor_id is an admin mentor profile)
            const { data: supportRows } = await supabase.rpc("get_support_mentor_profile");
            const adminMentorIds = (supportRows ?? []).map((r: { id: string }) => r.id);
            
            if (adminMentorIds.includes(conversation.mentor_id)) {
              // This is a support conversation - claim it for this admin
              logger.info("Admin claiming support conversation", { conversationId, userId: user.id });
              await supabase
                .from("conversations")
                .update({ claimed_by_admin_id: user.id })
                .eq("id", conversationId);
            }
          }
        }

        // Update conversation timestamp
        await supabase
          .from("conversations")
          .update({ last_message_at: new Date().toISOString() })
          .eq("id", conversationId);

        // Send notification to recipient (fire-and-forget; don't block on 401/network)
        let recipientId: string;
        if (isMentorInThisConversation) {
          recipientId = conversation.user_id;
        } else {
          recipientId = conversationMentor?.user_id || conversation.mentor_id;
        }

        const { data: { session } } = await supabase.auth.getSession();
        supabase.functions
          .invoke("send-message-notification", {
            body: {
              messageId: newMessage.id,
              recipientId,
              senderName,
              messageContent: content.trim(),
            },
            headers:
              session?.access_token != null
                ? { Authorization: `Bearer ${session.access_token}` }
                : undefined,
          })
          .catch((err) => logger.warn("Notification error (non-blocking)", { error: err?.message ?? err, messageId: newMessage.id }));

        setSending(false);
        return true;
      } catch (err) {
        logger.error("Error in sendMessage", err instanceof Error ? err : new Error(String(err)), { conversationId });
        toast({
          title: "Error",
          description: "Failed to send message",
          variant: "destructive",
        });
        setSending(false);
        return false;
      }
    },
    [conversationId, conversation, user, toast]
  );

  // Refresh messages
  const refreshMessages = useCallback(async () => {
    await loadMessages();
    await markAsRead();
  }, [loadMessages, markAsRead]);

  // Set up real-time subscription
  useEffect(() => {
    if (!conversationId || !user) return;

    // Clean up existing channel
    if (channelRef.current) {
      supabase.removeChannel(channelRef.current);
    }

    const channelName = `chat-${conversationId}-${user.id}-${Date.now()}`;

    const channel = supabase
      .channel(channelName)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `conversation_id=eq.${conversationId}`,
        },
        (payload) => {
          const newMsg = payload.new as ChatMessage;
          // Deduplicate
          if (!processedMessageIds.current.has(newMsg.id)) {
            processedMessageIds.current.add(newMsg.id);
            setMessages((prev) => [...prev, newMsg]);

            // Mark as read if from other user and tab is visible
            if (newMsg.sender_id !== user.id && document.visibilityState === "visible") {
              supabase
                .from("messages")
                .update({
                  is_read: true,
                  read_at: new Date().toISOString(),
                  delivered_at: new Date().toISOString(),
                })
                .eq("id", newMsg.id)
                .then(() => {});
            }
          }
        }
      )
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "messages",
          filter: `conversation_id=eq.${conversationId}`,
        },
        (payload) => {
          const updatedMsg = payload.new as ChatMessage;
          setMessages((prev) =>
            prev.map((msg) => (msg.id === updatedMsg.id ? updatedMsg : msg))
          );
        }
      )
      .subscribe((status) => {
        if (status === "SUBSCRIBED") {
          setConnectionStatus("connected");
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } else if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
          setConnectionStatus("disconnected");
          if (channelRef.current === channel) {
            supabase.removeChannel(channel).then(() => {});
            channelRef.current = null;
          }
          setTimeout(loadMessages, 3000);
          if (!pollIntervalRef.current) {
            pollIntervalRef.current = setInterval(loadMessages, CHAT_POLL_MS);
          }
        } else {
          setConnectionStatus("connecting");
        }
      });

    channelRef.current = channel;

    // Background polling: ensure recipient gets new messages (e.g. from admin) even if realtime is flaky
    if (backgroundPollRef.current) clearInterval(backgroundPollRef.current);
    backgroundPollRef.current = setInterval(() => {
      if (document.visibilityState === "visible") loadMessages();
    }, BACKGROUND_POLL_MS);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (backgroundPollRef.current) {
        clearInterval(backgroundPollRef.current);
        backgroundPollRef.current = null;
      }
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current);
        channelRef.current = null;
      }
    };
  }, [conversationId, user, loadMessages]);

  // Initial load: load conversation + messages, mark as read, then refetch so UI shows read state
  useEffect(() => {
    if (!conversationId || !user) return;

    let cancelled = false;
    const run = async () => {
      loadConversation();
      await loadMessages();
      await markAsRead();
      if (!cancelled) await loadMessages(); // Refetch so UI shows read receipts
    };
    run();
    return () => { cancelled = true; };
  }, [conversationId, user, loadConversation, loadMessages, markAsRead]);

  // Reload on tab visibility change and mark as read when user returns to tab
  useEffect(() => {
    const handleVisibility = async () => {
      if (document.visibilityState === "visible" && conversationId) {
        logger.debug("Tab visible, refreshing messages", { conversationId });
        await markAsRead();
        await loadMessages();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [conversationId, loadMessages, markAsRead]);

  return {
    messages,
    conversation,
    loading,
    sending,
    connectionStatus,
    sendMessage,
    refreshMessages,
  };
}
