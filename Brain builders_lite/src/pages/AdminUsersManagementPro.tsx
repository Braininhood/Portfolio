import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from "@/components/ui/dialog";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { 
  Eye, 
  Edit, 
  Trash2, 
  UserPlus, 
  Search, 
  MessageSquare, 
  Calendar,
  RefreshCw,
  ToggleLeft,
  ToggleRight
} from "lucide-react";
import { logger } from "@/utils/logger";
import { TimezoneSelect } from "@/components/TimezoneSelect";

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  skill_level: string | null;
  goals: string | null;
  preferred_language: string | null;
  timezone: string | null;
  updated_at: string | null;
  created_at: string | null;
}

interface MentorProfile {
  id: string;
  user_id: string | null;
  name: string;
  title: string;
  category: string;
  bio: string;
  full_bio: string;
  price: number;
  expertise: string[];
  languages: string[];
  experience: string;
  education: string;
  image_url: string | null;
  username: string | null;
  timezone?: string | null;
}

interface UserRole {
  id: string;
  user_id: string;
  role: string;
}

interface FullUserData {
  profile: UserProfile;
  mentorProfile: MentorProfile | null;
  roles: UserRole[];
}

const ASSIGNABLE_ROLES = ["learner", "mentor"] as const;
type AssignableRole = (typeof ASSIGNABLE_ROLES)[number];

