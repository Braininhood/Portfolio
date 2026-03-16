import { useState, useEffect, useRef } from "react";
import { supabase } from "@/integrations/supabase/client";

export type AppRole = "admin" | "mentor" | "learner";

export const useUserRole = () => {
  const [roles, setRoles] = useState<AppRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [hasMentorProfile, setHasMentorProfile] = useState(false);
  
  // Use ref to track previous roles without causing re-renders
  const previousRolesRef = useRef<string>("");

  useEffect(() => {
    const fetchUserRoles = async () => {
      setLoading(true);
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.user) {
          setRoles([]);
          setUserId(null);
          setHasMentorProfile(false);
          setLoading(false);
          return;
        }
        setUserId(session.user.id);
        const [rolesRes, mentorRes] = await Promise.all([
          supabase.from("user_roles").select("role").eq("user_id", session.user.id),
          supabase.from("mentor_profiles").select("id").eq("user_id", session.user.id).maybeSingle(),
        ]);
        if (rolesRes.error) {
          const msg = rolesRes.error?.message ?? "";
          if (msg && !msg.includes("NetworkError")) {
            console.warn("Error fetching user roles:", msg);
          }
          setRoles([]);
        } else {
          const newRoles = rolesRes.data?.map((r) => r.role as AppRole) || [];
          const newRoleString = newRoles.sort().join(',');
          
          // Check if roles changed (only if we had previous roles loaded)
          if (previousRolesRef.current && previousRolesRef.current !== newRoleString) {
            console.log("🔄 Role change detected!");
            console.log("   Old roles:", previousRolesRef.current);
            console.log("   New roles:", newRoleString);
            
            // Determine target dashboard based on new role
            const targetUrl = newRoles.includes("admin") 
              ? "/admin" 
              : newRoles.includes("mentor") 
                ? "/mentor/dashboard" 
                : "/learner/dashboard";
            
            // Store redirect and force sign-out
            sessionStorage.setItem("post_role_change_redirect", targetUrl);
            localStorage.setItem("post_role_change_redirect", targetUrl);
            
            console.log("🔓 Forcing sign-out due to role change...");
            console.log("📦 Target redirect:", targetUrl);
            
            // Sign out and redirect
            setTimeout(async () => {
              await supabase.auth.signOut();
              window.location.href = "/auth?role_changed=true";
            }, 1000);
            
            return; // Don't update state, we're signing out
          }
          
          // Update ref for next comparison
          previousRolesRef.current = newRoleString;
          setRoles(newRoles);
        }
        setHasMentorProfile(!!mentorRes?.data);
      } catch (e) {
        console.error("useUserRole:", e);
        setRoles([]);
        setHasMentorProfile(false);
      }
      setLoading(false);
    };

    fetchUserRoles();

    // Subscribe to auth changes
    let authSubscription: { unsubscribe: () => void } = { unsubscribe: () => {} };
    try {
      const { data: { subscription: sub } } = supabase.auth.onAuthStateChange(() => {
        fetchUserRoles();
      });
      authSubscription = sub;
    } catch (e) {
      console.error("useUserRole onAuthStateChange:", e);
    }
    
    // Poll for role changes every 3 seconds
    console.log("🔄 Starting role change polling (every 3 seconds)");
    const pollInterval = setInterval(() => {
      fetchUserRoles();
    }, 3000); // Check every 3 seconds

    return () => {
      authSubscription.unsubscribe();
      clearInterval(pollInterval);
      console.log("🛑 Stopped role change polling");
    };
  }, []);

  const hasRole = (role: AppRole): boolean => {
    return roles.includes(role);
  };

  const isAdmin = hasRole("admin");
  const isMentor = hasRole("mentor");  // ✅ Only check actual role, not profile
  const isLearner = hasRole("learner");

  return {
    roles,
    loading,
    userId,
    hasRole,
    isAdmin,
    isMentor,
    isLearner,
    hasMentorProfile,  // Still available but not used for isMentor check
  };
};
