import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";
import { MentorStatsCard } from "@/components/MentorStatsCard";
import { MentorBookingsCard } from "@/components/MentorBookingsCard";
import { MentorSessionEditDialog, type MentorBooking } from "@/components/MentorSessionEditDialog";
import { BookingCalendarView } from "@/components/BookingCalendarView";
import { MentorProfileEditor } from "@/components/MentorProfileEditor";
import { WeeklyAvailabilityEditor } from "@/components/WeeklyAvailabilityEditor";
import { GoogleCalendarSync } from "@/components/GoogleCalendarSync";
import { AvailabilitySummary } from "@/components/AvailabilitySummary";
import { ConversationsList } from "@/components/ConversationsList";
import { NotificationSettings } from "@/components/NotificationSettings";
import { AvatarManagementTab } from "@/components/AvatarManagementTab";
import { MentorProductsTab } from "@/components/MentorProductsTab";
import { MentorSalesTab } from "@/components/MentorSalesTab";
import { MentorQuestionsTab } from "@/components/MentorQuestionsTab";
import { StripeConnectSetup } from "@/components/StripeConnectSetup";
import { PayoutDashboard } from "@/components/PayoutDashboard";
import { User } from "@supabase/supabase-js";
import { Settings, ShoppingBag, Receipt, LayoutDashboard, User as UserIcon, Bot, CalendarClock, HelpCircle, CalendarDays, MessageSquare, Wallet } from "lucide-react";
import { useUserRole } from "@/hooks/useUserRole";
import { useUnreadMessages } from "@/hooks/useUnreadMessages";
import { Badge } from "@/components/ui/badge";

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
  availability: string;
  experience: string;
  education: string;
  certifications: string[] | null;
  image_url: string | null;
  rating: number | null;
  review_count: number | null;
  username: string | null;
  timezone?: string | null;
}

interface Booking {
  id: string;
  mentor_id: string;
  user_email: string;
  booking_date: string;
  booking_time: string;
  status: string;
  price: number;
  meeting_link: string | null;
  meeting_platform: string | null;
  notes: string | null;
}