export default function AdminUsersManagementPro() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [rolesByUser, setRolesByUser] = useState<Record<string, UserRole[]>>({});
  const [mentorProfiles, setMentorProfiles] = useState<Record<string, MentorProfile>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  // Get current user ID on mount
  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setCurrentUserId(user.id);
    });
  }, []);
  
  // Modals
  const [viewUserDialog, setViewUserDialog] = useState(false);
  const [editProfileDialog, setEditProfileDialog] = useState(false);
  const [editMentorDialog, setEditMentorDialog] = useState(false);
  const [addUserDialog, setAddUserDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [roleChangeDialog, setRoleChangeDialog] = useState(false);
  
  // Selected user data
  const [selectedUser, setSelectedUser] = useState<FullUserData | null>(null);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);
  const [roleChangeData, setRoleChangeData] = useState<{userId: string, currentRole: string, newRole: string} | null>(null);
  
  // Form data
  const [profileForm, setProfileForm] = useState({
    full_name: "",
    skill_level: "",
    goals: "",
    preferred_language: "",
    timezone: "",
  });
  
  const [mentorForm, setMentorForm] = useState({
    name: "",
    title: "",
    category: "",
    bio: "",
    full_bio: "",
    price: 0,
    expertise: "",
    languages: "",
    experience: "",
    education: "",
    username: "",
    timezone: "",
  });
  
  const [newUserForm, setNewUserForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "learner" as AssignableRole,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    
    try {
      // Use RPC function to get profiles with emails (admin-only)
      const { data: profilesData, error: profilesError } = await supabase
        .rpc('get_profiles_with_email');
      
      if (profilesError) {
        logger.error("Error fetching profiles", profilesError);
        toast.error("Failed to load user profiles");
        setLoading(false);
        return;
      }
      
      if (!profilesData) {
        setLoading(false);
        return;
      }
      
      setUsers(profilesData as UserProfile[]);
      
      // Fetch roles
      const { data: rolesData } = await supabase
        .from("user_roles")
        .select("id, user_id, role");
      
      const roleMap: Record<string, UserRole[]> = {};
      (rolesData ?? []).forEach((r) => {
        if (!r.role) return;
        const role: UserRole = { id: r.id, user_id: r.user_id, role: r.role };
        if (!roleMap[r.user_id]) roleMap[r.user_id] = [];
        roleMap[r.user_id].push(role);
      });
      setRolesByUser(roleMap);
      
      // Fetch mentor profiles
      const { data: mentorData } = await supabase
        .from("mentor_profiles")
        .select("*");
      
      const mentorMap: Record<string, MentorProfile> = {};
      (mentorData ?? []).forEach((m) => {
        if (m.user_id) {
          mentorMap[m.user_id] = m;
        }
      });
      setMentorProfiles(mentorMap);
      
    } catch (error) {
      logger.error("Error fetching users", error);
      toast.error("Failed to load users");
    }
    
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleViewUser = async (userId: string) => {
    const profile = users.find(u => u.id === userId);
    if (!profile) return;
    
    setSelectedUser({
      profile,
      mentorProfile: mentorProfiles[userId] || null,
      roles: rolesByUser[userId] || [],
    });
    setViewUserDialog(true);
  };

  const handleEditProfile = () => {
    if (!selectedUser) return;
    setProfileForm({
      full_name: selectedUser.profile.full_name || "",
      skill_level: selectedUser.profile.skill_level || "",
      goals: selectedUser.profile.goals || "",
      preferred_language: selectedUser.profile.preferred_language || "",
      timezone: selectedUser.profile.timezone || "",
    });
    setViewUserDialog(false);
    setEditProfileDialog(true);
  };

  const handleEditMentorProfile = () => {
    if (!selectedUser?.mentorProfile) return;
    const mp = selectedUser.mentorProfile;
    setMentorForm({
      name: mp.name,
      title: mp.title,
      category: mp.category,
      bio: mp.bio,
      full_bio: mp.full_bio,
      price: mp.price,
      expertise: mp.expertise.join(", "),
      languages: mp.languages.join(", "),
      experience: mp.experience,
      education: mp.education,
      username: mp.username || "",
      timezone: (mp as { timezone?: string }).timezone || "",
    });
    setViewUserDialog(false);
    setEditMentorDialog(true);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    const { error } = await supabase
      .from("profiles")
      .update({
        full_name: profileForm.full_name || null,
        skill_level: profileForm.skill_level || null,
        goals: profileForm.goals || null,
        preferred_language: profileForm.preferred_language || null,
        timezone: profileForm.timezone?.trim() || null,
      })
      .eq("id", selectedUser.profile.id);

    if (error) {
      logger.error("Error updating profile", error);
      toast.error("Failed to update profile");
    } else {
      toast.success("User profile updated");
      setEditProfileDialog(false);
      fetchData();
    }
  };

  const handleSaveMentorProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser?.mentorProfile) return;

    const { error } = await supabase
      .from("mentor_profiles")
      .update({
        name: mentorForm.name,
        title: mentorForm.title,
        category: mentorForm.category,
        bio: mentorForm.bio,
        full_bio: mentorForm.full_bio,
        price: mentorForm.price,
        expertise: mentorForm.expertise.split(",").map(e => e.trim()).filter(Boolean),
        languages: mentorForm.languages.split(",").map(l => l.trim()).filter(Boolean),
        experience: mentorForm.experience,
        education: mentorForm.education,
        username: mentorForm.username || null,
        timezone: mentorForm.timezone?.trim() || null,
      })
      .eq("id", selectedUser.mentorProfile.id);

    if (error) {
      logger.error("Error updating mentor profile", error);
      toast.error("Failed to update mentor profile");
    } else {
      toast.success("Mentor profile updated");
      setEditMentorDialog(false);
      fetchData();
    }
  };

  const handleRoleChange = async (userId: string, currentRole: string, newRole: string) => {
    setRoleChangeData({ userId, currentRole, newRole });
    setRoleChangeDialog(true);
  };

  const confirmRoleChange = async () => {
    if (!roleChangeData) return;
    
    const { userId, currentRole, newRole } = roleChangeData;
    const { data: { user: currentUser } } = await supabase.auth.getUser();
    const isChangingSelf = currentUser && currentUser.id === userId;
    
    console.log("🔄 Starting role change:");
    console.log("   - Target user ID:", userId);
    console.log("   - Current user ID:", currentUser?.id);
    console.log("   - Is changing self:", isChangingSelf);
    console.log("   - Role change:", currentRole, "→", newRole);
    
    // Remove old role
    const oldRoleRecord = rolesByUser[userId]?.find(r => r.role === currentRole);
    if (oldRoleRecord) {
      await supabase.from("user_roles").delete().eq("id", oldRoleRecord.id);
    }
    
    // Add new role (cast to the enum type)
    await supabase.from("user_roles").insert({ 
      user_id: userId, 
      role: newRole as "learner" | "mentor" 
    });
    
    console.log("✅ Role updated in database");
    
    if (isChangingSelf) {
      console.log("🎯 This is YOU changing your own role!");
      
      // Close dialog first
      setRoleChangeDialog(false);
      setRoleChangeData(null);
      
      // Store the target redirect in sessionStorage AND localStorage
      const targetUrl = newRole === "mentor" ? "/mentor/dashboard" : "/learner/dashboard";
      sessionStorage.setItem("post_role_change_redirect", targetUrl);
      localStorage.setItem("post_role_change_redirect", targetUrl);
      
      console.log("📦 Target URL:", targetUrl);
      console.log("📦 SessionStorage:", sessionStorage.getItem("post_role_change_redirect"));
      console.log("📦 LocalStorage:", localStorage.getItem("post_role_change_redirect"));
      
      // Show toast BEFORE timeout
      toast.success(`Your role changed to ${newRole}`, {
        description: "Signing out now...",
        duration: 5000,
      });
      
      // Immediate redirect - don't wait
      console.log("🔓 Initiating sign out...");
      
      try {
        const { error } = await supabase.auth.signOut();
        if (error) {
          console.error("❌ Sign out error:", error);
        } else {
          console.log("✅ Signed out successfully");
        }
      } catch (err) {
        console.error("❌ Sign out exception:", err);
      }
      
      // Force redirect regardless of sign-out result
      console.log("🎯 Redirecting to auth page...");
      window.location.href = "/auth?role_changed=true";
      
    } else {
      console.log("👤 Changing another user's role (not yours)");
      toast.success(`Role changed from ${currentRole} to ${newRole}`);
      setRoleChangeDialog(false);
      setRoleChangeData(null);
      fetchData();
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    toast.error("User creation must be done through Supabase Dashboard", {
      description: "Go to your Supabase project > Authentication > Users > Add User",
    });
    
    // Note: Cannot use admin.createUser from client side (requires service role key)
    // Users must be created through Supabase Dashboard or a server-side API endpoint
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      if (!token) {
        toast.error("Session expired. Please sign in again.");
        setDeleteDialog(false);
        setUserToDelete(null);
        return;
      }

      const { data, error } = await supabase.functions.invoke("admin-delete-user", {
        body: { userId: userToDelete },
        headers: { Authorization: `Bearer ${token}` },
      });

      if (error) {
        toast.error(error.message ?? "Failed to delete user");
        return;
      }
      if (data?.error) {
        toast.error(data.error);
        return;
      }

      toast.success("User deleted successfully");
      setDeleteDialog(false);
      setUserToDelete(null);
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  // Filter users
  const filteredUsers = users.filter((u) => {
    const roles = rolesByUser[u.id] ?? [];
    const isAdmin = roles.some((r) => r.role === "admin");
    if (isAdmin) return false; // Never show admins
    
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      u.full_name?.toLowerCase().includes(search) ||
      u.email.toLowerCase().includes(search) ||
      u.id.toLowerCase().includes(search)
    );
  });

  const getUserType = (userId: string): string => {
    const roles = rolesByUser[userId] ?? [];
    const hasMentorProfile = !!mentorProfiles[userId];
    
    if (roles.some(r => r.role === "mentor") || hasMentorProfile) {
      if (roles.some(r => r.role === "learner")) {
        return "Both";
      }
      return "Mentor";
    }
    return "Learner";
  };

  const getPrimaryRole = (userId: string): string => {
    const roles = rolesByUser[userId] ?? [];
    if (roles.some(r => r.role === "mentor")) return "mentor";
    if (roles.some(r => r.role === "learner")) return "learner";
    return "learner";
  };

  const handleToggleDashboard = async (userId: string) => {
    const roles = rolesByUser[userId] || [];
    const currentRole = getPrimaryRole(userId);
    const hasMentorRole = roles.some(r => r.role === "mentor");
    const hasLearnerRole = roles.some(r => r.role === "learner");
    const hasMentorProfile = !!mentorProfiles[userId];

    // Determine target role
    const newRole: AssignableRole = currentRole === "mentor" ? "learner" : "mentor";
    
    // Validation: Can only toggle to mentor if they have mentor profile
    if (newRole === "mentor" && !hasMentorProfile) {
      toast.error("User must have a mentor profile to switch to mentor dashboard");
      return;
    }

    // If user doesn't have the target role, add it
    if (newRole === "mentor" && !hasMentorRole) {
      const { error: insertError } = await supabase
        .from("user_roles")
        .insert({ user_id: userId, role: "mentor" as "learner" | "mentor" });
      
      if (insertError) {
        logger.error("Error adding mentor role", insertError);
        toast.error("Failed to add mentor role");
        return;
      }
    }

    if (newRole === "learner" && !hasLearnerRole) {
      const { error: insertError } = await supabase
        .from("user_roles")
        .insert({ user_id: userId, role: "learner" as "learner" | "mentor" });
      
      if (insertError) {
        logger.error("Error adding learner role", insertError);
        toast.error("Failed to add learner role");
        return;
      }
    }

    // Remove the old primary role
    const roleToRemove = roles.find(r => r.role === currentRole);
    if (roleToRemove) {
      const { error: deleteError } = await supabase
        .from("user_roles")
        .delete()
        .eq("id", roleToRemove.id);
      
      if (deleteError) {
        logger.error("Error removing role", deleteError);
        toast.error("Failed to toggle dashboard");
        return;
      }
    }

    const dashboardName = newRole === "mentor" ? "Mentor" : "Learner";
    toast.success(`User dashboard toggled to ${dashboardName}`);
    fetchData();
  };

  const hasDashboardSwitch = (userId: string): boolean => {
    const roles = rolesByUser[userId] ?? [];
    return roles.some(r => r.role === "learner") && roles.some(r => r.role === "mentor");
  };

  const handleAllowDashboardSwitch = async (userId: string, allow: boolean) => {
    const roles = rolesByUser[userId] ?? [];
    const primaryRole = getPrimaryRole(userId);
    const hasMentorProfile = !!mentorProfiles[userId];

    if (allow) {
      const otherRole: AssignableRole = primaryRole === "mentor" ? "learner" : "mentor";
      if (otherRole === "mentor" && !hasMentorProfile) {
        toast.error("User must have a mentor profile to allow mentor dashboard switch");
        return;
      }
      const alreadyHas = roles.some(r => r.role === otherRole);
      if (alreadyHas) return;
      const { error } = await supabase
        .from("user_roles")
        .insert({ user_id: userId, role: otherRole as "learner" | "mentor" });
      if (error) {
        logger.error("Error adding role for dashboard switch", error);
        toast.error("Failed to allow dashboard switch");
        return;
      }
      toast.success("User can now switch between Learner and Mentor dashboards");
    } else {
      const toRemove = primaryRole === "mentor" ? "learner" : "mentor";
      const row = roles.find(r => r.role === toRemove);
      if (!row) return;
      const { error } = await supabase.from("user_roles").delete().eq("id", row.id);
      if (error) {
        logger.error("Error removing role", error);
        toast.error("Failed to remove dashboard switch");
        return;
      }
      toast.success("Dashboard switch removed. User will see only their primary dashboard.");
    }
    fetchData();
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <p className="text-muted-foreground">Loading users...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle>Users Management</CardTitle>
              <CardDescription>
                Manage all platform users - view, edit, change roles, add or delete users
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={() => setAddUserDialog(true)} size="sm">
                <UserPlus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            <div className="text-sm text-muted-foreground">
              {filteredUsers.length} users
            </div>
          </div>

          {filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchTerm ? "No users found" : "No users to display"}
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Current Role</TableHead>
                    <TableHead>Has Mentor Profile</TableHead>
                    <TableHead className="text-center whitespace-nowrap">Can switch</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => {
                    const userType = getUserType(user.id);
                    const primaryRole = getPrimaryRole(user.id);
                    const hasMentorProfile = !!mentorProfiles[user.id];
                    
                    return (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium flex items-center gap-2">
                              {user.full_name || "—"}
                              {user.id === currentUserId && (
                                <Badge variant="secondary" className="text-xs">You</Badge>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={userType === "Mentor" || userType === "Both" ? "default" : "secondary"}>
                            {userType}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={primaryRole}
                            onValueChange={(newRole) => handleRoleChange(user.id, primaryRole, newRole)}
                          >
                            <SelectTrigger className="w-[120px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="learner">Learner</SelectItem>
                              <SelectItem value="mentor">Mentor</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          {hasMentorProfile ? (
                            <Badge variant="outline">Yes</Badge>
                          ) : (
                            <span className="text-muted-foreground">No</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Switch
                            checked={hasDashboardSwitch(user.id)}
                            onCheckedChange={(checked) => handleAllowDashboardSwitch(user.id, checked)}
                            disabled={primaryRole === "learner" && !hasMentorProfile}
                            title={primaryRole === "learner" && !hasMentorProfile ? "Add mentor profile first" : "Allow user to switch between Learner and Mentor dashboards"}
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleToggleDashboard(user.id)}
                              title={`Toggle to ${primaryRole === "mentor" ? "Learner" : "Mentor"} Dashboard`}
                              disabled={primaryRole === "learner" && !mentorProfiles[user.id]}
                            >
                              {primaryRole === "mentor" ? (
                                <ToggleRight className="h-4 w-4 text-green-600" />
                              ) : (
                                <ToggleLeft className="h-4 w-4 text-blue-600" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleViewUser(user.id)}
                              title="View details"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setUserToDelete(user.id);
                                setDeleteDialog(true);
                              }}
                              title="Delete user"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* View User Details Dialog */}
      <Dialog open={viewUserDialog} onOpenChange={setViewUserDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
            <DialogDescription>
              Complete information for {selectedUser?.profile.full_name || selectedUser?.profile.email}
            </DialogDescription>
          </DialogHeader>
          
          {selectedUser && (
            <Tabs defaultValue="profile" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="profile">User Profile</TabsTrigger>
                <TabsTrigger value="mentor" disabled={!selectedUser.mentorProfile}>
                  Mentor Profile
                </TabsTrigger>
                <TabsTrigger value="activity">Activity</TabsTrigger>
              </TabsList>
              
              <TabsContent value="profile" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">User Profile</CardTitle>
                    <CardDescription>Basic user information from profiles table</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-muted-foreground">Email</Label>
                        <p className="font-medium">{selectedUser.profile.email}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Full Name</Label>
                        <p className="font-medium">{selectedUser.profile.full_name || "—"}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Skill Level</Label>
                        <p className="font-medium">{selectedUser.profile.skill_level || "—"}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Language</Label>
                        <p className="font-medium">{selectedUser.profile.preferred_language || "—"}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Time zone</Label>
                        <p className="font-medium">{selectedUser.profile.timezone || "—"}</p>
                      </div>
                      <div className="col-span-2">
                        <Label className="text-muted-foreground">Goals</Label>
                        <p className="font-medium">{selectedUser.profile.goals || "—"}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Roles</Label>
                        <div className="flex gap-1 mt-1">
                          {selectedUser.roles.map((r) => (
                            <Badge key={r.id} variant="outline">{r.role}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    <Button onClick={handleEditProfile} className="mt-4">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit User Profile
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="mentor" className="space-y-4">
                {selectedUser.mentorProfile ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Mentor Profile</CardTitle>
                      <CardDescription>Professional mentor information from mentor_profiles table</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-muted-foreground">Name</Label>
                          <p className="font-medium">{selectedUser.mentorProfile.name}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Title</Label>
                          <p className="font-medium">{selectedUser.mentorProfile.title}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Category</Label>
                          <p className="font-medium">{selectedUser.mentorProfile.category}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Price</Label>
                          <p className="font-medium">${selectedUser.mentorProfile.price}</p>
                        </div>
                        <div className="col-span-2">
                          <Label className="text-muted-foreground">Bio</Label>
                          <p className="font-medium">{selectedUser.mentorProfile.bio}</p>
                        </div>
                        <div className="col-span-2">
                          <Label className="text-muted-foreground">Expertise</Label>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {selectedUser.mentorProfile.expertise.map((e, i) => (
                              <Badge key={i} variant="secondary">{e}</Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Username</Label>
                          <p className="font-medium">{selectedUser.mentorProfile.username || "—"}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Time zone</Label>
                          <p className="font-medium">{(selectedUser.mentorProfile as { timezone?: string }).timezone || "—"}</p>
                        </div>
                      </div>
                      <Button onClick={handleEditMentorProfile} className="mt-4">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Mentor Profile
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="py-8 text-center text-muted-foreground">
                      No mentor profile
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
              
              <TabsContent value="activity" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">User Activity</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => navigate(`/admin?tab=messages`)}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      View Messages
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => navigate(`/admin?tab=bookings`)}
                    >
                      <Calendar className="h-4 w-4 mr-2" />
                      View Bookings
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit User Profile Dialog */}
      <Dialog open={editProfileDialog} onOpenChange={setEditProfileDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User Profile</DialogTitle>
            <DialogDescription>Update basic user information</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <Label>Full Name</Label>
              <Input
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
              />
            </div>
            <div>
              <Label>Skill Level</Label>
              <Select
                value={profileForm.skill_level}
                onValueChange={(v) => setProfileForm({ ...profileForm, skill_level: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Goals</Label>
              <Textarea
                value={profileForm.goals}
                onChange={(e) => setProfileForm({ ...profileForm, goals: e.target.value })}
              />
            </div>
            <div>
              <Label>Preferred Language</Label>
              <Select
                value={profileForm.preferred_language}
                onValueChange={(v) => setProfileForm({ ...profileForm, preferred_language: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <TimezoneSelect
                value={profileForm.timezone}
                onValueChange={(v) => setProfileForm({ ...profileForm, timezone: v })}
                label="Time zone"
                placeholder="Select time zone"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditProfileDialog(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Mentor Profile Dialog */}
      <Dialog open={editMentorDialog} onOpenChange={setEditMentorDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Mentor Profile</DialogTitle>
            <DialogDescription>Update professional mentor information</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSaveMentorProfile} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Name</Label>
                <Input
                  value={mentorForm.name}
                  onChange={(e) => setMentorForm({ ...mentorForm, name: e.target.value })}
                />
              </div>
              <div>
                <Label>Title</Label>
                <Input
                  value={mentorForm.title}
                  onChange={(e) => setMentorForm({ ...mentorForm, title: e.target.value })}
                />
              </div>
              <div>
                <Label>Category</Label>
                <Input
                  value={mentorForm.category}
                  onChange={(e) => setMentorForm({ ...mentorForm, category: e.target.value })}
                />
              </div>
              <div>
                <Label>Price</Label>
                <Input
                  type="number"
                  value={mentorForm.price}
                  onChange={(e) => setMentorForm({ ...mentorForm, price: Number(e.target.value) })}
                />
              </div>
              <div className="col-span-2">
                <Label>Bio</Label>
                <Textarea
                  value={mentorForm.bio}
                  onChange={(e) => setMentorForm({ ...mentorForm, bio: e.target.value })}
                />
              </div>
              <div className="col-span-2">
                <Label>Expertise (comma-separated)</Label>
                <Input
                  value={mentorForm.expertise}
                  onChange={(e) => setMentorForm({ ...mentorForm, expertise: e.target.value })}
                />
              </div>
              <div>
                <Label>Username</Label>
                <Input
                  value={mentorForm.username}
                  onChange={(e) => setMentorForm({ ...mentorForm, username: e.target.value })}
                />
              </div>
              <div className="col-span-2">
                <TimezoneSelect
                  value={mentorForm.timezone}
                  onValueChange={(v) => setMentorForm({ ...mentorForm, timezone: v })}
                  label="Time zone"
                  placeholder="Select mentor time zone"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditMentorDialog(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add User Dialog */}
      <Dialog open={addUserDialog} onOpenChange={setAddUserDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New User</DialogTitle>
            <DialogDescription>Create a new user account</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddUser} className="space-y-4">
            <div>
              <Label>Email*</Label>
              <Input
                type="email"
                required
                value={newUserForm.email}
                onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
              />
            </div>
            <div>
              <Label>Password*</Label>
              <Input
                type="password"
                required
                value={newUserForm.password}
                onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
              />
            </div>
            <div>
              <Label>Full Name</Label>
              <Input
                value={newUserForm.full_name}
                onChange={(e) => setNewUserForm({ ...newUserForm, full_name: e.target.value })}
              />
            </div>
            <div>
              <Label>Initial Role</Label>
              <Select
                value={newUserForm.role}
                onValueChange={(v: AssignableRole) => setNewUserForm({ ...newUserForm, role: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="learner">Learner</SelectItem>
                  <SelectItem value="mentor">Mentor</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddUserDialog(false)}>
                Cancel
              </Button>
              <Button type="submit">Create User</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Role Change Confirmation */}
      <AlertDialog open={roleChangeDialog} onOpenChange={setRoleChangeDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Change User Role?</AlertDialogTitle>
            <AlertDialogDescription>
              This will change the user's role from <strong>{roleChangeData?.currentRole}</strong> to <strong>{roleChangeData?.newRole}</strong>.
              The old role will be removed and replaced with the new role.
              {roleChangeData?.currentRole === "mentor" && " Their mentor profile will be preserved but inactive."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmRoleChange}>Confirm Change</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete User Confirmation */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the user and all their data. All data will be archived before deletion.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} className="bg-destructive text-destructive-foreground">
              Delete User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
