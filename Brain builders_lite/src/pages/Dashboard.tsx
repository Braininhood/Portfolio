import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useUnreadMessages } from "@/hooks/useUnreadMessages";
import { useUserRole } from "@/hooks/useUserRole";
import Navbar from "@/components/Navbar";
import { RecommendationsCard } from "@/components/RecommendationsCard";
import { ConversationsList } from "@/components/ConversationsList";
import { BookingCalendarView } from "@/components/BookingCalendarView";
import { GoogleCalendarSync } from "@/components/GoogleCalendarSync";
import { NotificationSettings } from "@/components/NotificationSettings";
import { PurchasedProductCard } from "@/components/PurchasedProductCard";
import { DashboardQuestionsTab } from "@/components/DashboardQuestionsTab";
import { User, Session } from "@supabase/supabase-js";
import { Settings, ShoppingBag, MessageCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { normalizeProfileFromDb } from "@/utils/profile";
import { TimezoneSelect } from "@/components/TimezoneSelect";

interface Profile {
  id: string;
  full_name: string | null;
  interests: string[] | null;
  skill_level: string | null;
  goals: string | null;
  preferred_language: string | null;
  timezone: string | null;
}

interface Purchase {
  id: string;
  amount: number;
  status: string;
  created_at: string;
  product: {
    id: string;
    title: string;
    description: string;
    file_type: string;
    preview_image_url: string | null;
    mentor_id: string;
    mentor_profiles: {
      name: string;
      image_url: string | null;
    } | null;
  } | null;
}

const Dashboard = () => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab") || "overview";
  const [activeTab, setActiveTab] = useState(tabFromUrl);
  const [profileTimezone, setProfileTimezone] = useState(profile?.timezone ?? "");
  useEffect(() => { setActiveTab(tabFromUrl); }, [tabFromUrl]);
  useEffect(() => { setProfileTimezone(profile?.timezone ?? ""); }, [profile?.timezone]);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailUpdating, setEmailUpdating] = useState(false);
  const [passwordUpdating, setPasswordUpdating] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { unreadCount } = useUnreadMessages(user);
  const { isMentor, loading: roleLoading } = useUserRole();
  const loadUserDataRunRef = useRef(false);
  const recommendationsInFlightRef = useRef(false);
  const hasShown401ToastRef = useRef(false);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        if (!session?.user) {
          navigate("/auth");
          loadUserDataRunRef.current = false;
        } else if (!loadUserDataRunRef.current) {
          loadUserDataRunRef.current = true;
          loadUserData(session.user.id);
        }
      }
    );

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (!session?.user) {
        navigate("/auth");
      } else if (!loadUserDataRunRef.current) {
        loadUserDataRunRef.current = true;
        loadUserData(session.user.id);
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  useEffect(() => {
    if (!session?.user || roleLoading || !isMentor) return;
    // User has both roles and chose learner view – stay on learner dashboard
    const preferred = localStorage.getItem("gcreators_dashboard_view");
    if (preferred === "learner") return;
    navigate("/mentor/dashboard", { replace: true });
  }, [session?.user, roleLoading, isMentor, navigate]);

  const loadUserData = async (userId: string) => {
    setLoading(true);

    const { data: profileData, error: profileError } = await supabase
      .from("profiles")
      .select("*")
      .eq("id", userId)
      .maybeSingle();

    if (profileError) {
      console.error("Error loading profile:", profileError);
    }

    let resolvedProfile: Profile | null = null;
    if (profileData && profileData.id) {
      resolvedProfile = normalizeProfileFromDb(profileData as Record<string, unknown> & { id: string }) as Profile;
    } else {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      const fullName = authUser?.user_metadata?.full_name ?? authUser?.email?.split("@")[0] ?? "";
      const { error: upsertErr } = await supabase.from("profiles").upsert(
        { id: userId, full_name: fullName },
        { onConflict: "id" }
      );
      if (!upsertErr) {
        const { data: refetched } = await supabase.from("profiles").select("*").eq("id", userId).maybeSingle();
        if (refetched?.id) {
          resolvedProfile = normalizeProfileFromDb(refetched as Record<string, unknown> & { id: string }) as Profile;
        } else {
          resolvedProfile = { id: userId, full_name: fullName, interests: [], skill_level: null, goals: null, preferred_language: null, timezone: null };
        }
      } else {
        resolvedProfile = { id: userId, full_name: fullName, interests: [], skill_level: null, goals: null, preferred_language: null, timezone: null };
      }
    }
    setProfile(resolvedProfile);

    // Load purchases with mentor info
    const { data: purchasesData } = await supabase
      .from("product_purchases")
      .select(`
        id,
        amount,
        status,
        created_at,
        product:mentor_products(
          id,
          title,
          description,
          file_type,
          preview_image_url,
          mentor_id,
          mentor_profiles(
            name,
            image_url
          )
        )
      `)
      .eq("buyer_id", userId)
      .eq("status", "completed")
      .order("created_at", { ascending: false });
    
    setPurchases((purchasesData as unknown as Purchase[]) || []);
    setLoading(false);

    // Load recommendations if profile is complete (use resolved profile with normalized interests)
    if (resolvedProfile?.interests?.length && resolvedProfile?.skill_level) {
      loadRecommendations(userId);
    }
  };

  const loadRecommendations = async (userId: string, retried = false) => {
    if (recommendationsInFlightRef.current && !retried) return;
    recommendationsInFlightRef.current = true;
    setRecommendationsLoading(true);

    try {
      if (retried) {
        await supabase.auth.refreshSession();
      }
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;

      if (!accessToken) {
        throw Object.assign(new Error("Authentication required"), { status: 401 });
      }

      const { data, error } = await supabase.functions.invoke("recommend-mentors", {
        body: { userId, access_token: accessToken },
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (error) {
        const err = error as { status?: number; context?: { body?: { error?: string } } };
        if (err.status === 401 && !retried) {
          setRecommendationsLoading(false);
          recommendationsInFlightRef.current = false;
          return loadRecommendations(userId, true);
        }
        throw err;
      }

      if (data?.recommendations) {
        setRecommendations(data.recommendations);
      }
    } catch (error: any) {
      const status = error?.status ?? error?.statusCode;
      const msg = error?.message ?? "";
      const errName = error?.name ?? "";

      // Silently fail for Edge Function fetch/network errors - recommendations are optional
      const isFetchError =
        errName === "FunctionsFetchError" ||
        errName === "FunctionsError" ||
        msg.includes("Failed to send a request") ||
        msg.includes("Edge Function");
      if (isFetchError) {
        setRecommendations([]);
        setRecommendationsLoading(false);
        recommendationsInFlightRef.current = false;
        return;
      }
      console.error("Recommendations error:", error);
      const bodyError = error?.context?.body?.error ?? "";

      if (status === 401 || msg.includes("Authentication required")) {
        if (!hasShown401ToastRef.current) {
          hasShown401ToastRef.current = true;
          toast({
            title: "Session expired",
            description: bodyError || "Please sign out and sign in again to get recommendations.",
            variant: "destructive",
          });
        }
      } else if (msg.includes("Rate limit")) {
        toast({
          title: "Rate Limit",
          description: "Too many requests. Please try again in a moment.",
          variant: "destructive",
        });
      } else if (msg.includes("credits") || msg.includes("Credits")) {
        toast({
          title: "Credits Exhausted",
          description: "AI credits exhausted. Please add credits to continue.",
          variant: "destructive",
        });
      } else if (!msg.includes("401") && !msg.includes("Authentication")) {
        toast({
          title: "Recommendations unavailable",
          description: "We couldn't load recommendations right now. Please try again later.",
          variant: "destructive",
        });
      }
    } finally {
      recommendationsInFlightRef.current = false;
      setRecommendationsLoading(false);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!user) return;

    const formData = new FormData(e.currentTarget);
    const selectedInterests = formData.getAll("interests").filter((v): v is string => typeof v === 'string');

    const { error } = await supabase
      .from("profiles")
      .update({
        full_name: formData.get("full_name")?.toString(),
        interests: selectedInterests,
        skill_level: formData.get("skill_level")?.toString(),
        goals: formData.get("goals")?.toString(),
        timezone: formData.get("timezone")?.toString().trim() || null,
      })
      .eq("id", user.id);

    if (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
      loadUserData(user.id);
    }
  };

  const handleUpdateEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !newEmail.trim()) return;
    setEmailUpdating(true);
    const { error } = await supabase.auth.updateUser({ email: newEmail.trim() });
    setEmailUpdating(false);
    if (error) {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    } else {
      setNewEmail("");
      toast({
        title: "Verification sent",
        description: "Check your new email and click the confirmation link to complete the change.",
      });
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !newPassword || !confirmPassword) {
      toast({ title: "Error", description: "Fill in both password fields.", variant: "destructive" });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({ title: "Error", description: "Passwords do not match.", variant: "destructive" });
      return;
    }
    if (newPassword.length < 6) {
      toast({ title: "Error", description: "Password must be at least 6 characters.", variant: "destructive" });
      return;
    }
    setPasswordUpdating(true);
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    setPasswordUpdating(false);
    if (error) {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    } else {
      setNewPassword("");
      setConfirmPassword("");
      toast({ title: "Success", description: "Password updated successfully." });
    }
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container pt-32 px-4">
          <p className="text-center">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container pt-24 sm:pt-32 px-4 pb-16">
        {/* Mobile-optimized header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8">
          <div className="min-w-0">
            <h1 className="text-2xl sm:text-4xl font-bold mb-1 sm:mb-2 truncate">My Dashboard</h1>
            <p className="text-sm sm:text-base text-muted-foreground truncate">Welcome back, {profile?.full_name || user?.email}</p>
          </div>
        </div>

        <Tabs defaultValue={activeTab} value={activeTab} onValueChange={(val) => {
          setActiveTab(val);
          setSearchParams({ tab: val });
        }} className="space-y-4 sm:space-y-6">
          {/* Horizontally scrollable tabs for mobile */}
          <div className="overflow-x-auto -mx-4 px-4 pb-2">
            <TabsList className="inline-flex w-max min-w-full sm:w-auto sm:flex-wrap gap-1">
              <TabsTrigger value="recommendations" className="text-xs sm:text-sm whitespace-nowrap">
                Recommendations
              </TabsTrigger>
              <TabsTrigger value="sessions" className="text-xs sm:text-sm whitespace-nowrap">
                Sessions
              </TabsTrigger>
              <TabsTrigger value="questions" className="text-xs sm:text-sm whitespace-nowrap">
                <MessageCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Questions
              </TabsTrigger>
              <TabsTrigger value="purchases" className="text-xs sm:text-sm whitespace-nowrap">
                <ShoppingBag className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Purchases
                {purchases.length > 0 && (
                  <Badge variant="secondary" className="ml-1 sm:ml-2 text-xs">{purchases.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="messages" className="text-xs sm:text-sm whitespace-nowrap relative">
                <MessageCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Messages
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="ml-1 sm:ml-2 text-xs">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="profile" className="text-xs sm:text-sm whitespace-nowrap">
                Profile
              </TabsTrigger>
              <TabsTrigger value="settings" className="text-xs sm:text-sm whitespace-nowrap">
                <Settings className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Settings
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="recommendations" className="space-y-6">
            <RecommendationsCard 
              recommendations={recommendations}
              loading={recommendationsLoading}
              onCompleteProfile={() => setActiveTab("profile")}
            />
          </TabsContent>

          <TabsContent value="questions" className="space-y-6">
            <DashboardQuestionsTab userId={user?.id || ""} />
          </TabsContent>

          <TabsContent value="purchases" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>My Purchases</CardTitle>
                <CardDescription>Download your purchased digital products</CardDescription>
              </CardHeader>
              <CardContent>
                {purchases.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <ShoppingBag className="mx-auto h-12 w-12 mb-4 opacity-50" />
                    <p>No purchases yet</p>
                    <Button className="mt-4" onClick={() => navigate("/mentors")}>
                      Browse Products
                    </Button>
                  </div>
                ) : (
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {purchases.map((purchase) => (
                      <PurchasedProductCard key={purchase.id} purchase={purchase} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="messages" className="space-y-6">
            <ConversationsList userId={user?.id || ""} />
          </TabsContent>

          <TabsContent value="sessions" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <BookingCalendarView userId={user?.id || ""} userType="learner" />
              </div>
              <div>
                <GoogleCalendarSync mentorId={user?.id || ""} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Settings</CardTitle>
                <CardDescription>Update your profile information and preferences</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      name="full_name"
                      defaultValue={profile?.full_name || ""}
                      placeholder="Your name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="interests">Categories of Interest*</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="interest-business"
                          name="interests"
                          value="Business"
                          defaultChecked={profile?.interests?.includes("Business")}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="interest-business" className="font-normal cursor-pointer">Business</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="interest-tech"
                          name="interests"
                          value="Tech"
                          defaultChecked={profile?.interests?.includes("Tech")}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="interest-tech" className="font-normal cursor-pointer">Tech</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="interest-creators"
                          name="interests"
                          value="Creators"
                          defaultChecked={profile?.interests?.includes("Creators")}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="interest-creators" className="font-normal cursor-pointer">Creators</Label>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="skill_level">Skill Level</Label>
                    <Select name="skill_level" defaultValue={profile?.skill_level || ""}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select your skill level" />
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
                    <Textarea
                      id="goals"
                      name="goals"
                      defaultValue={profile?.goals || ""}
                      placeholder="What are your learning goals?"
                      rows={4}
                    />
                  </div>

                  <div className="space-y-2">
                    <TimezoneSelect
                      value={profileTimezone}
                      onValueChange={setProfileTimezone}
                      label="Time zone"
                      placeholder="Select your time zone (for sessions and booking)"
                    />
                    <input type="hidden" name="timezone" value={profileTimezone} />
                  </div>

                  <Button type="submit" className="w-full">
                    Update Profile
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            {/* Edit profile */}
            <Card>
              <CardHeader>
                <CardTitle>Profile</CardTitle>
                <CardDescription>Update your name, interests, and goals</CardDescription>
              </CardHeader>
              <CardContent>
                <Button type="button" variant="outline" onClick={() => setActiveTab("profile")}>
                  Edit profile
                </Button>
              </CardContent>
            </Card>

            {/* Email */}
            <Card>
              <CardHeader>
                <CardTitle>Email address</CardTitle>
                <CardDescription>Change your email. We&apos;ll send a verification link to the new address. After you confirm, the new email is saved and used for sign-in.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Current email</Label>
                  <Input type="email" value={user?.email ?? ""} readOnly className="bg-muted" />
                </div>
                <form onSubmit={handleUpdateEmail} className="space-y-2">
                  <div className="space-y-2">
                    <Label htmlFor="new_email">New email</Label>
                    <Input
                      id="new_email"
                      type="email"
                      placeholder="new@example.com"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                    />
                  </div>
                  <Button type="submit" disabled={emailUpdating}>
                    {emailUpdating ? "Sending…" : "Update email"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Password */}
            <Card>
              <CardHeader>
                <CardTitle>Password</CardTitle>
                <CardDescription>Set a new password. You stay signed in.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleChangePassword} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new_password">New password</Label>
                    <Input
                      id="new_password"
                      type="password"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      minLength={6}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm new password</Label>
                    <Input
                      id="confirm_password"
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      minLength={6}
                    />
                  </div>
                  <Button type="submit" disabled={passwordUpdating}>
                    {passwordUpdating ? "Updating…" : "Change password"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <NotificationSettings />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;