import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageSquare, ArrowRight, Archive, ArchiveRestore, MoreVertical, Trash2, Loader2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useUserRole } from "@/hooks/useUserRole";
import { logger } from "@/utils/logger";

interface Conversation {
  id: string;
  user_id: string;
  mentor_id: string;
  mentor_name: string;
  last_message_at: string | null;
  unread_count: number;
  archived: boolean;
  archived_at: string | null;
  claimed_by_admin_id: string | null;
  display_name: string;
  is_mentor_view: boolean;
  is_support: boolean;
}

export const ConversationsList = ({ userId }: { userId: string }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"active" | "archived">("active");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [currentMentorProfile, setCurrentMentorProfile] = useState<{ id: string; name: string } | null>(null);
  const [adminMentorProfile, setAdminMentorProfile] = useState<{ id: string; name: string } | null>(null);
  const adminMentorProfileLoadingRef = useRef(false);

  const [newConversationOpen, setNewConversationOpen] = useState<"admin" | "mentor" | "learner" | false>(false);
  const [profilesLoading, setProfilesLoading] = useState(false);
  const [profiles, setProfiles] = useState<Array<{ id: string; full_name: string | null }>>([]);
  const [learnersForMentor, setLearnersForMentor] = useState<Array<{ id: string; full_name: string | null }>>([]);
  const [learnersLoading, setLearnersLoading] = useState(false);
  const [mentorsForLearner, setMentorsForLearner] = useState<Array<{ id: string; name: string }>>([]);
  const [mentorsForLearnerLoading, setMentorsForLearnerLoading] = useState(false);
  const [profileSearch, setProfileSearch] = useState("");
  const [mentorSearch, setMentorSearch] = useState("");

  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { isAdmin } = useUserRole();
  const messagesBasePath = isAdmin ? "/admin/messages" : "/learner/messages";

  const fetchConversations = async () => {
    if (!userId) return;
    
    setLoading(true);

    // Check if current user is admin
    const { data: myRoles } = await supabase
      .from("user_roles")
      .select("role")
      .eq("user_id", userId);
    const isUserAdmin = (myRoles ?? []).some((r) => r.role === "admin");

    // First, check if the current user is a mentor and get their mentor_profile id
    const { data: mentorProfile } = await supabase
      .from("mentor_profiles")
      .select("id, name")
      .eq("user_id", userId)
      .maybeSingle();

    const mentorProfileId = mentorProfile?.id;
    setCurrentMentorProfile(mentorProfileId ? { id: mentorProfileId, name: mentorProfile?.name || "Mentor" } : null);

    logger.debug("fetchConversations", { userId, mentorProfileId, hasMentorProfile: !!mentorProfileId, isUserAdmin });

    // Build the filter: user_id matches OR mentor_id matches (for mentors)
    let query = supabase
      .from("conversations")
      .select("*")
      .order("last_message_at", { ascending: false, nullsFirst: false });

    if (isUserAdmin) {
      // Admin: show conversations where they are the user, OR support conversations, OR where they are the mentor
      const { data: supportRows } = await supabase.rpc("get_support_mentor_profile");
      const allAdminMentorIds = (supportRows ?? []).map((r: { id: string }) => r.id).filter((id): id is string => Boolean(id));
      const orParts: string[] = [`user_id.eq.${userId}`];
      if (allAdminMentorIds.length > 0) {
        orParts.push(
          `and(mentor_id.in.(${allAdminMentorIds.join(",")}),claimed_by_admin_id.is.null)`,
          `and(mentor_id.in.(${allAdminMentorIds.join(",")}),claimed_by_admin_id.eq.${userId})`
        );
      }
      // If admin is also a mentor, show their regular mentor conversations (learners who messaged them)
      if (mentorProfileId) {
        orParts.push(`mentor_id.eq.${mentorProfileId}`);
      }
      query = query.or(orParts.join(","));
    } else if (mentorProfileId) {
      // User is a mentor (not admin) - show conversations where they are the student OR the mentor
      query = query.or(`user_id.eq.${userId},mentor_id.eq.${mentorProfileId}`);
    } else {
      // User is not a mentor - only show conversations where they are the student
      query = query.eq("user_id", userId);
    }

    const { data: conversationsData, error } = await query;

    if (error) {
      logger.error("Error fetching conversations", error, { userId });
      setLoading(false);
      return;
    }

    logger.debug("fetchConversations result", { count: conversationsData?.length });

    // Fetch deleted conversations for current user (soft delete) with deleted_at
    const { data: deletedConvs } = await supabase
      .from("conversation_deletions")
      .select("conversation_id, deleted_at")
      .eq("user_id", userId);

    const deletedMap = new Map<string, string>(
      (deletedConvs ?? []).map((d) => [d.conversation_id, d.deleted_at])
    );

    // Filter: hide only if user deleted it AND no new message since delete (restore when there is new activity)
    const activeConversations = (conversationsData || []).filter((conv) => {
      const deletedAt = deletedMap.get(conv.id);
      if (!deletedAt) return true;
      const lastAt = conv.last_message_at;
      if (!lastAt) return false;
      return new Date(lastAt) > new Date(deletedAt);
    });

    // Resolve support (admin) mentor id so we can show "Support" for those conversations (RPC works for learners)
    const { data: supportRows } = await supabase.rpc("get_support_mentor_profile");
    const adminMentorIds = new Set<string>(
      (supportRows ?? []).map((r: { id: string; name: string }) => r.id).filter((id): id is string => Boolean(id))
    );

    // Fetch unread counts and participant names
    const conversationsWithDetails = await Promise.all(
      activeConversations.map(async (conv) => {
        // Get unread count
        const { count } = await supabase
          .from("messages")
          .select("*", { count: "exact", head: true })
          .eq("conversation_id", conv.id)
          .eq("is_read", false)
          .neq("sender_id", userId);

        // Check if current user is the mentor by looking up mentor_profiles
        const { data: mentorProfile } = await supabase
          .from("mentor_profiles")
          .select("user_id")
          .eq("id", conv.mentor_id)
          .maybeSingle();

        const isMentorView = mentorProfile?.user_id === userId;
        const isSupport = adminMentorIds.has(conv.mentor_id);

        // Get display name for other participant
        // - If I'm viewing as mentor (admin or regular mentor), show the USER's name
        // - If I'm viewing as user, show "Support" for support chats, otherwise mentor name
        let displayName: string;
        if (isMentorView) {
          // I'm the mentor - show the user/learner's name
          const { data: profileData } = await supabase
            .from("profiles")
            .select("full_name")
            .eq("id", conv.user_id)
            .maybeSingle();
          displayName = profileData?.full_name || "User";
        } else {
          // I'm the user - show "Support" for support chats, otherwise mentor name
          displayName = isSupport ? "Support" : conv.mentor_name;
        }

        return {
          ...conv,
          unread_count: count || 0,
          display_name: displayName,
          is_mentor_view: isMentorView,
          is_support: isSupport,
        };
      })
    );

    setConversations(conversationsWithDetails);
    setLoading(false);
  };

  const createAdminMentorProfile = async (adminUserId: string): Promise<{ id: string; name: string } | null> => {
    try {
      const { data: profileData } = await supabase
        .from("profiles")
        .select("full_name")
        .eq("id", adminUserId)
        .maybeSingle();

      const adminName = profileData?.full_name || "Admin";

      const { data: created, error: createError } = await supabase
        .from("mentor_profiles")
        .insert({
          user_id: adminUserId,
          name: adminName,
          title: "Administrator",
          category: "Business",
          bio: "Platform administrator",
          full_bio: "Platform administrator",
          expertise: ["Administration"],
          languages: ["English"],
          availability: "Available",
          experience: "Platform administration",
          education: "N/A",
          certifications: [],
          price: 0,
          is_active: false, // Hidden from public mentor listings
        })
        .select("id, name")
        .single();

      if (createError) {
        logger.error("Error creating admin mentor profile", createError, { adminUserId });
        return null;
      }

      return { id: created.id, name: created.name };
    } catch (error) {
      logger.error("Error creating admin mentor profile", error instanceof Error ? error : new Error(String(error)), { adminUserId });
      return null;
    }
  };

  // Support = only user(s) with role ADMIN in DB (e.g. k.dommovoy). Used by "Message to support" for learners and mentors.
  const ensureAdminMentorLoaded = async (): Promise<{ id: string; name: string } | null> => {
    if (adminMentorProfile) return adminMentorProfile;
    if (adminMentorProfileLoadingRef.current) return null;
    adminMentorProfileLoadingRef.current = true;
    try {
      const { data: rpcRows, error: rpcError } = await supabase.rpc("get_support_mentor_profile");
      
      logger.debug("ensureAdminMentorLoaded RPC result", { rpcRows, rpcError, rowCount: rpcRows?.length });

      if (!rpcError && rpcRows && rpcRows.length > 0) {
        const row = rpcRows[0] as { id: string; name: string };
        const profile = { id: row.id, name: row.name || "Support" };
        logger.debug("Setting admin mentor profile from RPC", profile);
        setAdminMentorProfile(profile);
        return profile;
      }

      logger.warn("No support profile from RPC, checking if current user is admin", { userId });

      // Fallback: if current user is admin and no support profile exists yet, create own
      const { data: myRoles } = await supabase
        .from("user_roles")
        .select("role")
        .eq("user_id", userId);
      const isAdmin = (myRoles ?? []).some((r) => r.role === "admin");
      logger.debug("Current user admin check", { isAdmin, myRoles });
      
      if (isAdmin) {
        const profile = await createAdminMentorProfile(userId);
        if (profile) {
          logger.debug("Created new admin mentor profile", profile);
          setAdminMentorProfile(profile);
          return profile;
        }
      }

      logger.warn("No support mentor profile available");
      return null;
    } finally {
      adminMentorProfileLoadingRef.current = false;
    }
  };

  const openOrCreateConversation = async (targetUserId: string, mentorId: string, mentorName: string) => {
    if (!targetUserId || !mentorId) return;

    const { data: existing, error: existingError } = await supabase
      .from("conversations")
      .select("id")
      .eq("user_id", targetUserId)
      .eq("mentor_id", mentorId)
      .maybeSingle();

    if (existingError) {
      logger.error("Error checking existing conversation", existingError, { targetUserId, mentorId });
    }

    if (existing?.id) {
      navigate(`${messagesBasePath}/${existing.id}`);
      return;
    }

    const { data: created, error: createError } = await supabase
      .from("conversations")
      .insert({
        user_id: targetUserId,
        mentor_id: mentorId,
        mentor_name: mentorName,
      })
      .select("id")
      .single();

    if (createError) {
      logger.error("Error creating conversation", createError, { targetUserId, mentorId });
      toast({
        title: "Error",
        description: "Failed to start conversation",
        variant: "destructive",
      });
      return;
    }

    logger.debug("Conversation created", { conversationId: created.id, targetUserId, mentorId, mentorName });
    navigate(`${messagesBasePath}/${created.id}`);
  };

  // Message to support: for all users (learner or mentor) — opens conversation only with the user who has role ADMIN.
  const startConversationWithAdmin = async () => {
    const adminProfile = (await ensureAdminMentorLoaded()) || adminMentorProfile;
    if (!adminProfile) {
      toast({
        title: "Support chat not available yet",
        description: "Support needs to be set up. If you have an admin account, open Messages once to enable it.",
        variant: "destructive",
      });
      return;
    }
    logger.debug("startConversationWithAdmin", { userId, adminProfile });
    await openOrCreateConversation(userId, adminProfile.id, adminProfile.name);
  };

  const startConversationAsAdmin = async (targetUserId: string) => {
    // If admin doesn't have mentor profile, auto-create one
    if (!currentMentorProfile?.id) {
      const created = await createAdminMentorProfile(userId);
      if (!created) {
        toast({
          title: "Error",
          description: "Failed to set up admin chat profile. Please try again.",
          variant: "destructive",
        });
        return;
      }
      setCurrentMentorProfile(created);
      
      // Admin-initiated conversation: check existing first
      const { data: existing } = await supabase
        .from("conversations")
        .select("id")
        .eq("user_id", targetUserId)
        .eq("mentor_id", created.id)
        .maybeSingle();
      
      if (existing?.id) {
        navigate(`${messagesBasePath}/${existing.id}`);
        return;
      }
      
      // Create new and immediately claim it for this admin
      const { data: newConv, error: createError } = await supabase
        .from("conversations")
        .insert({
          user_id: targetUserId,
          mentor_id: created.id,
          mentor_name: created.name,
          claimed_by_admin_id: userId, // Immediately claim for this admin
        })
        .select("id")
        .single();
      
      if (createError) {
        logger.error("Error creating admin conversation", createError);
        toast({ title: "Error", description: "Failed to start conversation", variant: "destructive" });
        return;
      }
      
      logger.debug("Admin conversation created and claimed", { conversationId: newConv.id, claimedBy: userId });
      navigate(`${messagesBasePath}/${newConv.id}`);
    } else {
      // Check existing first
      const { data: existing } = await supabase
        .from("conversations")
        .select("id")
        .eq("user_id", targetUserId)
        .eq("mentor_id", currentMentorProfile.id)
        .maybeSingle();
      
      if (existing?.id) {
        navigate(`${messagesBasePath}/${existing.id}`);
        return;
      }
      
      // Create new and claim
      const { data: newConv, error: createError } = await supabase
        .from("conversations")
        .insert({
          user_id: targetUserId,
          mentor_id: currentMentorProfile.id,
          mentor_name: currentMentorProfile.name,
          claimed_by_admin_id: userId, // Immediately claim for this admin
        })
        .select("id")
        .single();
      
      if (createError) {
        logger.error("Error creating admin conversation", createError);
        toast({ title: "Error", description: "Failed to start conversation", variant: "destructive" });
        return;
      }
      
      logger.debug("Admin conversation created and claimed", { conversationId: newConv.id, claimedBy: userId });
      navigate(`${messagesBasePath}/${newConv.id}`);
    }
  };

  const loadProfilesIfNeeded = async () => {
    if (profilesLoading || profiles.length > 0) return;
    setProfilesLoading(true);
    try {
      const { data, error } = await supabase
        .from("profiles")
        .select("id, full_name")
        .order("full_name", { ascending: true });

      if (error) {
        logger.error("Error fetching profiles", error, { userId });
        toast({
          title: "Error",
          description: "Failed to load users list",
          variant: "destructive",
        });
        return;
      }
      setProfiles((data || []).filter((p) => p.id !== userId));
    } finally {
      setProfilesLoading(false);
    }
  };

  const loadLearnersForMentorIfNeeded = async (forceRefresh = false) => {
    if (!currentMentorProfile?.id || learnersLoading) return;
    if (!forceRefresh && learnersForMentor.length > 0) return;
    setLearnersLoading(true);
    try {
      const mentorId = currentMentorProfile.id;
      let userIds: string[] = [];

      const { data: learnerIds, error: rpcError } = await (supabase as any).rpc("get_mentor_learner_ids", {
        p_mentor_id: mentorId,
      });
      if (!rpcError) {
        const rows = Array.isArray(learnerIds) ? learnerIds : [];
        userIds = rows.map((r: { learner_id?: string }) => r.learner_id).filter((id): id is string => Boolean(id));
      }

      if (userIds.length === 0) {
        const { data: bookings } = await supabase
          .from("bookings")
          .select("user_id")
          .eq("mentor_id", mentorId)
          .not("user_id", "is", null);
        const { data: productIds } = await supabase
          .from("mentor_products")
          .select("id")
          .eq("mentor_id", mentorId);
        const ids = productIds?.map((p) => p.id) ?? [];
        let buyerIds: string[] = [];
        if (ids.length > 0) {
          const { data: purchases } = await supabase
            .from("product_purchases")
            .select("buyer_id")
            .in("product_id", ids)
            .eq("status", "completed");
          buyerIds = (purchases ?? []).map((p) => p.buyer_id);
        }
        userIds = [...new Set([
          ...(bookings ?? []).map((b) => b.user_id).filter((id): id is string => Boolean(id)),
          ...buyerIds,
        ])];
      }

      if (userIds.length === 0) {
        setLearnersForMentor([]);
        return;
      }
      const { data: profs, error } = await supabase
        .from("profiles")
        .select("id, full_name")
        .in("id", userIds)
        .order("full_name", { ascending: true });
      if (error) {
        logger.error("Error fetching learners", error, { mentorId });
        return;
      }
      setLearnersForMentor(profs ?? []);
    } finally {
      setLearnersLoading(false);
    }
  };

  const loadMentorsForLearnerIfNeeded = async () => {
    if (mentorsForLearnerLoading || mentorsForLearner.length > 0) return;
    setMentorsForLearnerLoading(true);
    try {
      const { data, error } = await supabase
        .from("mentor_profiles")
        .select("id, name")
        .or("is_active.eq.true,is_active.is.null")
        .order("name", { ascending: true });
      if (error) {
        logger.error("Error fetching mentors for learner", error);
        toast({ title: "Error", description: "Failed to load mentors", variant: "destructive" });
        return;
      }
      setMentorsForLearner(data ?? []);
    } finally {
      setMentorsForLearnerLoading(false);
    }
  };

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Preload support (admin) mentor profile so "Message to support" works for learners and mentors
  useEffect(() => {
    if (userId) {
      ensureAdminMentorLoaded();
    }
  }, [userId]);

  useEffect(() => {
    fetchConversations();

    const timer = window.setTimeout(() => {
      const channel = supabase
        .channel(`conversations-list-${userId}-${Date.now()}`)
        .on(
          "postgres_changes",
          {
            event: "*",
            schema: "public",
            table: "messages",
          },
          () => {
            fetchConversations();
          }
        )
        .on(
          "postgres_changes",
          {
            event: "*",
            schema: "public",
            table: "conversations",
          },
          () => {
            fetchConversations();
          }
        )
        .subscribe((status) => {
          if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
            if (channelRef.current === channel) {
              supabase.removeChannel(channel).then(() => {});
              channelRef.current = null;
            }
            if (!pollIntervalRef.current) {
              pollIntervalRef.current = setInterval(fetchConversations, 45000);
            }
          }
        });
      channelRef.current = channel;
    }, 1500);

    const handleVisibility = () => {
      if (document.visibilityState === "visible") fetchConversations();
    };
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
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
  }, [userId]);

  const filteredProfiles = useMemo(() => {
    const q = profileSearch.trim().toLowerCase();
    if (!q) return profiles;
    return profiles.filter((p) => (p.full_name || "").toLowerCase().includes(q) || p.id.toLowerCase().includes(q));
  }, [profiles, profileSearch]);

  const filteredLearnersForMentor = useMemo(() => {
    const q = profileSearch.trim().toLowerCase();
    if (!q) return learnersForMentor;
    return learnersForMentor.filter(
      (p) => (p.full_name || "").toLowerCase().includes(q) || p.id.toLowerCase().includes(q)
    );
  }, [learnersForMentor, profileSearch]);

  const filteredMentorsForLearner = useMemo(() => {
    const q = mentorSearch.trim().toLowerCase();
    if (!q) return mentorsForLearner;
    return mentorsForLearner.filter((m) => (m.name || "").toLowerCase().includes(q));
  }, [mentorsForLearner, mentorSearch]);

  const handleArchive = async (conversationId: string, currentlyArchived: boolean, e: React.MouseEvent) => {
    e.stopPropagation();

    const { error } = await supabase
      .from("conversations")
      .update({
        archived: !currentlyArchived,
        archived_at: !currentlyArchived ? new Date().toISOString() : null,
      })
      .eq("id", conversationId);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to update conversation",
        variant: "destructive",
      });
      return;
    }

    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === conversationId
          ? { ...conv, archived: !currentlyArchived, archived_at: !currentlyArchived ? new Date().toISOString() : null }
          : conv
      )
    );

    toast({
      title: currentlyArchived ? "Conversation restored" : "Conversation archived",
    });
  };

  const handleDelete = async () => {
    if (!deleteId) return;

    // Soft delete: Add to conversation_deletions table instead of actually deleting
    const { error } = await supabase
      .from("conversation_deletions")
      .insert({
        conversation_id: deleteId,
        user_id: userId,
      });

    if (error) {
      toast({
        title: "Error",
        description: "Failed to delete conversation",
        variant: "destructive",
      });
      return;
    }

    // Remove from local state
    setConversations((prev) => prev.filter((conv) => conv.id !== deleteId));
    setDeleteId(null);
    toast({ 
      title: "Conversation deleted"
    });
  };

  const activeConversations = conversations.filter((c) => !c.archived);
  const archivedConversations = conversations.filter((c) => c.archived);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Messages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const ConversationItem = ({ conversation }: { conversation: Conversation }) => (
    <div
      className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent/5 transition-colors group cursor-pointer"
      onClick={() => navigate(`${messagesBasePath}/${conversation.id}`)}
    >
      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
        <span className="text-sm font-semibold text-primary">
          {conversation.display_name.charAt(0).toUpperCase()}
        </span>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-semibold truncate">{conversation.display_name}</p>
          {conversation.unread_count > 0 && (
            <Badge className="shrink-0">{conversation.unread_count}</Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground truncate">
          {conversation.is_support ? "Support" : conversation.is_mentor_view ? "Student" : "Mentor"} •{" "}
          {conversation.last_message_at
            ? new Date(conversation.last_message_at).toLocaleDateString()
            : "No messages yet"}
        </p>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={(e) => handleArchive(conversation.id, conversation.archived, e)}>
              {conversation.archived ? (
                <>
                  <ArchiveRestore className="h-4 w-4 mr-2" />
                  Restore
                </>
              ) : (
                <>
                  <Archive className="h-4 w-4 mr-2" />
                  Archive
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                setDeleteId(conversation.id);
              }}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="ghost" size="sm">
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Messages
              </CardTitle>
              <CardDescription>Your conversations</CardDescription>
            </div>

            {isAdmin ? (
              <Button
                size="sm"
                onClick={async () => {
                  setNewConversationOpen("admin");
                  await loadProfilesIfNeeded();
                }}
              >
                New conversation
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                {currentMentorProfile ? (
                  <Button
                    size="sm"
                    onClick={async () => {
                      setNewConversationOpen("mentor");
                      setLearnersForMentor([]);
                      await loadLearnersForMentorIfNeeded(true);
                    }}
                  >
                    New conversation
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={async () => {
                      setNewConversationOpen("learner");
                      await loadMentorsForLearnerIfNeeded();
                    }}
                  >
                    New conversation
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={startConversationWithAdmin}>
                  Message to support
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "active" | "archived")}>
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="active">Active ({activeConversations.length})</TabsTrigger>
              <TabsTrigger value="archived">Archived ({archivedConversations.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="active">
              {activeConversations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No active conversations</p>
                  <p className="text-sm mt-2">
                    {isAdmin
                      ? "Your conversations with learners and mentors will appear here"
                      : currentMentorProfile
                        ? "Your conversations with learners and admins will appear here"
                        : "Start a conversation with a mentor"}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {activeConversations.map((conversation) => (
                    <ConversationItem key={conversation.id} conversation={conversation} />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="archived">
              {archivedConversations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Archive className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No archived conversations</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {archivedConversations.map((conversation) => (
                    <ConversationItem key={conversation.id} conversation={conversation} />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this conversation and all messages. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog
        open={newConversationOpen !== false}
        onOpenChange={(open) => {
          if (!open) {
            setNewConversationOpen(false);
            setProfileSearch("");
            setMentorSearch("");
          }
        }}
      >
        <DialogContent className="sm:max-w-lg" aria-describedby="new-conversation-description">
          <DialogHeader>
            <DialogTitle>
              {newConversationOpen === "admin"
                ? "Start a new conversation"
                : newConversationOpen === "learner"
                  ? "Start a conversation with a mentor"
                  : "Start a conversation with a learner"}
            </DialogTitle>
            <DialogDescription id="new-conversation-description">
              {newConversationOpen === "admin"
                ? "Select a user to message."
                : newConversationOpen === "learner"
                  ? "Choose a mentor to message."
                  : "Only learners who booked a session or bought a product from you appear here."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <Input
              value={newConversationOpen === "learner" ? mentorSearch : profileSearch}
              onChange={(e) =>
                newConversationOpen === "learner"
                  ? setMentorSearch(e.target.value)
                  : setProfileSearch(e.target.value)
              }
              placeholder={
                newConversationOpen === "learner" ? "Search mentors by name" : "Search by name or ID"
              }
            />

            <div className="max-h-72 overflow-auto border rounded-md">
              {newConversationOpen === "admin" ? (
                profilesLoading ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : filteredProfiles.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">No users found.</div>
                ) : (
                  <div className="divide-y">
                    {filteredProfiles.slice(0, 200).map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        className="w-full text-left px-3 py-2 hover:bg-accent/30 transition-colors"
                        onClick={async () => {
                          await startConversationAsAdmin(p.id);
                          setNewConversationOpen(false);
                        }}
                      >
                        <div className="font-medium">{p.full_name || "User"}</div>
                        <div className="text-xs text-muted-foreground">{p.id}</div>
                      </button>
                    ))}
                  </div>
                )
              ) : newConversationOpen === "learner" ? (
                mentorsForLearnerLoading ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : filteredMentorsForLearner.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">No mentors found.</div>
                ) : (
                  <div className="divide-y">
                    {filteredMentorsForLearner.map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        className="w-full text-left px-3 py-2 hover:bg-accent/30 transition-colors"
                        onClick={async () => {
                          await openOrCreateConversation(userId, m.id, m.name);
                          setNewConversationOpen(false);
                        }}
                      >
                        <div className="font-medium">{m.name || "Mentor"}</div>
                        <div className="text-xs text-muted-foreground">{m.id}</div>
                      </button>
                    ))}
                  </div>
                )
              ) : learnersLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : filteredLearnersForMentor.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No learners with a booking or purchase yet.
                </div>
              ) : (
                <div className="divide-y">
                  {filteredLearnersForMentor.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className="w-full text-left px-3 py-2 hover:bg-accent/30 transition-colors"
                      onClick={async () => {
                        if (!currentMentorProfile) return;
                        await openOrCreateConversation(p.id, currentMentorProfile.id, currentMentorProfile.name);
                        setNewConversationOpen(false);
                      }}
                    >
                      <div className="font-medium">{p.full_name || "User"}</div>
                      <div className="text-xs text-muted-foreground">{p.id}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
