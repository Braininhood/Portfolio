import { CheckCircle2 } from "lucide-react";

const steps = [
  {
    number: "01",
    title: "Create Your Profile",
    description: "Tell us about your goals, current skills, and what you want to achieve.",
  },
  {
    number: "02",
    title: "Get AI Recommendations",
    description: "Our AI analyzes your profile and suggests the best mentors and courses for you.",
  },
  {
    number: "03",
    title: "Connect & Learn",
    description: "Book consultations, enroll in courses, and start your growth journey.",
  },
  {
    number: "04",
    title: "Track Progress",
    description: "Monitor your achievements and celebrate milestones as you advance.",
  },
];

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl sm:text-5xl font-display font-bold mb-4">
            How <span className="gradient-text">Brain Bulders</span> Works
          </h2>
          <p className="text-xl text-muted-foreground">
            Your personalized learning journey in four simple steps
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <div
              key={index}
              className="relative group"
            >
              {/* Connector Line (hidden on mobile) */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-16 left-1/2 w-full h-0.5 bg-gradient-primary opacity-30" />
              )}

              <div className="relative z-10 text-center space-y-4">
                {/* Number Circle */}
                <div className="inline-flex w-32 h-32 rounded-full bg-gradient-primary items-center justify-center group-hover:shadow-glow transition-all duration-300 group-hover:scale-110">
                  <span className="text-4xl font-display font-bold text-white">
                    {step.number}
                  </span>
                </div>

                {/* Content */}
                <div className="space-y-2">
                  <h3 className="text-xl font-display font-bold">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground">
                    {step.description}
                  </p>
                </div>

                {/* Check Icon */}
                <CheckCircle2 className="inline-block text-accent" size={24} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;