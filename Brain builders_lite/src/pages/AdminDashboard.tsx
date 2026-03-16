import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Users, BookOpen, Calendar, ArrowRight, DollarSign, Bot, MessageSquare, Zap } from "lucide-react";
import { User } from "@supabase/supabase-js";

interface Stats {
  mentors: number;
  learners: number;
  bookings: number;
  questions: number;
  totalRevenue: number;
}

interface AvatarStat {
  avatar_id: string;
  avatar_name: string;
  mentor_name: string;
  mentor_id: string;
  status: string;
  total_conversations: number;
  total_user_messages: number;
  unique_users: number;
  total_tokens_used: number;
  last_conversation_at: string | null;
  last_trained_at: string | null;
}

export default function AdminDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<Stats>({
    mentors: 0,
    learners: 0,
    bookings: 0,
    questions: 0,
    totalRevenue: 0,
  });
  const [avatarStats, setAvatarStats] = useState<AvatarStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) setUser(session.user);
  };

  useEffect(() => {
    const fetchAll = async () => {
      const [mentorsRes, learnersRes, bookingsRes, questionsRes, revenueRes, avatarRes] = await Promise.all([
        supabase.from("mentor_profiles").select("id", { count: "exact", head: true }),
        supabase.from("profiles").select("id", { count: "exact", head: true }),
        supabase.from("bookings").select("id", { count: "exact", head: true }),
        supabase.from("mentor_questions").select("id", { count: "exact", head: true }),
        supabase.from("bookings").select("price").eq("status", "confirmed"),
        supabase.rpc("get_all_avatar_stats" as any),
      ]);

      const totalRevenue = (revenueRes.data ?? []).reduce((sum, b) => sum + Number(b.price), 0);

      setStats({
        mentors: mentorsRes.count ?? 0,
        learners: (learnersRes.count ?? 0) - (mentorsRes.count ?? 0),
        bookings: bookingsRes.count ?? 0,
        questions: questionsRes.count ?? 0,
        totalRevenue,
      });

      if (!avatarRes.error && avatarRes.data) {
        setAvatarStats(avatarRes.data as AvatarStat[]);
      }

      setLoading(false);
    };
    fetchAll();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header with stats - matching mentor dashboard style */}
      <div className="border-b bg-card">
        <div className="p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {/* Page title */}
            <div className="mb-6 md:mb-8">
              <h1 className="text-2xl sm:text-4xl font-bold mb-1 sm:mb-2">Admin Dashboard</h1>
              <p className="text-sm sm:text-base text-muted-foreground">
                Welcome back, {user?.email}
              </p>
            </div>

            {/* Stats cards - matching mentor stats style */}
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
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="p-6 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Quick stats grid */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Mentors</CardTitle>
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.mentors}</div>
                  <p className="text-xs text-muted-foreground mt-1">Registered mentor profiles</p>
                  <Button variant="link" className="px-0 mt-2 h-auto" asChild>
                    <Link to="/admin/mentors">
                      Manage <ArrowRight className="ml-1 h-3 w-3" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Bookings</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.bookings}</div>
                  <p className="text-xs text-muted-foreground mt-1">Total sessions booked</p>
                  <Button variant="link" className="px-0 mt-2 h-auto" asChild>
                    <Link to="/admin/bookings">
                      Manage <ArrowRight className="ml-1 h-3 w-3" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Questions</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.questions}</div>
                  <p className="text-xs text-muted-foreground mt-1">Mentor Q&A submissions</p>
                  <Button variant="link" className="px-0 mt-2 h-auto" asChild>
                    <Link to="/admin/questions">
                      Manage <ArrowRight className="ml-1 h-3 w-3" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Quick actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick actions</CardTitle>
                <CardDescription>Manage content and users</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link to="/admin/mentors">Manage mentors</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/admin/bookings">Manage bookings</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/admin/learners">Manage learners</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/admin/questions">Manage questions</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/admin/payments">Payments</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/admin/subscriptions">Subscriptions</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/mentors" target="_blank" rel="noopener noreferrer">
                    View public mentors page
                  </Link>
                </Button>
              </CardContent>
            </Card>

            {/* AI Avatar Monitoring */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Bot className="h-5 w-5" />
                      AI Avatar Monitoring
                    </CardTitle>
                    <CardDescription>Usage and performance across all mentor avatars</CardDescription>
                  </div>
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-4 w-4" />
                      {avatarStats.reduce((s, a) => s + Number(a.total_conversations), 0)} total conversations
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="h-4 w-4" />
                      {avatarStats.reduce((s, a) => s + Number(a.total_tokens_used), 0).toLocaleString()} tokens used
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {avatarStats.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">
                    No AI avatars created yet
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Avatar</TableHead>
                        <TableHead>Mentor</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Conversations</TableHead>
                        <TableHead className="text-right">Messages</TableHead>
                        <TableHead className="text-right">Users</TableHead>
                        <TableHead className="text-right">Tokens</TableHead>
                        <TableHead>Last Active</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {avatarStats.map((a) => (
                        <TableRow key={a.avatar_id}>
                          <TableCell className="font-medium">{a.avatar_name || "—"}</TableCell>
                          <TableCell>{a.mentor_name}</TableCell>
                          <TableCell>
                            <Badge
                              variant={a.status === "ready" ? "default" : a.status === "training" ? "secondary" : "outline"}
                              className={a.status === "ready" ? "bg-green-500 hover:bg-green-600" : ""}
                            >
                              {a.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">{Number(a.total_conversations)}</TableCell>
                          <TableCell className="text-right">{Number(a.total_user_messages)}</TableCell>
                          <TableCell className="text-right">{Number(a.unique_users)}</TableCell>
                          <TableCell className="text-right">{Number(a.total_tokens_used).toLocaleString()}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {a.last_conversation_at
                              ? new Date(a.last_conversation_at).toLocaleDateString()
                              : "Never"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
