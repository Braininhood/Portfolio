import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Edit } from "lucide-react";
import { profileSchema, validateData } from "@/utils/validation";
import { logger } from "@/utils/logger";

const ONLINE_MINUTES = 5;

interface Profile {
  id: string;
  full_name: string | null;
  skill_level: string | null;
  goals: string | null;
  preferred_language: string | null;
  updated_at: string | null;
  last_seen_at?: string | null;
}

interface UserRole {
  id: string;
  user_id: string;
  role: string;
}

/** Only learner and mentor can be assigned from UI. Admin is managed only via SQL. */
const ASSIGNABLE_ROLES = ["learner", "mentor"] as const;
type AssignableRole = (typeof ASSIGNABLE_ROLES)[number];

export default function AdminLearners() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [rolesByUser, setRolesByUser] = useState<Record<string, UserRole[]>>({});
  const [mentorUserIds, setMentorUserIds] = useState<Set<string>>(new Set());
  const [adminUserIds, setAdminUserIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
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
    const admins = new Set<string>();
    (rolesRes.data ?? []).forEach((r: UserRole) => {
      if (!roleMap[r.user_id]) roleMap[r.user_id] = [];
      roleMap[r.user_id].push(r);
      if (r.role === "admin") admins.add(r.user_id);
    });
    setRolesByUser(roleMap);
    setAdminUserIds(admins);

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
    
    // Validate input
    const dataToValidate = {
      full_name: formData.full_name.trim() || undefined,
      skill_level: formData.skill_level || undefined,
      goals: formData.goals.trim() || undefined,
      preferred_language: formData.preferred_language.trim() || undefined,
    };
    
    const validation = validateData(profileSchema, dataToValidate);
    if (!validation.success) {
      logger.warn("Validation failed for profile", { errors: validation.errors, profileId: editingProfile.id });
      toast.error(`Validation error: ${validation.errors[0]}`);
      return;
    }
    
    const { error } = await supabase
      .from("profiles")
      .update({
        full_name: validation.data.full_name || null,
        skill_level: validation.data.skill_level || null,
        goals: validation.data.goals || null,
        preferred_language: validation.data.preferred_language || null,
      })
      .eq("id", editingProfile.id);
    if (error) {
      logger.error("Failed to update profile", error, { profileId: editingProfile.id });
      toast.error(error.message);
      return;
    }
    toast.success("Profile updated");
    setShowDialog(false);
    setEditingProfile(null);
    fetchData();
  };

  const handleAddRole = async (userId: string, role: AssignableRole) => {
    const { data: inserted, error } = await supabase
      .from("user_roles")
      .insert({ user_id: userId, role })
      .select("id, user_id, role")
      .single();
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Role added");
    setRolesByUser((prev) => ({
      ...prev,
      [userId]: [...(prev[userId] ?? []), inserted as UserRole],
    }));
    fetchData();
  };

  const handleRemoveRole = async (roleId: string, userId: string, role: string) => {
    if (role === "admin") return;
    if (!confirm("Remove this role?")) return;
    const { error } = await supabase.from("user_roles").delete().eq("id", roleId);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Role removed");
    setRolesByUser((prev) => ({
      ...prev,
      [userId]: (prev[userId] ?? []).filter((r) => r.id !== roleId),
    }));
    fetchData();
  };

  const handleEdit = (p: Profile) => {
    setEditingProfile(p);
    setFormData({
      full_name: p.full_name ?? "",
      skill_level: p.skill_level ?? "",
      goals: p.goals ?? "",
      preferred_language: p.preferred_language ?? "",
    });
    setShowDialog(true);
  };

  const visibleProfiles = profiles.filter((p) => !adminUserIds.has(p.id));
  const learnerProfiles = visibleProfiles.filter((p) => !mentorUserIds.has(p.id));
  const mentorProfiles = visibleProfiles.filter((p) => mentorUserIds.has(p.id));

  const isOnline = (lastSeen: string | null | undefined) => {
    if (!lastSeen) return false;
    return Date.now() - new Date(lastSeen).getTime() < ONLINE_MINUTES * 60 * 1000;
  };

  const renderTable = (list: Profile[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Skill level</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Roles</TableHead>
          <TableHead className="text-right">Updated</TableHead>
          <TableHead className="w-[100px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {list.map((p) => {
          const roles = (rolesByUser[p.id] ?? []).filter((r) => r.role !== "admin");
          const hasMentorProfile = mentorUserIds.has(p.id);
          const primaryRole = roles.some((r) => r.role === "mentor") || hasMentorProfile ? "Mentor" : "Learner";
          const online = isOnline(p.last_seen_at ?? null);
          return (
            <TableRow key={p.id}>
              <TableCell className="font-medium">{p.full_name || "—"}</TableCell>
              <TableCell>
                <span className={online ? "text-green-600" : "text-muted-foreground"}>
                  {online ? "Online" : "Offline"}
                </span>
              </TableCell>
              <TableCell>{p.skill_level || "—"}</TableCell>
              <TableCell>
                <Badge variant="secondary">{primaryRole}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap items-center gap-1">
                  {roles.map((r) => (
                    <Badge key={r.id} variant="outline" className="mr-1">
                      {r.role}
                      <button
                        type="button"
                        className="ml-1 rounded hover:bg-muted"
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
                        <SelectItem key={r} value={r}>{r}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-sm">
                {p.updated_at ? new Date(p.updated_at).toLocaleDateString() : "—"}
              </TableCell>
              <TableCell>
                <Button variant="ghost" size="icon" onClick={() => handleEdit(p)} title="Edit profile">
                  <Edit className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Learners & mentors</h1>
          <p className="text-sm text-muted-foreground">
            Learners tab: users without a mentor profile. Mentors tab: users with a mentor profile. Edit profile updates data in place (no duplicate). Role changes update the DB and the user’s dashboard.
          </p>
        </div>

        <Tabs defaultValue="learners" className="space-y-4">
          <TabsList>
            <TabsTrigger value="learners">Learners ({learnerProfiles.length})</TabsTrigger>
            <TabsTrigger value="mentors">Mentors ({mentorProfiles.length})</TabsTrigger>
          </TabsList>
          <Card>
            {loading ? (
              <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
            ) : (
              <>
                <TabsContent value="learners" className="mt-0">
                  {learnerProfiles.length === 0 ? (
                    <CardContent className="py-12 text-center text-muted-foreground">No learners. (Users with a mentor profile appear in the Mentors tab.)</CardContent>
                  ) : (
                    renderTable(learnerProfiles)
                  )}
                </TabsContent>
                <TabsContent value="mentors" className="mt-0">
                  {mentorProfiles.length === 0 ? (
                    <CardContent className="py-12 text-center text-muted-foreground">No mentors. Add mentor role or create a mentor profile from the Mentors admin page.</CardContent>
                  ) : (
                    renderTable(mentorProfiles)
                  )}
                </TabsContent>
              </>
            )}
          </Card>
        </Tabs>

        <Dialog open={showDialog} onOpenChange={(open) => { setShowDialog(open); if (!open) setEditingProfile(null); }}>
          <DialogContent className="max-w-md" aria-describedby="admin-learners-edit-desc">
            <DialogHeader>
              <DialogTitle>Edit profile</DialogTitle>
              <DialogDescription id="admin-learners-edit-desc">
                Update this user's profile details.
              </DialogDescription>
            </DialogHeader>
            {editingProfile && (
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div>
                  <Label>Full name</Label>
                  <Input
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Skill level</Label>
                  <Select value={formData.skill_level} onValueChange={(v) => setFormData({ ...formData, skill_level: v })}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Goals</Label>
                  <Input
                    value={formData.goals}
                    onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Preferred language</Label>
                  <Input
                    value={formData.preferred_language}
                    onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
                  <Button type="submit">Save</Button>
                </div>
              </form>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
