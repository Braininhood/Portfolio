import { Brain, Calendar, GraduationCap, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import aiMatchingImage from "@/assets/ai-matching.jpg";
import consultationImage from "@/assets/consultation.jpg";
import learningPathImage from "@/assets/learning-path.jpg";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Matching",
    description: "Our advanced AI analyzes your goals, skills, and challenges to connect you with the perfect mentors and courses.",
    image: aiMatchingImage,
  },
  {
    icon: Calendar,
    title: "1:1 Consultations",
    description: "Book personalized sessions with industry experts. Get tailored guidance on your specific challenges.",
    image: consultationImage,
  },
  {
    icon: GraduationCap,
    title: "Premium Courses",
    description: "Access state-of-the-art training materials. Learn at your own pace with structured learning paths.",
    image: learningPathImage,
  },
  {
    icon: TrendingUp,
    title: "Track Your Progress",
    description: "Monitor your growth with comprehensive dashboards. Celebrate milestones and achievements.",
    image: null,
  },
];

const Features = () => {
  return (
    <section className="py-24 bg-gradient-accent">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl sm:text-5xl font-display font-bold mb-4">
            Everything You Need to{" "}
            <span className="gradient-text">Grow</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            A comprehensive platform designed to accelerate your personal and professional development
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="group hover:shadow-strong transition-all duration-300 hover:-translate-y-2 border-border/50 overflow-hidden"
            >
              {feature.image && (
                <div className="h-48 overflow-hidden">
                  <img
                    src={feature.image}
                    alt={feature.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                </div>
              )}
              <CardContent className="p-6 space-y-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-primary flex items-center justify-center">
                  <feature.icon className="text-white" size={24} />
                </div>
                <h3 className="text-xl font-display font-bold">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;