import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProfilePhotoUpload } from "@/components/ProfilePhotoUpload";
import { TimezoneSelect } from "@/components/TimezoneSelect";
import { useState } from "react";

interface MentorProfile {
  id: string;
  name: string;
  title: string;
  category: string;
  bio: string;
  full_bio: string;
  price: number;
  expertise: string[];
  languages: string[];
  availability: string;
  experience: string;
  education: string;
  certifications: string[] | null;
  image_url: string | null;
  username: string | null;
  timezone?: string | null;
}

interface MentorProfileEditorProps {
  profile: MentorProfile | null;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  userId: string;
}

export const MentorProfileEditor = ({ profile, onSubmit, userId }: MentorProfileEditorProps) => {
  const [imageUrl, setImageUrl] = useState(profile?.image_url || "");
  const [timezone, setTimezone] = useState(profile?.timezone || "");

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    const formData = new FormData(e.currentTarget);
    formData.set("image_url", imageUrl);
    formData.set("timezone", timezone);
    onSubmit(e);
  };

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6">
        <CardTitle className="text-lg sm:text-xl">Mentor Profile Settings</CardTitle>
        <CardDescription className="text-sm">Update your mentor profile information</CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0">
        <form onSubmit={handleFormSubmit} className="space-y-4 sm:space-y-6">
          {/* Profile Photo Upload */}
          <div className="flex justify-center pb-4 sm:pb-6 border-b">
            <ProfilePhotoUpload
              currentPhotoUrl={imageUrl}
              onPhotoUpdate={setImageUrl}
              userId={userId}
              fallbackText={profile?.name?.charAt(0).toUpperCase() || "M"}
            />
          </div>
          
          <input type="hidden" name="image_url" value={imageUrl} />
          <input type="hidden" name="timezone" value={timezone} />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="name" className="text-xs sm:text-sm">Full Name*</Label>
              <Input
                id="name"
                name="name"
                defaultValue={profile?.name || ""}
                placeholder="John Doe"
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>
            
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="username" className="text-xs sm:text-sm">Username (for shop URL)</Label>
              <Input
                id="username"
                name="username"
                defaultValue={profile?.username || ""}
                placeholder="johndoe"
                title="Only lowercase letters, numbers, hyphens and underscores"
                className="h-9 sm:h-10 text-sm"
                onInput={(e) => {
                  const target = e.target as HTMLInputElement;
                  target.value = target.value.toLowerCase().replace(/[^a-z0-9_-]/g, "");
                }}
              />
              <p className="text-[10px] sm:text-xs text-muted-foreground break-all">
                Shop URL: /shop/{profile?.username || "your-username"}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="title" className="text-xs sm:text-sm">Professional Title*</Label>
              <Input
                id="title"
                name="title"
                defaultValue={profile?.title || ""}
                placeholder="Senior Software Engineer"
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>

            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="category" className="text-xs sm:text-sm">Category*</Label>
              <Select name="category" defaultValue={profile?.category || ""} required>
                <SelectTrigger className="h-9 sm:h-10 text-sm">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Business">Business</SelectItem>
                  <SelectItem value="Tech">Tech</SelectItem>
                  <SelectItem value="Creators">Creators</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="price" className="text-xs sm:text-sm">Hourly Rate ($)*</Label>
            <Input
              id="price"
              name="price"
              type="number"
              min="0"
              step="0.01"
              defaultValue={profile?.price || ""}
              placeholder="100"
              required
              className="h-9 sm:h-10 text-sm"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <TimezoneSelect
              value={timezone}
              onValueChange={setTimezone}
              label="Time zone"
              placeholder="Select your time zone (for availability and sessions)"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="bio" className="text-xs sm:text-sm">Short Bio* (Max 200 characters)</Label>
            <Textarea
              id="bio"
              name="bio"
              defaultValue={profile?.bio || ""}
              placeholder="A brief introduction about yourself..."
              maxLength={200}
              rows={2}
              required
              className="text-sm min-h-[60px]"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="full_bio" className="text-xs sm:text-sm">Full Bio*</Label>
            <Textarea
              id="full_bio"
              name="full_bio"
              defaultValue={profile?.full_bio || ""}
              placeholder="Tell your story, share your expertise and what makes you unique..."
              rows={4}
              required
              className="text-sm min-h-[100px] sm:min-h-[150px]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="expertise" className="text-xs sm:text-sm">Areas of Expertise* (comma-separated)</Label>
              <Input
                id="expertise"
                name="expertise"
                defaultValue={profile?.expertise?.join(", ") || ""}
                placeholder="JavaScript, React, Node.js"
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>

            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="languages" className="text-xs sm:text-sm">Languages* (comma-separated)</Label>
              <Input
                id="languages"
                name="languages"
                defaultValue={profile?.languages?.join(", ") || ""}
                placeholder="English, Spanish, French"
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="availability" className="text-xs sm:text-sm">Availability*</Label>
            <Input
              id="availability"
              name="availability"
              defaultValue={profile?.availability || ""}
              placeholder="Mon-Fri, 9 AM - 5 PM EST"
              required
              className="h-9 sm:h-10 text-sm"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="experience" className="text-xs sm:text-sm">Professional Experience*</Label>
            <Textarea
              id="experience"
              name="experience"
              defaultValue={profile?.experience || ""}
              placeholder="10+ years in software development..."
              rows={3}
              required
              className="text-sm min-h-[80px]"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="education" className="text-xs sm:text-sm">Education*</Label>
            <Textarea
              id="education"
              name="education"
              defaultValue={profile?.education || ""}
              placeholder="BS in Computer Science from MIT"
              rows={2}
              required
              className="text-sm min-h-[60px]"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="certifications" className="text-xs sm:text-sm">Certifications (comma-separated)</Label>
            <Input
              id="certifications"
              name="certifications"
              defaultValue={profile?.certifications?.join(", ") || ""}
              placeholder="AWS Certified, PMP, Google Analytics"
              className="h-9 sm:h-10 text-sm"
            />
          </div>

          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="image_url" className="text-xs sm:text-sm">Profile Image URL</Label>
            <Input
              id="image_url"
              name="image_url"
              type="url"
              defaultValue={profile?.image_url || ""}
              placeholder="https://example.com/your-photo.jpg"
              className="h-9 sm:h-10 text-sm"
            />
          </div>

          <Button type="submit" className="w-full h-10 sm:h-11 text-sm sm:text-base">
            {profile ? "Update Profile" : "Create Profile"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
