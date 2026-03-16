import { useState, useEffect, useCallback, useRef } from "react";
import { supabase } from "@/integrations/supabase/client";
import { User } from "@supabase/supabase-js";

const POLL_INTERVAL_MS = 25000;

export function useUnreadMessages(user: User | null) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchUnreadCount = useCallback(async () => {
    if (!user) {
      setUnreadCount(0);
      setLoading(false);
      return;
    }

    try {
      // First, get all conversations where user is either the student or mentor
      const { data: mentorProfile } = await supabase
        .from("mentor_profiles")
        .select("id")
        .eq("user_id", user.id)
        .maybeSingle();

      // Build query for conversations
      let conversationIds: string[] = [];

      // Get conversations where user is the student
      const { data: studentConvs } = await supabase
        .from("conversations")
        .select("id")
        .eq("user_id", user.id)
        .eq("archived", false);

      if (studentConvs) {
        conversationIds = [...conversationIds, ...studentConvs.map(c => c.id)];
      }

      // Get conversations where user is the mentor
      if (mentorProfile) {
        const { data: mentorConvs } = await supabase
          .from("conversations")
          .select("id")
          .eq("mentor_id", mentorProfile.id)
          .eq("archived", false);

        if (mentorConvs) {
          conversationIds = [...conversationIds, ...mentorConvs.map(c => c.id)];
        }
      }

      // Exclude soft-deleted conversations unless there's a new message since delete (match ConversationsList logic)
      const { data: deletedRows } = await supabase
        .from("conversation_deletions")
        .select("conversation_id, deleted_at")
        .eq("user_id", user.id);
      const deletedMap = new Map(
        (deletedRows ?? []).map((r) => [r.conversation_id, r.deleted_at] as [string, string])
      );
      if (deletedMap.size > 0) {
        const { data: convsWithLastMessage } = await supabase
          .from("conversations")
          .select("id, last_message_at")
          .in("id", conversationIds);
        const restoredIds = new Set(
          (convsWithLastMessage ?? [])
            .filter(
              (c) =>
                c.last_message_at &&
                deletedMap.has(c.id) &&
                new Date(c.last_message_at) > new Date(deletedMap.get(c.id)!)
            )
            .map((c) => c.id)
        );
        conversationIds = conversationIds.filter(
          (id) => !deletedMap.has(id) || restoredIds.has(id)
        );
      }

      if (conversationIds.length === 0) {
        setUnreadCount(0);
        setLoading(false);
        return;
      }

      // Get unread messages count across all conversations
      const { count, error } = await supabase
        .from("messages")
        .select("*", { count: "exact", head: true })
        .in("conversation_id", conversationIds)
        .eq("is_read", false)
        .neq("sender_id", user.id);

      if (error) {
        console.error("[UnreadMessages] Error fetching count:", error);
      } else {
        setUnreadCount(count || 0);
      }
    } catch (err) {
      console.error("[UnreadMessages] Error:", err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Set up real-time subscription (delayed so WebSocket isn't opened during page load)
  useEffect(() => {
    if (!user) return;

    fetchUnreadCount();

    if (channelRef.current) {
      supabase.removeChannel(channelRef.current);
      channelRef.current = null;
    }

    const timer = window.setTimeout(() => {
      const channelName = `unread-messages-${user.id}-${Date.now()}`;
      const channel = supabase
        .channel(channelName)
        .on(
          "postgres_changes",
          {
            event: "INSERT",
            schema: "public",
            table: "messages",
          },
          (payload) => {
            const newMsg = payload.new as { sender_id: string; is_read: boolean };
            if (newMsg.sender_id !== user.id && !newMsg.is_read) {
              setUnreadCount((prev) => prev + 1);
            }
          }
        )
        .on(
          "postgres_changes",
          {
            event: "UPDATE",
            schema: "public",
            table: "messages",
          },
          (payload) => {
            const oldMsg = payload.old as { is_read: boolean; sender_id: string };
            const newMsg = payload.new as { is_read: boolean; sender_id: string };
            if (!oldMsg.is_read && newMsg.is_read && newMsg.sender_id !== user.id) {
              setUnreadCount((prev) => Math.max(0, prev - 1));
            }
          }
        )
        .subscribe((status) => {
          if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
            if (channelRef.current === channel) {
              supabase.removeChannel(channel).then(() => {});
              channelRef.current = null;
            }
            if (!pollIntervalRef.current) {
              pollIntervalRef.current = setInterval(fetchUnreadCount, POLL_INTERVAL_MS);
            }
          }
        });

      channelRef.current = channel;
    }, 1500);

    return () => {
      window.clearTimeout(timer);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current);
        channelRef.current = null;
      }
    };
  }, [user, fetchUnreadCount]);

  // Refresh on tab visibility change
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        fetchUnreadCount();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [fetchUnreadCount]);

  return { unreadCount, loading, refresh: fetchUnreadCount };
}
