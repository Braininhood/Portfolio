import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useUserRole } from "@/hooks/useUserRole";
import { useUnreadMessages } from "@/hooks/useUnreadMessages";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LayoutDashboard, Users, LogOut, Menu, X, Shield, Calendar, UserCircle, HelpCircle, CreditCard, Bell, MessageCircle } from "lucide-react";
import { User } from "@supabase/supabase-js";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/mentors", label: "Mentors", icon: Users },
  { to: "/admin/bookings", label: "Bookings", icon: Calendar },
  { to: "/admin/learners", label: "Learners", icon: UserCircle },
  { to: "/admin/questions", label: "Questions", icon: HelpCircle },
  { to: "/admin/payments", label: "Payments", icon: CreditCard },
  { to: "/admin/subscriptions", label: "Subscriptions", icon: Bell },
];

export const AdminLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { isAdmin, loading: roleLoading } = useUserRole();
  const { unreadCount } = useUnreadMessages(user);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setUser(session?.user ?? null));
  }, []);

  useEffect(() => {
    if (roleLoading) return;
    if (!isAdmin) {
      toast.error("Access denied. Admin only.");
      navigate("/");
      return;
    }
  }, [isAdmin, roleLoading, navigate]);

  const handleSignOut = () => {
    supabase.auth.signOut();
    navigate("/");
  };

  if (roleLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "border-r bg-card flex flex-col transition-[width] duration-200 z-40",
          sidebarOpen ? "w-56" : "w-16"
        )}
      >
        <div className="p-4 border-b flex items-center justify-between">
          <Link to="/admin" className="flex items-center gap-2 min-w-0">
            <Shield className="h-6 w-6 shrink-0 text-primary" />
            {sidebarOpen && <span className="font-semibold truncate">Admin</span>}
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={() => setSidebarOpen((o) => !o)}
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname === to || (to !== "/admin" && location.pathname.startsWith(to));
            return (
              <Link key={to} to={to}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn("w-full justify-start gap-3", !sidebarOpen && "justify-center px-0")}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {sidebarOpen && <span>{label}</span>}
                </Button>
              </Link>
            );
          })}
        </nav>
        <div className="p-2 border-t">
          <div className={cn("px-3 py-2 text-xs text-muted-foreground truncate", !sidebarOpen && "hidden")}>
            {user?.email}
          </div>
          <Link to="/admin/messages">
            <Button variant="ghost" className={cn("w-full justify-start gap-3 relative", !sidebarOpen && "justify-center px-0")}>
              <MessageCircle className="h-4 w-4 shrink-0" />
              {sidebarOpen && <span>Messages</span>}
              {unreadCount > 0 && (
                <Badge variant="destructive" className="ml-auto h-5 min-w-5 px-1 text-xs">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </Badge>
              )}
            </Button>
          </Link>
          <Button variant="ghost" className={cn("w-full justify-start gap-3", !sidebarOpen && "justify-center px-0")} onClick={handleSignOut}>
            <LogOut className="h-4 w-4 shrink-0" />
            {sidebarOpen && <span>Sign out</span>}
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto flex flex-col min-h-0">
        <Outlet />
      </main>
    </div>
  );
};
