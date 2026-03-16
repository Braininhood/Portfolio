import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ProfilePhotoUpload } from "@/components/ProfilePhotoUpload";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import { normalizeProfileFromDb } from "@/utils/profile";

const SKILL_LEVELS = ["beginner", "intermediate", "advanced"] as const;

export default function Profile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [userId, setUserId] = useState<string>("");
  const [profile, setProfile] = useState({
    full_name: "",
    avatar_url: "",
    goals: "",
    interests: [] as string[],
    skill_level: "",
    preferred_language: "",
  });

  useEffect(() => {
    checkUser();
  }, []);

  const checkUser = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) {
      navigate("/auth");
      return;
    }

    setUserId(user.id);
    loadProfile(user.id);
  };

  const loadProfile = async (id: string) => {
    try {
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", id)
        .maybeSingle();

      if (error) throw error;

      if (data && data.id) {
        const normalized = normalizeProfileFromDb(data as Record<string, unknown> & { id: string });
        setProfile({
          full_name: normalized.full_name ?? "",
          avatar_url: normalized.avatar_url ?? "",
          goals: normalized.goals ?? "",
          interests: normalized.interests,
          skill_level: normalized.skill_level ?? "",
          preferred_language: normalized.preferred_language ?? "",
        });
      } else {
        // No profile row (e.g. user created via SQL, trigger didn't run, or new project)
        const { data: { user } } = await supabase.auth.getUser();
        const fullName = user?.user_metadata?.full_name ?? user?.email?.split("@")[0] ?? "";
        const { error: insertError } = await supabase.from("profiles").upsert(
          { id, full_name: fullName },
          { onConflict: "id" }
        );
        if (insertError) {
          console.error("Error creating profile:", insertError);
          toast.error("Could not create profile. Check console.");
        } else {
          setProfile((prev) => ({ ...prev, full_name: fullName }));
        }
      }
    } catch (error) {
      console.error("Error loading profile:", error);
      toast.error("Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoUpdate = async (url: string) => {
    try {
      const { error } = await supabase
        .from("profiles")
        .update({ avatar_url: url })
        .eq("id", userId);

      if (error) throw error;

      setProfile({ ...profile, avatar_url: url });
    } catch (error) {
      console.error("Error updating photo:", error);
      toast.error("Failed to update profile photo");
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      const skillLevel = profile.skill_level?.trim().toLowerCase();
      const validSkillLevel = SKILL_LEVELS.includes(skillLevel as typeof SKILL_LEVELS[number])
        ? skillLevel
        : null;

      const { error } = await supabase
        .from("profiles")
        .update({
          full_name: profile.full_name || null,
          goals: profile.goals || null,
          interests: profile.interests,
          skill_level: validSkillLevel,
          preferred_language: profile.preferred_language || null,
        })
        .eq("id", userId);

      if (error) throw error;

      toast.success("Profile updated successfully");
    } catch (error) {
      console.error("Error saving profile:", error);
      toast.error("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8 pt-24">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>My Profile</CardTitle>
            <CardDescription>
              Manage your profile information and preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <ProfilePhotoUpload
              currentPhotoUrl={profile.avatar_url}
              onPhotoUpdate={handlePhotoUpdate}
              userId={userId}
              fallbackText={profile.full_name?.charAt(0).toUpperCase() || "U"}
            />

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  value={profile.full_name}
                  onChange={(e) =>
                    setProfile({ ...profile, full_name: e.target.value })
                  }
                  placeholder="Enter your full name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="skill_level">Skill Level</Label>
                <Select
                  value={profile.skill_level || "none"}
                  onValueChange={(v) =>
                    setProfile({ ...profile, skill_level: v === "none" ? "" : v })
                  }
                >
                  <SelectTrigger id="skill_level">
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Not set</SelectItem>
                    {SKILL_LEVELS.map((level) => (
                      <SelectItem key={level} value={level}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="goals">Learning Goals</Label>
                <Textarea
                  id="goals"
                  value={profile.goals}
                  onChange={(e) =>
                    setProfile({ ...profile, goals: e.target.value })
                  }
                  placeholder="What do you want to achieve?"
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="preferred_language">Preferred Language</Label>
                <Input
                  id="preferred_language"
                  value={profile.preferred_language}
                  onChange={(e) =>
                    setProfile({ ...profile, preferred_language: e.target.value })
                  }
                  placeholder="e.g., English"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Button onClick={handleSave} disabled={saving} className="flex-1">
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
              <Button variant="outline" onClick={() => navigate("/")} className="flex-1">
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
