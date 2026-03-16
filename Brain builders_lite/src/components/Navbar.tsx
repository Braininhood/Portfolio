import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Menu, X, MessageCircle, LogOut, ArrowLeftRight } from "lucide-react";
import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useUnreadMessages } from "@/hooks/useUnreadMessages";
import { useUserRole } from "@/hooks/useUserRole";
import { NotificationBell } from "@/components/NotificationBell";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { unreadCount } = useUnreadMessages(user);
  const { isAdmin, isMentor, isLearner } = useUserRole();
  const canSwitchDashboards = isMentor && isLearner;
  const isOnLearnerDashboard = location.pathname.startsWith("/learner");
  const isOnMentorDashboard = location.pathname.startsWith("/mentor/");
  const dashboardBase = user && isAdmin ? "/admin" : user && isMentor ? "/mentor/dashboard" : "/learner/dashboard";
  const messagesPath = user && isAdmin
    ? "/admin/messages"
    : user && isMentor
      ? "/mentor/dashboard?tab=messages"
      : "/learner/dashboard?tab=messages";
  const isDashboard = location.pathname.startsWith("/mentor/") || location.pathname.startsWith("/learner") || location.pathname.startsWith("/admin");

  const goToDashboard = () => {
    // Always navigate to base dashboard path (no tab param) to land on overview
    navigate(dashboardBase);
    setIsOpen(false);
  };

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <nav className="fixed top-0 w-full z-50 glass-effect border-b border-border">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex-shrink-0">
            <h1 className="text-2xl font-display font-bold gradient-text">
              Brain Bulders
            </h1>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {!user && (
              <>
                <Link to="/auth/mentor" className="text-foreground hover:text-accent transition-colors">
                  Become a Mentor
                </Link>
                <Link to="/auth/learner" className="text-foreground hover:text-accent transition-colors">
                  Join as Learner
                </Link>
              </>
            )}
            {!isDashboard && (
              <>
                <Link to="/mentors" className="text-foreground hover:text-accent transition-colors">
                  Find Mentors
                </Link>
                <a href="/#how-it-works" className="text-foreground hover:text-accent transition-colors">
                  How It Works
                </a>
              </>
            )}
            {user && isAdmin && (
              <Link to="/admin" className="text-foreground hover:text-accent transition-colors font-medium">
                Admin
              </Link>
            )}
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-2 sm:space-x-4">
            {user && (
              <>
                <NotificationBell />
                <Button
                  variant="ghost"
                  size="icon"
                  className="relative"
                  onClick={() => navigate(messagesPath)}
                  aria-label="Messages"
                >
                  <MessageCircle className="h-5 w-5" />
                  {unreadCount > 0 && (
                    <Badge 
                      variant="destructive" 
                      className="absolute -top-1 -right-1 h-5 min-w-5 px-1.5 text-xs flex items-center justify-center"
                    >
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </Badge>
                  )}
                </Button>
                {isOnLearnerDashboard && (
                  <Button variant="outline" size="sm" onClick={() => navigate("/mentors")}>
                    Find Mentor
                  </Button>
                )}
                {isOnLearnerDashboard && canSwitchDashboards && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      localStorage.setItem("gcreators_dashboard_view", "mentor");
                      navigate("/mentor/dashboard", { replace: true });
                    }}
                  >
                    <ArrowLeftRight className="mr-1.5 h-4 w-4" />
                    Switch to Mentor
                  </Button>
                )}
                {isOnMentorDashboard && canSwitchDashboards && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      localStorage.setItem("gcreators_dashboard_view", "learner");
                      navigate("/learner/dashboard", { replace: true });
                    }}
                  >
                    <ArrowLeftRight className="mr-1.5 h-4 w-4" />
                    Switch to Learner
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={async () => { await supabase.auth.signOut(); navigate("/"); }}>
                  <LogOut className="mr-1.5 h-4 w-4" />
                  Sign Out
                </Button>
              </>
            )}
            {!user && (
              <Button variant="ghost" onClick={() => navigate('/auth')}>Sign In</Button>
            )}
            {user && (
              <Button variant="hero" onClick={goToDashboard}>
                Dashboard
              </Button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-foreground hover:text-accent"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 space-y-4">
            {!user && (
              <>
                <Link
                  to="/auth/mentor"
                  className="block text-foreground hover:text-accent transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  Become a Mentor
                </Link>
                <Link
                  to="/auth/learner"
                  className="block text-foreground hover:text-accent transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  Join as Learner
                </Link>
              </>
            )}
            {!isDashboard && (
              <>
                <Link
                  to="/mentors"
                  className="block text-foreground hover:text-accent transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  Find Mentors
                </Link>
                <a
                  href="/#how-it-works"
                  className="block text-foreground hover:text-accent transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  How It Works
                </a>
              </>
            )}
            {user && isAdmin && (
              <Link
                to="/admin"
                className="block text-foreground hover:text-accent transition-colors font-medium"
                onClick={() => setIsOpen(false)}
              >
                Admin
              </Link>
            )}
            <div className="pt-4 space-y-2">
              {user && (
                <>
                  <Button
                    variant="outline"
                    className="w-full relative"
                    onClick={() => {
                      setIsOpen(false);
                      navigate(messagesPath);
                    }}
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Messages
                    {unreadCount > 0 && (
                      <Badge variant="destructive" className="ml-2 h-5 min-w-5 px-1.5 text-xs">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </Badge>
                    )}
                  </Button>
                  {isOnLearnerDashboard && (
                    <Button variant="outline" className="w-full" onClick={() => { setIsOpen(false); navigate("/mentors"); }}>
                      Find Mentor
                    </Button>
                  )}
                  {isOnLearnerDashboard && canSwitchDashboards && (
                    <Button variant="outline" className="w-full" onClick={() => { setIsOpen(false); localStorage.setItem("gcreators_dashboard_view", "mentor"); navigate("/mentor/dashboard", { replace: true }); }}>
                      <ArrowLeftRight className="h-4 w-4 mr-2" />
                      Switch to Mentor
                    </Button>
                  )}
                  {isOnMentorDashboard && canSwitchDashboards && (
                    <Button variant="outline" className="w-full" onClick={() => { setIsOpen(false); localStorage.setItem("gcreators_dashboard_view", "learner"); navigate("/learner/dashboard", { replace: true }); }}>
                      <ArrowLeftRight className="h-4 w-4 mr-2" />
                      Switch to Learner
                    </Button>
                  )}
                  <Button variant="outline" className="w-full" onClick={async () => { setIsOpen(false); await supabase.auth.signOut(); navigate("/"); }}>
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </Button>
                </>
              )}
              {!user && (
                <Button variant="ghost" className="w-full" onClick={() => { setIsOpen(false); navigate('/auth'); }}>
                  Sign In
                </Button>
              )}
              {user && (
                <Button variant="hero" className="w-full" onClick={goToDashboard}>
                  Dashboard
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;