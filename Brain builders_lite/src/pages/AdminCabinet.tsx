import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";
import { User } from "@supabase/supabase-js";
import { LayoutDashboard, Users, Calendar, UserCircle, HelpCircle, CreditCard, Bell, MessageSquare, DollarSign, BookOpen, Bot } from "lucide-react";
import { useUserRole } from "@/hooks/useUserRole";
import { useUnreadMessages } from "@/hooks/useUnreadMessages";
import { Badge } from "@/components/ui/badge";
import AdminUsersManagementPro from "./AdminUsersManagementPro";
import AdminBookings from "./AdminBookings";
import AdminQuestions from "./AdminQuestions";
import AdminPayments from "./AdminPayments";
import AdminSubscriptions from "./AdminSubscriptions";
import AdminAvatars from "./AdminAvatars";
import { ConversationsList } from "@/components/ConversationsList";

interface Stats {
  mentors: number;
  learners: number;
  bookings: number;
  questions: number;
  totalRevenue: number;
}

const AdminCabinet = () => {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<Stats>({ 
    mentors: 0, 
    learners: 0,
    bookings: 0, 
    questions: 0,
    totalRevenue: 0
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab") || "dashboard";
  const [activeTab, setActiveTab] = useState(tabFromUrl);
  const { toast } = useToast();
  const { isAdmin, loading: roleLoading } = useUserRole();
  const { unreadCount } = useUnreadMessages(user);

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!roleLoading && !isAdmin) {
      navigate("/", { replace: true });
      toast({
        title: "Access denied",
        description: "Admin access required",
        variant: "destructive",
      });
    }
  }, [roleLoading, isAdmin, navigate]);

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      navigate("/auth");
      return;
    }
    
    setUser(session.user);
    loadAdminData();
  };

  const loadAdminData = async () => {
    setLoading(true);

    const [mentorsRes, learnersRes, bookingsRes, questionsRes, revenueRes] = await Promise.all([
      supabase.from("mentor_profiles").select("id", { count: "exact", head: true }),
      supabase.from("profiles").select("id", { count: "exact", head: true }),
      supabase.from("bookings").select("id", { count: "exact", head: true }),
      supabase.from("mentor_questions").select("id", { count: "exact", head: true }),
      supabase.from("bookings").select("price").eq("status", "confirmed"),
    ]);
    
    const totalRevenue = (revenueRes.data ?? []).reduce((sum, b) => sum + Number(b.price), 0);
    
    setStats({
      mentors: mentorsRes.count ?? 0,
      learners: (learnersRes.count ?? 0) - (mentorsRes.count ?? 0),
      bookings: bookingsRes.count ?? 0,
      questions: questionsRes.count ?? 0,
      totalRevenue,
    });

    setLoading(false);
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
      <div className="container pt-24 sm:pt-32 px-3 sm:px-4 pb-16">
        {/* Header - matching mentor cabinet style */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8">
          <div className="min-w-0">
            <h1 className="text-2xl sm:text-4xl font-bold mb-1 sm:mb-2 truncate">Admin Dashboard</h1>
            <p className="text-sm sm:text-base text-muted-foreground truncate">
              Welcome back, {user?.email}
            </p>
          </div>
        </div>

        {/* Stats cards - matching mentor stats style */}
        <div className="mb-4 sm:mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Earnings</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${stats.totalRevenue.toFixed(2)}</div>
                <p className="text-xs text-muted-foreground mt-1">Lifetime earnings</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Students</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.learners}</div>
                <p className="text-xs text-muted-foreground mt-1">Students mentored</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Mentors</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.mentors}</div>
                <p className="text-xs text-muted-foreground mt-1">Registered mentors</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Upcoming Sessions</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.bookings}</div>
                <p className="text-xs text-muted-foreground mt-1">Sessions scheduled</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tabs - matching mentor cabinet tabs style */}
        <Tabs
          value={activeTab}
          onValueChange={(val) => {
            setActiveTab(val);
            setSearchParams(val === "dashboard" ? {} : { tab: val });
          }}
          className="space-y-4 sm:space-y-6"
        >
          {/* Scrollable tabs for mobile */}
          <ScrollArea className="w-full whitespace-nowrap">
            <TabsList className="inline-flex h-auto p-1 w-max min-w-full sm:w-auto sm:flex-wrap gap-1">
              <TabsTrigger value="dashboard" className="px-3 py-2 text-xs sm:text-sm">
                <LayoutDashboard className="h-4 w-4 mr-1.5 sm:mr-2" />
                Dashboard
              </TabsTrigger>
              <TabsTrigger value="users" className="px-3 py-2 text-xs sm:text-sm">
                <UserCircle className="h-4 w-4 mr-1.5 sm:mr-2" />
                Users
              </TabsTrigger>
              <TabsTrigger value="bookings" className="px-3 py-2 text-xs sm:text-sm">
                <Calendar className="h-4 w-4 mr-1.5 sm:mr-2" />
                Bookings
              </TabsTrigger>
              <TabsTrigger value="questions" className="px-3 py-2 text-xs sm:text-sm">
                <HelpCircle className="h-4 w-4 mr-1.5 sm:mr-2" />
                Questions
              </TabsTrigger>
              <TabsTrigger value="payments" className="px-3 py-2 text-xs sm:text-sm">
                <CreditCard className="h-4 w-4 mr-1.5 sm:mr-2" />
                Sales
              </TabsTrigger>
              <TabsTrigger value="subscriptions" className="px-3 py-2 text-xs sm:text-sm">
                <Bell className="h-4 w-4 mr-1.5 sm:mr-2" />
                Subscriptions
              </TabsTrigger>
              <TabsTrigger value="avatars" className="px-3 py-2 text-xs sm:text-sm">
                <Bot className="h-4 w-4 mr-1.5 sm:mr-2" />
                AI Avatars
              </TabsTrigger>
              <TabsTrigger value="messages" className="px-3 py-2 text-xs sm:text-sm relative">
                <MessageSquare className="h-4 w-4 mr-1.5 sm:mr-2" />
                Messages
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="ml-1 h-4 min-w-4 px-1 text-xs">
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
          </ScrollArea>

          {/* Tab contents */}
          <TabsContent value="dashboard">
            <Card>
              <CardHeader>
                <CardTitle>Platform Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Manage your platform from this central dashboard.</p>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <Button variant="outline" onClick={() => setActiveTab("users")}>
                    <UserCircle className="mr-2 h-4 w-4" />
                    Manage Users ({stats.learners + stats.mentors})
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab("bookings")}>
                    <Calendar className="mr-2 h-4 w-4" />
                    Manage Bookings ({stats.bookings})
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab("questions")}>
                    <HelpCircle className="mr-2 h-4 w-4" />
                    Manage Questions ({stats.questions})
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab("payments")}>
                    <CreditCard className="mr-2 h-4 w-4" />
                    Manage Sales
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab("subscriptions")}>
                    <Bell className="mr-2 h-4 w-4" />
                    Subscriptions
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab("avatars")}>
                    <Bot className="mr-2 h-4 w-4" />
                    AI Avatars
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <AdminUsersManagementPro />
          </TabsContent>

          <TabsContent value="bookings">
            <AdminBookings />
          </TabsContent>

          <TabsContent value="questions">
            <AdminQuestions />
          </TabsContent>

          <TabsContent value="payments">
            <AdminPayments />
          </TabsContent>

          <TabsContent value="subscriptions">
            <AdminSubscriptions />
          </TabsContent>

          <TabsContent value="avatars">
            <AdminAvatars />
          </TabsContent>

          <TabsContent value="messages">
            {user && <ConversationsList userId={user.id} />}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminCabinet;
