import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { AvatarChatInterface } from "@/components/AvatarChatInterface";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

const AvatarChat = () => {
  const { avatarId } = useParams();
  const navigate = useNavigate();
  const [avatar, setAvatar] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
    if (avatarId) {
      fetchAvatar();
    }
  }, [avatarId]);

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      toast.error("Please sign in to chat with avatars");
      navigate("/auth");
    }
  };

  const fetchAvatar = async () => {
    if (!avatarId) return;
    setLoading(true);
    const { data, error } = await supabase
      .from('mentor_avatars')
      .select('*, mentor_profiles(*)')
      .eq('id', avatarId)
      .eq('status', 'ready')
      .single();

    if (error || !data) {
      console.error("Error fetching avatar:", error);
      toast.error("Avatar not found or not available");
      navigate("/mentors");
      return;
    }

    setAvatar(data);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-32">
          <p className="text-center">Loading...</p>
        </div>
      </div>
    );
  }

  if (!avatar) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-32 text-center">
          <h1 className="text-2xl font-bold mb-4">Avatar not found</h1>
          <Button onClick={() => navigate("/mentors")}>Back to Mentors</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <Navbar />
      <main className="flex-1 min-h-0 overflow-hidden flex flex-col">
        <div className="container mx-auto px-4 py-6 flex-1 flex flex-col min-h-0 overflow-hidden">
          <Button
            variant="ghost"
            onClick={() => navigate(`/mentors/${avatar.mentor_id}`)}
            className="mb-4 shrink-0"
          >
            <ArrowLeft size={20} className="mr-2" />
            Back to {avatar.mentor_profiles?.name}'s Profile
          </Button>

          <div className="max-w-4xl mx-auto flex-1 flex flex-col min-h-0 overflow-hidden w-full">
            <div className="mb-4 shrink-0">
              <h1 className="text-2xl md:text-3xl font-bold mb-1">
                Chat with {avatar.avatar_name}
              </h1>
              <p className="text-sm text-muted-foreground">
                AI-powered assistant by {avatar.mentor_profiles?.name}
              </p>
            </div>

            <div className="flex-1 min-h-0 overflow-hidden">
              <AvatarChatInterface
                avatarId={avatarId!}
                mentorId={avatar.mentor_id}
                fillContainer
              />
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default AvatarChat;
