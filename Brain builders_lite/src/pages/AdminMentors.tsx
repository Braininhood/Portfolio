import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import { Plus, Edit, Trash2, ExternalLink, UserMinus } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { mentorProfileSchema, type MentorProfileInput, validateData } from "@/utils/validation";
import { logger } from "@/utils/logger";
import { TimezoneSelect } from "@/components/TimezoneSelect";

interface MentorProfile {
  id: string;
  user_id: string | null;
  name: string;
  title: string;
  category: string;
  price: number;
  bio: string;
  full_bio: string;
  is_active: boolean | null;
  created_at: string;
  username: string | null;
}

interface UserRoleRow {
  id: string;
  user_id: string;
  role: string;
}

export default function AdminMentors() {
  const [mentors, setMentors] = useState<MentorProfile[]>([]);
  const [rolesByUser, setRolesByUser] = useState<Record<string, UserRoleRow[]>>({});
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ id: string } | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingMentor, setEditingMentor] = useState<MentorProfile | null>(null);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    title: "",
    category: "Business",
    image_url: "",
    price: "",
    bio: "",
    full_bio: "",
    expertise: "",
    languages: "",
    availability: "Available this week",
    experience: "",
    education: "",
    certifications: "",
    timezone: "",
  });

  const fetchMentors = useCallback(async () => {
    setLoading(true);
    const [mentorsRes, rolesRes] = await Promise.all([
      supabase.from("mentor_profiles").select("*").order("created_at", { ascending: false }),
      supabase.from("user_roles").select("id, user_id, role"),
    ]);

    if (mentorsRes.error) {
      console.error("Error fetching mentors:", mentorsRes.error);
      toast.error("Failed to load mentors");
      setMentors([]);
    } else {
      setMentors(mentorsRes.data ?? []);
    }

    const roleMap: Record<string, UserRoleRow[]> = {};
    (rolesRes.data ?? []).forEach((r: UserRoleRow) => {
      if (!roleMap[r.user_id]) roleMap[r.user_id] = [];
      roleMap[r.user_id].push(r);
    });
    setRolesByUser(roleMap);
    setLoading(false);
  }, []);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        toast.error("Please sign in");
        navigate("/auth");
        return;
      }
      setUser(session.user);
    });
  }, [navigate]);

  useEffect(() => {
    if (user) fetchMentors();
  }, [user, fetchMentors]);

  useEffect(() => {
    const onFocus = () => {
      if (user) fetchMentors();
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [user, fetchMentors]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    // Prepare data for validation
    const dataToValidate: Partial<MentorProfileInput> = {
      name: formData.name,
      title: formData.title,
      category: formData.category as "Business" | "Tech" | "Creators",
      image_url: formData.image_url || undefined,
      price: parseFloat(formData.price),
      bio: formData.bio,
      full_bio: formData.full_bio,
      expertise: formData.expertise.split(",").map((s) => s.trim()).filter(Boolean),
      languages: formData.languages.split(",").map((s) => s.trim()).filter(Boolean),
      availability: formData.availability,
      experience: formData.experience,
      education: formData.education,
      certifications: formData.certifications
        ? formData.certifications.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
    };

    // Validate input
    const validation = validateData(mentorProfileSchema, dataToValidate);
    if (!validation.success) {
      logger.warn("Validation failed for mentor profile", { errors: validation.errors });
      toast.error(`Validation error: ${validation.errors[0]}`);
      return;
    }

    const mentorData = {
      user_id: user.id,
      ...validation.data,
      image_url: validation.data.image_url || null,
      timezone: formData.timezone?.trim() || null,
    };

    if (editingMentor) {
      const { error } = await supabase
        .from("mentor_profiles")
        .update(mentorData)
        .eq("id", editingMentor.id);
      if (error) {
        logger.error("Failed to update mentor", error, { mentorId: editingMentor.id });
        toast.error(error.message);
        return;
      }
      toast.success("Mentor updated");
    } else {
      const { error } = await supabase.from("mentor_profiles").insert(mentorData);
      if (error) {
        logger.error("Failed to create mentor", error);
        toast.error(error.message);
        return;
      }
      toast.success("Mentor created");
    }
    setShowDialog(false);
    setEditingMentor(null);
    resetForm();
    fetchMentors();
  };

  const handleEdit = (mentor: MentorProfile) => {
    setEditingMentor(mentor);
    setFormData({
      name: mentor.name,
      title: mentor.title,
      category: mentor.category,
      image_url: (mentor as any).image_url || "",
      price: String(mentor.price),
      bio: mentor.bio,
      full_bio: mentor.full_bio,
      expertise: Array.isArray((mentor as any).expertise) ? (mentor as any).expertise.join(", ") : "",
      languages: Array.isArray((mentor as any).languages) ? (mentor as any).languages.join(", ") : "",
      availability: (mentor as any).availability || "Available this week",
      experience: (mentor as any).experience || "",
      education: (mentor as any).education || "",
      certifications: Array.isArray((mentor as any).certifications)
        ? (mentor as any).certifications.join(", ")
        : "",
      timezone: (mentor as any).timezone || "",
    });
    setShowDialog(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this mentor profile?")) return;
    const { error } = await supabase.from("mentor_profiles").delete().eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Mentor deleted");
    fetchMentors();
  };

  const handleChangeToLearner = async (userId: string) => {
    if (!confirm("Change this user's role to learner? They will see the learner dashboard. Mentor profile will remain; remove it separately if needed.")) return;
    const roles = rolesByUser[userId] ?? [];
    const mentorRole = roles.find((r) => r.role === "mentor");
    const hasLearner = roles.some((r) => r.role === "learner");
    if (mentorRole) {
      const { error: delErr } = await supabase.from("user_roles").delete().eq("id", mentorRole.id);
      if (delErr) {
        toast.error(delErr.message);
        return;
      }
    }
    if (!hasLearner) {
      const { error: insErr } = await supabase.from("user_roles").insert({ user_id: userId, role: "learner" });
      if (insErr) {
        toast.error(insErr.message);
        return;
      }
    }
    toast.success("Role set to learner; user will see learner dashboard.");
    fetchMentors();
  };

  const resetForm = () => {
    setFormData({
      name: "",
      title: "",
      category: "Business",
      image_url: "",
      price: "",
      bio: "",
      full_bio: "",
      expertise: "",
      languages: "",
      availability: "Available this week",
      experience: "",
      education: "",
      certifications: "",
      timezone: "",
    });
  };

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Mentors</h1>
            <p className="text-sm text-muted-foreground">Manage mentor profiles and visibility</p>
          </div>
          <Dialog
            open={showDialog}
            onOpenChange={(open) => {
              setShowDialog(open);
              if (!open) {
                setEditingMentor(null);
                resetForm();
              }
            }}
          >
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add mentor
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingMentor ? "Edit mentor" : "Add mentor"}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Title *</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Category *</Label>
                    <Select
                      value={formData.category}
                      onValueChange={(v) => setFormData({ ...formData, category: v })}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Business">Business</SelectItem>
                        <SelectItem value="Tech">Tech</SelectItem>
                        <SelectItem value="Creators">Creators</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Price (USD) *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div>
                  <Label>Image URL</Label>
                  <Input
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Short bio *</Label>
                  <Textarea
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    rows={2}
                    required
                  />
                </div>
                <div>
                  <Label>Full bio *</Label>
                  <Textarea
                    value={formData.full_bio}
                    onChange={(e) => setFormData({ ...formData, full_bio: e.target.value })}
                    rows={4}
                    required
                  />
                </div>
                <div>
                  <Label>Expertise (comma-separated) *</Label>
                  <Input
                    value={formData.expertise}
                    onChange={(e) => setFormData({ ...formData, expertise: e.target.value })}
                    placeholder="e.g. Strategy, Fundraising"
                    required
                  />
                </div>
                <div>
                  <Label>Languages (comma-separated) *</Label>
                  <Input
                    value={formData.languages}
                    onChange={(e) => setFormData({ ...formData, languages: e.target.value })}
                    placeholder="e.g. English, Spanish"
                    required
                  />
                </div>
                <div>
                  <Label>Availability *</Label>
                  <Input
                    value={formData.availability}
                    onChange={(e) => setFormData({ ...formData, availability: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Experience *</Label>
                  <Input
                    value={formData.experience}
                    onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Education *</Label>
                  <Input
                    value={formData.education}
                    onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Certifications (comma-separated)</Label>
                  <Input
                    value={formData.certifications}
                    onChange={(e) => setFormData({ ...formData, certifications: e.target.value })}
                  />
                </div>
                <div>
                  <TimezoneSelect
                    value={formData.timezone}
                    onValueChange={(v) => setFormData({ ...formData, timezone: v })}
                    label="Time zone"
                    placeholder="Select mentor time zone"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => { setShowDialog(false); setEditingMentor(null); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit">{editingMentor ? "Update" : "Create"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          {loading ? (
            <CardContent className="py-12 text-center text-muted-foreground">Loading mentors…</CardContent>
          ) : mentors.length === 0 ? (
            <CardContent className="py-12 text-center text-muted-foreground">
              No mentors yet. Add one to get started.
            </CardContent>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Added</TableHead>
                  <TableHead className="w-[100px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {mentors.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">{m.name}</TableCell>
                    <TableCell>{m.title}</TableCell>
                    <TableCell>{m.category}</TableCell>
                    <TableCell className="text-right">${Number(m.price).toFixed(0)}</TableCell>
                    <TableCell>
                      <span className={m.is_active !== false ? "text-green-600" : "text-muted-foreground"}>
                        {m.is_active !== false ? "Active" : "Inactive"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {m.created_at ? new Date(m.created_at).toLocaleDateString() : "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        {m.id && (
                          <Button variant="ghost" size="icon" asChild>
                            <a href={`/mentors/${m.id}`} target="_blank" rel="noopener noreferrer" title="View public profile">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(m)} title="Edit">
                          <Edit className="h-4 w-4" />
                        </Button>
                        {m.user_id && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleChangeToLearner(m.user_id!)}
                            title="Change role to learner (removes mentor role; user will see learner dashboard)"
                          >
                            <UserMinus className="h-4 w-4" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(m.id)} title="Delete" className="text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  );
}