const MentorCabinet = () => {
  const [user, setUser] = useState<User | null>(null);
  const [mentorProfile, setMentorProfile] = useState<MentorProfile | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailUpdating, setEmailUpdating] = useState(false);
  const [passwordUpdating, setPasswordUpdating] = useState(false);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab") || "overview";
  const [activeTab, setActiveTab] = useState(tabFromUrl);
  const [editingSession, setEditingSession] = useState<MentorBooking | null>(null);
  const { toast } = useToast();
  const { isMentor, isAdmin, loading: roleLoading } = useUserRole();
  const { unreadCount } = useUnreadMessages(user);

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (roleLoading) return;
    if (isAdmin && !isMentor) {
      navigate("/admin", { replace: true });
    } else if (!isMentor && !isAdmin) {
      navigate("/learner/dashboard", { replace: true });
    }
  }, [roleLoading, isMentor, isAdmin, navigate]);

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      navigate("/auth");
      return;
    }
    
    setUser(session.user);
    loadMentorData(session.user.id);
  };

  const loadMentorData = async (userId: string) => {
    setLoading(true);

    // Load mentor profile
    const { data: profileData } = await supabase
      .from("mentor_profiles")
      .select("*")
      .eq("user_id", userId)
      .maybeSingle();

    setMentorProfile(profileData);

    if (profileData) {
      // Load bookings for this mentor
      const { data: bookingsData } = await supabase
        .from("bookings")
        .select("*")
        .eq("mentor_id", profileData.id)
        .order("booking_date", { ascending: false });

      setBookings(bookingsData || []);

      // Time slots are managed by WeeklyAvailabilityEditor component
    }

    setLoading(false);
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

  const handleProfileSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!user) return;

    const formData = new FormData(e.currentTarget);
    const expertise = formData.get("expertise")?.toString().split(",").map(e => e.trim()).filter(Boolean) || [];
    const languages = formData.get("languages")?.toString().split(",").map(l => l.trim()).filter(Boolean) || [];
    const certifications = formData.get("certifications")?.toString().split(",").map(c => c.trim()).filter(Boolean) || [];

    const profileData = {
      user_id: user.id,
      name: formData.get("name")?.toString() || "",
      title: formData.get("title")?.toString() || "",
      category: formData.get("category")?.toString() || "",
      bio: formData.get("bio")?.toString() || "",
      full_bio: formData.get("full_bio")?.toString() || "",
      price: parseFloat(formData.get("price")?.toString() || "0"),
      expertise,
      languages,
      availability: formData.get("availability")?.toString() || "",
      experience: formData.get("experience")?.toString() || "",
      education: formData.get("education")?.toString() || "",
      certifications,
      image_url: formData.get("image_url")?.toString() || null,
      username: formData.get("username")?.toString().toLowerCase().replace(/[^a-z0-9_-]/g, "") || null,
      timezone: formData.get("timezone")?.toString().trim() || null,
    };

    if (mentorProfile) {
      // Update existing profile
      const { error } = await supabase
        .from("mentor_profiles")
        .update(profileData)
        .eq("id", mentorProfile.id);

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
        loadMentorData(user.id);
      }
    } else {
      // Create new profile
      const { error } = await supabase
        .from("mentor_profiles")
        .insert(profileData);

      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Success",
          description: "Mentor profile created successfully",
        });
        loadMentorData(user.id);
      }
    }
  };

  const upcomingBookings = bookings.filter(b =>
    new Date(b.booking_date) >= new Date() && ["pending", "confirmed"].includes(b.status)
  );

  const pastBookings = bookings.filter(b =>
    new Date(b.booking_date) < new Date() || ["cancelled", "completed", "failed", "refunded"].includes(b.status)
  );

  // Calculate net earnings from transactions table (after fees)
  const [netEarnings, setNetEarnings] = useState(0);

  useEffect(() => {
    if (mentorProfile) {
      loadNetEarnings();
    }
  }, [mentorProfile]);

  const loadNetEarnings = async () => {
    if (!mentorProfile) return;

    try {
      // Direct query to transactions table
      // Note: This requires transactions table to be accessible
      // The table exists from migration: 20260222100005_add_mentor_services_product_variants_stripe_transactions.sql
      
      const { data: transactionsData, error } = await supabase
        .from('transactions')
        .select('net_amount')
        .eq('mentor_id', mentorProfile.id)
        .eq('status', 'completed');

      if (error) {
        console.error('Error loading net earnings:', error);
        // Fallback: show 0 earnings (transactions table might not have data yet)
        setNetEarnings(0);
        return;
      }

      if (transactionsData && transactionsData.length > 0) {
        const total = transactionsData.reduce((sum: number, t: any) => sum + Number(t.net_amount), 0);
        setNetEarnings(total);
      } else {
        setNetEarnings(0);
      }
    } catch (error) {
      console.error('Error loading net earnings:', error);
      setNetEarnings(0);
    }
  };

  const uniqueStudents = new Set(bookings.map(b => b.user_email)).size;

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
      <div className="container pt-24 sm:pt-32 px-3 sm:px-4 pb-16">
        {/* Mobile-friendly header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8">
          <div className="min-w-0">
            <h1 className="text-2xl sm:text-4xl font-bold mb-1 sm:mb-2 truncate">Mentor Cabinet</h1>
            <p className="text-sm sm:text-base text-muted-foreground truncate">
              Welcome back, {mentorProfile?.name || user?.email}
            </p>
          </div>
        </div>

        {mentorProfile && (
          <div className="mb-4 sm:mb-6">
            <MentorStatsCard
              totalEarnings={netEarnings}
              totalStudents={uniqueStudents}
              averageRating={mentorProfile.rating || 0}
              upcomingSessions={upcomingBookings.length}
            />
          </div>
        )}

        <Tabs
          value={activeTab}
          onValueChange={(val) => {
            setActiveTab(val);
            setSearchParams(val === "profile" ? {} : { tab: val });
          }}
          className="space-y-4 sm:space-y-6"
        >
          {/* Scrollable tabs for mobile */}
          <ScrollArea className="w-full whitespace-nowrap">
            <TabsList className="inline-flex h-auto p-1 w-max min-w-full sm:w-auto sm:flex-wrap gap-1">
              {mentorProfile && (
                <TabsTrigger value="overview" className="px-3 py-2 text-xs sm:text-sm">
                  <LayoutDashboard className="h-4 w-4 mr-1.5 sm:mr-2" />
                  <span className="hidden xs:inline">Overview</span>
                  <span className="xs:hidden">Home</span>
                </TabsTrigger>
              )}
              <TabsTrigger value="profile" className="px-3 py-2 text-xs sm:text-sm">
                <UserIcon className="h-4 w-4 mr-1.5 sm:mr-2" />
                Profile
              </TabsTrigger>
              {mentorProfile && (
                <TabsTrigger value="avatar" className="px-3 py-2 text-xs sm:text-sm">
                  <Bot className="h-4 w-4 mr-1.5 sm:mr-2" />
                  <span className="hidden sm:inline">AI Avatar</span>
                  <span className="sm:hidden">Avatar</span>
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="shop" className="px-3 py-2 text-xs sm:text-sm">
                  <ShoppingBag className="h-4 w-4 mr-1.5 sm:mr-2" />
                  Shop
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="sales" className="px-3 py-2 text-xs sm:text-sm">
                  <Receipt className="h-4 w-4 mr-1.5 sm:mr-2" />
                  Sales
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="payouts" className="px-3 py-2 text-xs sm:text-sm">
                  <Wallet className="h-4 w-4 mr-1.5 sm:mr-2" />
                  Payouts
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="availability" className="px-3 py-2 text-xs sm:text-sm">
                  <CalendarClock className="h-4 w-4 mr-1.5 sm:mr-2" />
                  <span className="hidden sm:inline">Availability</span>
                  <span className="sm:hidden">Slots</span>
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="questions" className="px-3 py-2 text-xs sm:text-sm">
                  <HelpCircle className="h-4 w-4 mr-1.5 sm:mr-2" />
                  <span className="hidden sm:inline">Questions</span>
                  <span className="sm:hidden">Q&A</span>
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="sessions" className="px-3 py-2 text-xs sm:text-sm">
                  <CalendarDays className="h-4 w-4 mr-1.5 sm:mr-2" />
                  Sessions
                </TabsTrigger>
              )}
              {mentorProfile && (
                <TabsTrigger value="messages" className="px-3 py-2 text-xs sm:text-sm relative">
                  <MessageSquare className="h-4 w-4 mr-1.5 sm:mr-2" />
                  <span className="hidden sm:inline">Messages</span>
                  <span className="sm:hidden">Chat</span>
                  {unreadCount > 0 && (
                    <Badge variant="destructive" className="ml-1.5 h-5 min-w-5 px-1 text-xs">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              <TabsTrigger value="settings" className="px-3 py-2 text-xs sm:text-sm">
                <Settings className="h-4 w-4 mr-1.5 sm:mr-2" />
                Settings
              </TabsTrigger>
            </TabsList>
            <ScrollBar orientation="horizontal" className="invisible" />
          </ScrollArea>

          {mentorProfile && (
            <TabsContent value="overview" className="space-y-6">
              <MentorBookingsCard bookings={upcomingBookings} type="upcoming" />
            </TabsContent>
          )}

          <TabsContent value="profile">
            <MentorProfileEditor 
              profile={mentorProfile}
              onSubmit={handleProfileSubmit}
              userId={user?.id || ""}
            />
          </TabsContent>

          {mentorProfile && (
            <TabsContent value="avatar">
              <AvatarManagementTab mentorId={mentorProfile.id} />
            </TabsContent>
          )}

          {mentorProfile && (
            <TabsContent value="shop">
              <MentorProductsTab
                mentorId={mentorProfile.id}
                mentorUsername={mentorProfile.username}
                mentorName={mentorProfile.name}
              />
            </TabsContent>
          )}

          {mentorProfile && (
            <TabsContent value="sales">
              <MentorSalesTab mentorId={mentorProfile.id} />
            </TabsContent>
          )}

          {mentorProfile && (
            <TabsContent value="payouts" className="space-y-6">
              <StripeConnectSetup mentorId={mentorProfile.id} />
              <PayoutDashboard mentorId={mentorProfile.id} />
            </TabsContent>
          )}

          {mentorProfile && (
            <>
              <TabsContent value="availability" className="space-y-6">
                <div className="grid gap-6 lg:grid-cols-3">
                  <div className="lg:col-span-2">
                    <WeeklyAvailabilityEditor mentorId={mentorProfile.id} />
                  </div>
                  <div className="space-y-6">
                    <AvailabilitySummary mentorId={mentorProfile.id} />
                    <div data-calendar-sync>
                      <GoogleCalendarSync mentorId={mentorProfile.id} />
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="questions">
                <MentorQuestionsTab mentorId={mentorProfile.id} />
              </TabsContent>

              <TabsContent value="sessions" className="space-y-6">
                <div className="grid gap-6 lg:grid-cols-3">
                  <div className="lg:col-span-2 space-y-6">
                    <BookingCalendarView userId={mentorProfile.id} userType="mentor" />
                    <MentorBookingsCard
                      bookings={upcomingBookings as MentorBooking[]}
                      type="upcoming"
                      onEditClick={(b) => setEditingSession(b)}
                    />
                    <MentorBookingsCard bookings={pastBookings as MentorBooking[]} type="past" />
                  </div>
                  <div>
                    <GoogleCalendarSync mentorId={mentorProfile.id} />
                  </div>
                </div>
                <MentorSessionEditDialog
                  booking={editingSession}
                  open={!!editingSession}
                  onOpenChange={(open) => !open && setEditingSession(null)}
                  onSaved={() => {
                    setEditingSession(null);
                    checkAuth();
                  }}
                  onMarkCompleted={() => {
                    setEditingSession(null);
                    checkAuth();
                  }}
                />
              </TabsContent>

              <TabsContent value="messages">
                <ConversationsList userId={user?.id || ""} />
              </TabsContent>
            </>
          )}

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile</CardTitle>
                <CardDescription>Update your mentor profile and public info</CardDescription>
              </CardHeader>
              <CardContent>
                <Button type="button" variant="outline" onClick={() => setActiveTab("profile")}>
                  Edit profile
                </Button>
              </CardContent>
            </Card>

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
                    <Label htmlFor="mentor-new-email">New email</Label>
                    <Input
                      id="mentor-new-email"
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

            <Card>
              <CardHeader>
                <CardTitle>Password</CardTitle>
                <CardDescription>Set a new password. You stay signed in.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleChangePassword} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="mentor-new-password">New password</Label>
                    <Input
                      id="mentor-new-password"
                      type="password"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      minLength={6}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mentor-confirm-password">Confirm new password</Label>
                    <Input
                      id="mentor-confirm-password"
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

export default MentorCabinet;
