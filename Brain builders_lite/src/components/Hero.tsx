import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Sparkles, Bot, Calendar, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useUserRole } from "@/hooks/useUserRole";

const Hero = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<{ id: string } | null>(null);
  const [heroImage, setHeroImage] = useState<string | null>(null);
  const { isMentor, isAdmin } = useUserRole();
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setUser(session?.user ?? null));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_, session) => setUser(session?.user ?? null));
    return () => subscription.unsubscribe();
  }, []);
  useEffect(() => {
    import("@/assets/hero-bg.jpg").then((m) => setHeroImage(m.default)).catch(() => setHeroImage(null));
  }, []);
  const dashboardPath = user && isAdmin ? "/admin" : user && isMentor ? "/mentor/dashboard" : "/learner/dashboard";
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <div
          className="absolute inset-0 bg-cover bg-center bg-muted"
          style={heroImage ? { backgroundImage: `url(${heroImage})` } : undefined}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/80 to-background" />
      </div>

      {/* Decorative Elements */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-accent/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-primary opacity-20 rounded-full blur-3xl animate-pulse delay-1000" />

      {/* Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm font-medium animate-fade-in">
            <Sparkles size={16} />
            AI-Powered Mentor Matching
          </div>

          {/* Headline */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display font-bold leading-tight animate-fade-in-up">
            Unlock Your Full Potential with{" "}
            <span className="gradient-text">Expert Mentors</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl sm:text-2xl text-muted-foreground max-w-3xl mx-auto animate-fade-in-up animation-delay-200">
            Connect with industry leaders in Business, Tech, and Creator industries. Personalized learning paths powered by AI.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up animation-delay-400">
            {!user ? (
              <>
                <Button 
                  variant="hero" 
                  size="lg" 
                  className="text-lg px-8 py-6"
                  onClick={() => navigate('/auth/learner')}
                >
                  Join as Learner
                  <ArrowRight className="ml-2" size={20} />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="text-lg px-8 py-6"
                  onClick={() => navigate('/auth/mentor')}
                >
                  Become a Mentor
                </Button>
              </>
            ) : (
              <Button 
                variant="hero" 
                size="lg" 
                className="text-lg px-8 py-6"
                onClick={() => navigate(dashboardPath)}
              >
                Go to Dashboard
                <ArrowRight className="ml-2" size={20} />
              </Button>
            )}
          </div>

          {/* AI Twin Value Section */}
          <div className="max-w-2xl mx-auto py-8 animate-fade-in-up animation-delay-600 space-y-5">
            <p className="text-lg text-muted-foreground leading-relaxed">
              Connect with <span className="font-semibold text-foreground">AI Twins</span> of real mentors who answer your questions, recommend the right digital products and services, and help you make smarter decisions — <span className="gradient-text font-semibold">24/7</span>.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center text-sm font-medium">
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent">
                <Bot size={16} />
                Ask anything — get instant answers
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent">
                <Sparkles size={16} />
                Personalized recommendations
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent">
                <Video size={16} />
                Learn from global experts in your language
              </div>
            </div>
          </div>

          {/* Trust Indicators */}
          <p className="text-sm text-muted-foreground animate-fade-in-up animation-delay-800">
            Trusted by 10,000+ professionals worldwide
          </p>

        </div>
      </div>
    </section>
  );
};

export default Hero;