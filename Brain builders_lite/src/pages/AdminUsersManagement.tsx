import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Edit, UserMinus, UserPlus, Search } from "lucide-react";
import { profileSchema, validateData } from "@/utils/validation";
import { logger } from "@/utils/logger";

interface Profile {
  id: string;
  full_name: string | null;
  skill_level: string | null;
  goals: string | null;
  preferred_language: string | null;
  updated_at: string | null;
}

interface UserRole {
  id: string;
  user_id: string;
  role: string;
}

const ASSIGNABLE_ROLES = ["learner", "mentor"] as const;
type AssignableRole = (typeof ASSIGNABLE_ROLES)[number];

export default function AdminUsersManagement() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [rolesByUser, setRolesByUser] = useState<Record<string, UserRole[]>>({});
  const [mentorUserIds, setMentorUserIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [formData, setFormData] = useState({
    full_name: "",
    skill_level: "",
    goals: "",
    preferred_language: "",
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [profRes, rolesRes, mentorRes] = await Promise.all([
      supabase.from("profiles").select("id, full_name, skill_level, goals, preferred_language, updated_at").order("updated_at", { ascending: false }),
      supabase.from("user_roles").select("id, user_id, role"),
      supabase.from("mentor_profiles").select("user_id"),
    ]);
    
    if (profRes.data) setProfiles(profRes.data);

    const roleMap: Record<string, UserRole[]> = {};
    (rolesRes.data ?? []).forEach((r: UserRole) => {
      if (!roleMap[r.user_id]) roleMap[r.user_id] = [];
      roleMap[r.user_id].push(r);
    });
    setRolesByUser(roleMap);

    const mentorIds = new Set<string>();
    (mentorRes.data ?? []).forEach((row: { user_id: string | null }) => {
      if (row.user_id) mentorIds.add(row.user_id);
    });
    setMentorUserIds(mentorIds);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProfile) return;

    const validation = validateData(profileSchema, {
      full_name: formData.full_name || null,
      skill_level: formData.skill_level || null,
      goals: formData.goals || null,
      preferred_language: formData.preferred_language || null,
    });

    if (!validation.success) {
      toast.error("Validation failed", { description: validation.errors[0] });
      return;
    }

    const { error } = await supabase
      .from("profiles")
      .update(validation.data)
      .eq("id", editingProfile.id);

    if (error) {
      logger.error("Error updating profile", error);
      toast.error("Error updating profile");
    } else {
      toast.success("Profile updated successfully");
      setShowDialog(false);
      fetchData();
    }
  };

  const handleEdit = (p: Profile) => {
    setEditingProfile(p);
    setFormData({
      full_name: p.full_name || "",
      skill_level: p.skill_level || "",
      goals: p.goals || "",
      preferred_language: p.preferred_language || "",
    });
    setShowDialog(true);
  };

  const handleAddRole = async (userId: string, role: AssignableRole) => {
    const { error } = await supabase.from("user_roles").insert({ user_id: userId, role });
    if (error) {
      logger.error("Error adding role", error);
      toast.error("Failed to add role");
    } else {
      toast.success(`${role} role added successfully`);
      fetchData();
    }
  };

  const handleRemoveRole = async (roleId: string, userId: string, roleName: string) => {
    const { error } = await supabase.from("user_roles").delete().eq("id", roleId);
    if (error) {
      logger.error("Error removing role", error);
      toast.error("Failed to remove role");
    } else {
      toast.success(`${roleName} role removed successfully`);
      fetchData();
    }
  };

  // Filter out admin users - they should NEVER appear in this list
  const visibleProfiles = profiles.filter((p) => {
    const userRoles = rolesByUser[p.id] ?? [];
    const isAdmin = userRoles.some((r) => r.role === "admin");
    return !isAdmin; // Exclude all admins
  });

  // Filter by search term
  const filteredProfiles = visibleProfiles.filter((p) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      p.full_name?.toLowerCase().includes(search) ||
      p.id.toLowerCase().includes(search)
    );
  });

  const getUserType = (userId: string): string => {
    const roles = rolesByUser[userId] ?? [];
    const hasMentorProfile = mentorUserIds.has(userId);
    
    if (roles.some(r => r.role === "mentor") || hasMentorProfile) {
      if (roles.some(r => r.role === "learner")) {
        return "Mentor & Learner";
      }
      return "Mentor";
    }
    return "Learner";
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">Loading users...</p>
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
                Manage all platform users, edit profiles, and change roles
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[250px]"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex gap-4">
            <div className="text-sm">
              <span className="font-medium">Total Users:</span> {filteredProfiles.length}
            </div>
            <div className="text-sm">
              <span className="font-medium">Learners:</span>{" "}
              {filteredProfiles.filter(p => getUserType(p.id) === "Learner").length}
            </div>
            <div className="text-sm">
              <span className="font-medium">Mentors:</span>{" "}
              {filteredProfiles.filter(p => getUserType(p.id).includes("Mentor")).length}
            </div>
          </div>

          {filteredProfiles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchTerm ? "No users found matching your search" : "No users found"}
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Skill Level</TableHead>
                    <TableHead>Roles</TableHead>
                    <TableHead className="text-right">Updated</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProfiles.map((p) => {
                    const roles = (rolesByUser[p.id] ?? []).filter((r) => r.role !== "admin");
                    const userType = getUserType(p.id);
                    const hasMentorProfile = mentorUserIds.has(p.id);
                    
                    return (
                      <TableRow key={p.id}>
                        <TableCell className="font-medium">
                          {p.full_name || "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant={userType.includes("Mentor") ? "default" : "secondary"}>
                            {userType}
                          </Badge>
                        </TableCell>
                        <TableCell>{p.skill_level || "—"}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap items-center gap-1">
                            {roles.map((r) => (
                              <Badge key={r.id} variant="outline" className="mr-1">
                                {r.role}
                                <button
                                  type="button"
                                  className="ml-1 rounded hover:bg-destructive hover:text-destructive-foreground"
                                  onClick={() => handleRemoveRole(r.id, p.id, r.role)}
                                  aria-label={`Remove ${r.role}`}
                                >
                                  ×
                                </button>
                              </Badge>
                            ))}
                            <Select
                              value=""
                              onValueChange={(v) => handleAddRole(p.id, v as AssignableRole)}
                            >
                              <SelectTrigger className="w-[90px] h-7">
                                <SelectValue placeholder="+ Role" />
                              </SelectTrigger>
                              <SelectContent>
                                {ASSIGNABLE_ROLES.filter((r) => !roles.some((x) => x.role === r)).map((r) => (
                                  <SelectItem key={r} value={r}>
                                    {r}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-muted-foreground text-sm">
                          {p.updated_at ? new Date(p.updated_at).toLocaleDateString() : "—"}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(p)}
                            title="Edit profile"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
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

      {/* Edit Profile Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User Profile</DialogTitle>
            <DialogDescription>
              Update user profile information
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="skill_level">Skill Level</Label>
              <Select
                value={formData.skill_level}
                onValueChange={(v) => setFormData({ ...formData, skill_level: v })}
              >
                <SelectTrigger id="skill_level">
                  <SelectValue placeholder="Select skill level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="goals">Goals</Label>
              <Input
                id="goals"
                value={formData.goals}
                onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="preferred_language">Preferred Language</Label>
              <Select
                value={formData.preferred_language}
                onValueChange={(v) => setFormData({ ...formData, preferred_language: v })}
              >
                <SelectTrigger id="preferred_language">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="zh">Chinese</SelectItem>
                  <SelectItem value="ja">Japanese</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
