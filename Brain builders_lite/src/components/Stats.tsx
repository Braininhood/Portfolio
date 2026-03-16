import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Users, Award, DollarSign } from "lucide-react";

const stats = [
  {
    icon: DollarSign,
    value: "$500B+",
    label: "Global Market Size",
    description: "Personal development market growing 10%+ annually",
  },
  {
    icon: Users,
    value: "86%",
    label: "Seek Coaching",
    description: "Professionals want guidance but struggle to access quality options",
  },
  {
    icon: TrendingUp,
    value: "73%",
    label: "Would Invest",
    description: "Ready to invest in personal development with trusted guidance",
  },
  {
    icon: Award,
    value: "80%",
    label: "Gross Margins",
    description: "From course and consultation sales",
  },
];

const Stats = () => {
  return (
    <section className="py-24 bg-primary text-primary-foreground relative overflow-hidden">
      {/* Decorative Background */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-96 h-96 bg-accent rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl sm:text-5xl font-display font-bold mb-4">
            The Numbers Speak for Themselves
          </h2>
          <p className="text-xl opacity-90">
            Join a thriving marketplace transforming personal development
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <Card
              key={index}
              className="bg-primary-foreground/10 border-primary-foreground/20 hover:bg-primary-foreground/20 transition-all duration-300 hover:scale-105"
            >
              <CardContent className="p-6 text-center space-y-4">
                <div className="w-16 h-16 mx-auto rounded-full bg-accent/20 flex items-center justify-center">
                  <stat.icon className="text-accent" size={32} />
                </div>
                <div className="text-4xl font-display font-bold">
                  {stat.value}
                </div>
                <div className="text-lg font-semibold">
                  {stat.label}
                </div>
                <p className="text-sm opacity-80">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Stats;