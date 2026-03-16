import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Upload, Sparkles, Bot, Mic, Image as ImageIcon, X, Check, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface AvatarCreationWizardProps {
  mentorId: string;
  existingAvatar?: any;
  onSuccess?: () => void;
}

export const AvatarCreationWizard = ({ mentorId, existingAvatar, onSuccess }: AvatarCreationWizardProps) => {
  const [step, setStep] = useState(1);
  const [isTraining, setIsTraining] = useState(false);
  const [photos, setPhotos] = useState<string[]>(existingAvatar?.photo_urls || []);
  const [voiceSample, setVoiceSample] = useState<string | null>(existingAvatar?.voice_sample_url || null);
  const [avatarName, setAvatarName] = useState(existingAvatar?.avatar_name || "");
  const [bioSummary, setBioSummary] = useState(existingAvatar?.bio_summary || "");
  const [expertiseAreas, setExpertiseAreas] = useState<string[]>(existingAvatar?.expertise_areas || []);
  const [personalityTraits, setPersonalityTraits] = useState<string[]>(existingAvatar?.personality_traits || []);
  const [expertiseInput, setExpertiseInput] = useState("");
  const [personalityInput, setPersonalityInput] = useState("");

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || photos.length >= 5) {
      toast.error("Maximum 5 photos allowed");
      return;
    }

    const newPhotos: string[] = [];
    
    for (let i = 0; i < Math.min(files.length, 5 - photos.length); i++) {
      const file = files[i];
      const fileExt = file.name.split('.').pop();
      const fileName = `${mentorId}-${Date.now()}-${i}.${fileExt}`;
      const filePath = `${fileName}`;

      const { error: uploadError, data } = await supabase.storage
        .from('avatar-photos')
        .upload(filePath, file);

      if (uploadError) {
        console.error("Upload error:", uploadError);
        toast.error(`Failed to upload ${file.name}`);
        continue;
      }

      const { data: { publicUrl } } = supabase.storage
        .from('avatar-photos')
        .getPublicUrl(filePath);

      newPhotos.push(publicUrl);
    }

    setPhotos([...photos, ...newPhotos]);
    toast.success(`${newPhotos.length} photo(s) uploaded`);
  };

  const handleVoiceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileExt = file.name.split('.').pop();
    const fileName = `${mentorId}-voice.${fileExt}`;
    const filePath = `${fileName}`;

    const { error: uploadError } = await supabase.storage
      .from('avatar-voices')
      .upload(filePath, file, { upsert: true });

    if (uploadError) {
      toast.error("Failed to upload voice sample");
      return;
    }

    const { data: { publicUrl } } = supabase.storage
      .from('avatar-voices')
      .getPublicUrl(filePath);

    setVoiceSample(publicUrl);
    toast.success("Voice sample uploaded");
  };

  const removePhoto = (index: number) => {
    setPhotos(photos.filter((_, i) => i !== index));
  };

  const addExpertise = () => {
    if (expertiseInput.trim() && !expertiseAreas.includes(expertiseInput.trim())) {
      setExpertiseAreas([...expertiseAreas, expertiseInput.trim()]);
      setExpertiseInput("");
    }
  };

  const addPersonality = () => {
    if (personalityInput.trim() && !personalityTraits.includes(personalityInput.trim())) {
      setPersonalityTraits([...personalityTraits, personalityInput.trim()]);
      setPersonalityInput("");
    }
  };

  const handleCreateAvatar = async () => {
    if (!avatarName || !bioSummary || photos.length === 0 || expertiseAreas.length === 0) {
      toast.error("Please complete all required fields");
      return;
    }

    setIsTraining(true);

    try {
      // Create or update avatar record
      const avatarData = {
        mentor_id: mentorId,
        avatar_name: avatarName,
        bio_summary: bioSummary,
        expertise_areas: expertiseAreas,
        personality_traits: personalityTraits,
        photo_urls: photos,
        voice_sample_url: voiceSample,
        status: 'draft'
      };

      const { data: avatar, error: avatarError } = existingAvatar
        ? await supabase
            .from('mentor_avatars')
            .update(avatarData)
            .eq('id', existingAvatar.id)
            .select()
            .single()
        : await supabase
            .from('mentor_avatars')
            .insert(avatarData)
            .select()
            .single();

      if (avatarError) throw avatarError;

      // Call train-avatar edge function
      const { data, error } = await supabase.functions.invoke('train-avatar', {
        body: {
          avatarId: avatar.id,
          mentorId,
          bioSummary,
          expertiseAreas,
          personalityTraits
        }
      });

      if (error) throw error;

      toast.success("AI Avatar created successfully!", {
        description: "Your avatar is now ready to interact with users."
      });

      onSuccess?.();
    } catch (error) {
      console.error("Error creating avatar:", error);
      toast.error("Failed to create avatar", {
        description: error instanceof Error ? error.message : "Please try again"
      });
    } finally {
      setIsTraining(false);
    }
  };

  const canProceedToStep2 = photos.length > 0;
  const canProceedToStep3 = avatarName && bioSummary && expertiseAreas.length > 0;

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-4">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              s === step ? 'bg-accent text-accent-foreground' : 
              s < step ? 'bg-primary text-primary-foreground' : 
              'bg-muted text-muted-foreground'
            }`}>
              {s < step ? <Check size={20} /> : s}
            </div>
            {s < 3 && <div className="w-12 h-0.5 bg-border" />}
          </div>
        ))}
      </div>

      {/* Step 1: Upload Media */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="text-accent" />
              Upload Photos & Voice
            </CardTitle>
            <CardDescription>
              Upload 1-5 photos and an optional voice sample to personalize your avatar
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Photos */}
            <div className="space-y-3">
              <Label>Photos ({photos.length}/5) *</Label>
              <div className="grid grid-cols-3 gap-4">
                {photos.map((photo, index) => (
                  <div key={index} className="relative group">
                    <img src={photo} alt={`Avatar ${index + 1}`} className="w-full aspect-square object-cover rounded-lg" />
                    <Button
                      size="sm"
                      variant="destructive"
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => removePhoto(index)}
                    >
                      <X size={16} />
                    </Button>
                  </div>
                ))}
                {photos.length < 5 && (
                  <label className="border-2 border-dashed border-border rounded-lg aspect-square flex flex-col items-center justify-center cursor-pointer hover:border-accent transition-colors">
                    <Upload className="text-muted-foreground mb-2" />
                    <span className="text-sm text-muted-foreground">Upload</span>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handlePhotoUpload}
                    />
                  </label>
                )}
              </div>
            </div>

            {/* Voice Sample */}
            <div className="space-y-3">
              <Label>Voice Sample (Optional)</Label>
              <div className="flex items-center gap-4">
                {voiceSample ? (
                  <Badge variant="secondary" className="flex items-center gap-2">
                    <Mic size={16} />
                    Voice sample uploaded
                  </Badge>
                ) : (
                  <label className="cursor-pointer">
                    <Button variant="outline" asChild>
                      <span>
                        <Mic className="mr-2" size={18} />
                        Upload Voice
                      </span>
                    </Button>
                    <input
                      type="file"
                      accept="audio/*"
                      className="hidden"
                      onChange={handleVoiceUpload}
                    />
                  </label>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                Upload a short voice recording (30-60 seconds) for voice cloning
              </p>
            </div>

            <Button 
              className="w-full" 
              onClick={() => setStep(2)}
              disabled={!canProceedToStep2}
            >
              Continue to Profile
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Profile Information */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="text-accent" />
              Avatar Profile
            </CardTitle>
            <CardDescription>
              Define your avatar's personality and expertise
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Avatar Name *</Label>
              <Input
                placeholder="e.g., Sarah's AI Assistant"
                value={avatarName}
                onChange={(e) => setAvatarName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Bio Summary *</Label>
              <Textarea
                placeholder="Brief description of your expertise and what your avatar can help with..."
                value={bioSummary}
                onChange={(e) => setBioSummary(e.target.value)}
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label>Expertise Areas *</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add an area of expertise"
                  value={expertiseInput}
                  onChange={(e) => setExpertiseInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addExpertise())}
                />
                <Button onClick={addExpertise}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {expertiseAreas.map((area, index) => (
                  <Badge key={index} variant="secondary" className="flex items-center gap-1">
                    {area}
                    <X 
                      size={14} 
                      className="cursor-pointer" 
                      onClick={() => setExpertiseAreas(expertiseAreas.filter((_, i) => i !== index))}
                    />
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Personality Traits (Optional)</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., friendly, professional, enthusiastic"
                  value={personalityInput}
                  onChange={(e) => setPersonalityInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPersonality())}
                />
                <Button onClick={addPersonality}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {personalityTraits.map((trait, index) => (
                  <Badge key={index} variant="outline" className="flex items-center gap-1">
                    {trait}
                    <X 
                      size={14} 
                      className="cursor-pointer" 
                      onClick={() => setPersonalityTraits(personalityTraits.filter((_, i) => i !== index))}
                    />
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                Back
              </Button>
              <Button 
                className="flex-1" 
                onClick={() => setStep(3)}
                disabled={!canProceedToStep3}
              >
                Review & Create
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review & Create */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="text-accent" />
              Review & Train Avatar
            </CardTitle>
            <CardDescription>
              Review your avatar configuration before training
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
              <div>
                <p className="text-sm font-semibold mb-1">Photos</p>
                <p className="text-sm text-muted-foreground">{photos.length} uploaded</p>
              </div>
              <div>
                <p className="text-sm font-semibold mb-1">Voice Sample</p>
                <p className="text-sm text-muted-foreground">{voiceSample ? 'Yes' : 'No'}</p>
              </div>
              <div>
                <p className="text-sm font-semibold mb-1">Avatar Name</p>
                <p className="text-sm text-muted-foreground">{avatarName}</p>
              </div>
              <div>
                <p className="text-sm font-semibold mb-1">Expertise Areas</p>
                <p className="text-sm text-muted-foreground">{expertiseAreas.length} areas</p>
              </div>
            </div>

            <div className="p-4 bg-accent/10 border border-accent/20 rounded-lg">
              <p className="text-sm font-semibold mb-2">Bio Summary:</p>
              <p className="text-sm text-muted-foreground">{bioSummary}</p>
            </div>

            {personalityTraits.length > 0 && (
              <div>
                <p className="text-sm font-semibold mb-2">Personality:</p>
                <div className="flex flex-wrap gap-2">
                  {personalityTraits.map((trait, index) => (
                    <Badge key={index} variant="outline">{trait}</Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                Back
              </Button>
              <Button 
                variant="hero"
                className="flex-1" 
                onClick={handleCreateAvatar}
                disabled={isTraining}
              >
                {isTraining ? (
                  <>
                    <Loader2 className="mr-2 animate-spin" size={18} />
                    Training Avatar...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2" size={18} />
                    Train Avatar
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
