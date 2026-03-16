import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";
import { User, Session } from "@supabase/supabase-js";
import type { AppRole } from "@/hooks/useUserRole";
import { rateLimiter, rateLimits, formatWaitTime } from "@/utils/rateLimit";

type AuthMode = "signin" | "signup-mentor" | "signup-learner";

const Auth = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const pathname = location.pathname;
  const isMentorSignup = pathname === "/auth/mentor";
  const isLearnerSignup = pathname === "/auth/learner";
  const isSignupOnly = isMentorSignup || isLearnerSignup;
  const signupRole: AppRole = isMentorSignup ? "mentor" : "learner";

  const redirectToByRole = async (userId: string): Promise<string> => {
    // PRIORITY 1: Check if user just changed their role (check both storages)
    const postRoleChangeRedirect = 
      sessionStorage.getItem("post_role_change_redirect") || 
      localStorage.getItem("post_role_change_redirect");
    
    if (postRoleChangeRedirect) {
      console.log("🎯 Found post-role-change redirect:", postRoleChangeRedirect);
      sessionStorage.removeItem("post_role_change_redirect");
      localStorage.removeItem("post_role_change_redirect");
      return postRoleChangeRedirect;
    }
    
    // PRIORITY 2: Check actual user_roles table (most accurate)
    const [rolesRes, mentorRes] = await Promise.all([
      supabase.from("user_roles").select("role").eq("user_id", userId),
      supabase.from("mentor_profiles").select("id").eq("user_id", userId).maybeSingle(),
    ]);
    const roles = (rolesRes.data?.map((r) => r.role as AppRole) || []) as AppRole[];
    const hasMentorProfile = !!mentorRes.data;
    
    console.log("📋 User roles:", roles);
    console.log("🎓 Has mentor profile:", hasMentorProfile);
    
    // Admin always goes to admin panel
    if (roles.includes("admin")) return "/admin";
    
    const hasMentorRole = roles.includes("mentor");
    const hasLearnerRole = roles.includes("learner");
    // User has both roles: use saved dashboard preference (managed by admin + toggle)
    if (hasMentorRole && hasLearnerRole) {
      const preferred = localStorage.getItem("gcreators_dashboard_view");
      if (preferred === "learner") return "/learner/dashboard";
      return "/mentor/dashboard"; // default to mentor
    }
    if (hasMentorRole) return "/mentor/dashboard";
    return "/learner/dashboard";
  };

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        if (session?.user) {
          const urlParams = new URLSearchParams(location.search);
          let redirectTo = urlParams.get("redirect") || undefined;
          if (redirectTo === "/dashboard") redirectTo = "/learner/dashboard";
          if (redirectTo === "/mentor-cabinet") redirectTo = "/mentor/dashboard";
          const target =
            redirectTo ||
            (await redirectToByRole(session.user.id));
          navigate(target, { replace: true });
        }
      }
    );

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        const urlParams = new URLSearchParams(location.search);
        let redirectTo = urlParams.get("redirect") || undefined;
        if (redirectTo === "/dashboard") redirectTo = "/learner/dashboard";
        if (redirectTo === "/mentor-cabinet") redirectTo = "/mentor/dashboard";
        const target =
          redirectTo ||
          (await redirectToByRole(session.user.id));
        navigate(target, { replace: true });
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate, location.search]);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // ✅ PRIORITY 2: Rate limiting for authentication
    const rateLimit = rateLimiter.check(rateLimits.authSignup);
    if (!rateLimit.allowed) {
      const waitTime = formatWaitTime(rateLimit.waitMs);
      toast({
        title: "Too many sign-up attempts",
        description: `Please wait ${waitTime} before trying again. You can sign up ${rateLimits.authSignup.maxRequests} times per hour.`,
        variant: "destructive",
      });
      return;
    }
    
    if (!email || !password) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }
    if (password.length < 6) {
      toast({
        title: "Error",
        description: "Password must be at least 6 characters",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    const redirectUrl = `${window.location.origin}/auth`;
    const emailNormalized = email.trim().toLowerCase();

    const { data: signUpData, error } = await supabase.auth.signUp({
      email: emailNormalized,
      password,
      options: {
        emailRedirectTo: redirectUrl,
        data: {
          full_name: fullName || emailNormalized.split("@")[0],
          role: signupRole,
        },
      },
    });

    if (error) {
      setLoading(false);
      const isRateLimit =
        error.message?.toLowerCase().includes("rate limit") ||
        error.message?.toLowerCase().includes("rate_limit");
      toast({
        title: "Sign up failed",
        description: isRateLimit
          ? "Too many sign-up emails sent. Please try again in an hour, or turn off “Confirm email” in Supabase (Auth → Email) for local testing."
          : error.message,
        variant: "destructive",
      });
      return;
    }

    if (signUpData.user) {
      const { error: roleError } = await supabase.from("user_roles").insert({
        user_id: signUpData.user.id,
        role: signupRole,
      });
      if (roleError) {
        console.error("Failed to assign role:", roleError);
      }
    }

    setLoading(false);
    const needsConfirmation = !signUpData.session && signUpData.user;
    toast({
      title: "Account created",
      description: needsConfirmation
        ? "Check your email and click the confirmation link. Then return here to sign in."
        : "Please sign in with your email and password.",
    });
    const asParam = signupRole === "mentor" ? "&as=mentor" : "";
    navigate(`/auth?from=signup${asParam}`, { replace: true });
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // ✅ PRIORITY 2: Rate limiting for authentication (prevent brute force)
    const rateLimit = rateLimiter.check(rateLimits.authLogin);
    if (!rateLimit.allowed) {
      const waitTime = formatWaitTime(rateLimit.waitMs);
      toast({
        title: "Too many login attempts",
        description: `Please wait ${waitTime} before trying again. This protects your account from brute force attacks.`,
        variant: "destructive",
      });
      return;
    }
    
    if (!email || !password) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }
    setLoading(true);
    const emailNormalized = email.trim().toLowerCase();
    const { error } = await supabase.auth.signInWithPassword({
      email: emailNormalized,
      password,
    });
    setLoading(false);
    if (error) {
      // Block user temporarily after 5 failed attempts (15 minute lockout)
      const loginAttempts = rateLimiter.getStatus(rateLimits.authLogin);
      if (loginAttempts.remaining === 0) {
        rateLimiter.block(rateLimits.authLogin, 15 * 60 * 1000); // 15 minutes
        toast({
          title: "Account temporarily locked",
          description: "Too many failed login attempts. Your account is locked for 15 minutes for security.",
          variant: "destructive",
        });
        return;
      }
      
      const isUnconfirmed =
        error.message?.toLowerCase().includes("email not confirmed") ||
        error.message?.toLowerCase().includes("confirm your email");
      toast({
        title: "Sign in failed",
        description: isUnconfirmed
          ? "Please confirm your email first. Check your inbox (and spam) for the confirmation link from us, then try signing in again."
          : `${error.message}${loginAttempts.remaining > 0 ? ` (${loginAttempts.remaining} attempts remaining)` : ''}`,
        variant: "destructive",
      });
    } else {
      // Reset rate limit on successful login
      rateLimiter.reset(rateLimits.authLogin.key);
    }
  };

  const fromSignup = new URLSearchParams(location.search).get("from") === "signup";
  const asMentor = new URLSearchParams(location.search).get("as") === "mentor";
  const roleChanged = new URLSearchParams(location.search).get("role_changed") === "true";
  const defaultTab: AuthMode = isSignupOnly
    ? isMentorSignup
      ? "signup-mentor"
      : "signup-learner"
    : "signin";

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-md mx-auto pt-32 px-4">
        <Tabs defaultValue={defaultTab} className="w-full" key={pathname}>
          {isSignupOnly && (
            <TabsList className="grid w-full grid-cols-1 w-auto">
              <TabsTrigger value={defaultTab} className="pointer-events-none">
                {isMentorSignup ? "Mentor sign up" : "Learner sign up"}
              </TabsTrigger>
            </TabsList>
          )}

          <TabsContent value="signin">
            {roleChanged && (
              <Card className="mb-4 border-primary/50 bg-primary/5">
                <CardContent className="pt-6">
                  <p className="text-sm font-medium">
                    Your role has been changed
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Please sign in again to access your new dashboard with updated permissions.
                  </p>
                </CardContent>
              </Card>
            )}
            {fromSignup && (
              <Card className="mb-4 border-primary/50 bg-primary/5">
                <CardContent className="pt-6">
                  <p className="text-sm font-medium">
                    {asMentor ? "You registered as a mentor" : "Verification link sent to your email"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {asMentor
                      ? "A verification link was sent to your email. After confirming, sign in to access your mentor dashboard."
                      : "Check your inbox (and spam folder) and click the link to activate your account. Then sign in below."}
                  </p>
                </CardContent>
              </Card>
            )}
            <Card>
              <CardHeader>
                <CardTitle>Welcome Back</CardTitle>
                <CardDescription>Sign in to your account to continue</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signin-email">Email</Label>
                    <Input
                      id="signin-email"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signin-password">Password</Label>
                    <Input
                      id="signin-password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Signing in..." : "Sign In"}
                  </Button>
                  {!isSignupOnly && (
                    <p className="text-sm text-muted-foreground text-center pt-2">
                      Don&apos;t have an account?{" "}
                      <span className="inline-flex gap-2">
                        <button
                          type="button"
                          className="text-primary underline"
                          onClick={() => navigate("/auth/learner")}
                        >
                          Join as Learner
                        </button>
                        {" · "}
                        <button
                          type="button"
                          className="text-primary underline"
                          onClick={() => navigate("/auth/mentor")}
                        >
                          Become a Mentor
                        </button>
                      </span>
                    </p>
                  )}
                  {isSignupOnly && (
                    <p className="text-sm text-muted-foreground text-center pt-2">
                      Already have an account?{" "}
                      <button
                        type="button"
                        className="text-primary underline"
                        onClick={() => navigate("/auth")}
                      >
                        Sign in
                      </button>
                    </p>
                  )}
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="signup-mentor">
            <Card>
              <CardHeader>
                <CardTitle>Become a Mentor</CardTitle>
                <CardDescription>Create an account to register as a mentor</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSignUp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-name">Full Name (optional)</Label>
                    <Input
                      id="signup-name"
                      type="text"
                      placeholder="John Doe"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input
                      id="signup-email"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input
                      id="signup-password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Creating account..." : "Sign Up as Mentor"}
                  </Button>
                  <p className="text-sm text-muted-foreground text-center">
                    Already have an account?{" "}
                    <button
                      type="button"
                      className="text-primary underline"
                      onClick={() => navigate("/auth")}
                    >
                      Sign in
                    </button>
                  </p>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="signup-learner">
            <Card>
              <CardHeader>
                <CardTitle>Join as Learner</CardTitle>
                <CardDescription>Create an account to start learning from mentors</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSignUp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-name-learner">Full Name (optional)</Label>
                    <Input
                      id="signup-name-learner"
                      type="text"
                      placeholder="John Doe"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email-learner">Email</Label>
                    <Input
                      id="signup-email-learner"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password-learner">Password</Label>
                    <Input
                      id="signup-password-learner"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Creating account..." : "Sign Up as Learner"}
                  </Button>
                  <p className="text-sm text-muted-foreground text-center">
                    Already have an account?{" "}
                    <button
                      type="button"
                      className="text-primary underline"
                      onClick={() => navigate("/auth")}
                    >
                      Sign in
                    </button>
                  </p>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Auth;
