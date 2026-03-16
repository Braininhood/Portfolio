import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Star, ArrowRight, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface Mentor {
  id: string;
  name: string;
  title: string;
  expertise: string[];
  category: string;
  experience: string;
  bio: string;
  price?: number;
  rating?: number;
  image_url?: string;
}

interface Recommendation {
  mentorId: string;
  matchScore: number;
  reasoning: string;
  keyBenefits: string[];
  mentor: Mentor;
}

interface RecommendationsCardProps {
  recommendations: Recommendation[];
  loading: boolean;
  onCompleteProfile?: () => void;
}

export const RecommendationsCard = ({ recommendations, loading, onCompleteProfile }: RecommendationsCardProps) => {
  const navigate = useNavigate();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            <CardTitle>AI-Powered Recommendations</CardTitle>
          </div>
          <CardDescription>Finding the perfect mentors for you...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-24 bg-muted rounded-lg"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            <CardTitle>AI-Powered Recommendations</CardTitle>
          </div>
          <CardDescription>Complete your profile to get personalized mentor recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Add your interests, skill level, and goals to receive AI-powered mentor matches.
          </p>
          <Button onClick={onCompleteProfile}>
            Complete Profile
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent animate-pulse" />
          <CardTitle>AI-Powered Recommendations</CardTitle>
        </div>
        <CardDescription>Personalized matches based on your profile</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {recommendations.map((rec, index) => (
          <Card key={rec.mentorId} className="overflow-hidden border-accent/20 hover:border-accent/40 transition-all">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/10 text-accent font-bold">
                    #{index + 1}
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">{rec.mentor.name}</h4>
                    <p className="text-sm text-muted-foreground">{rec.mentor.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {rec.mentor.category}
                      </Badge>
                      {rec.mentor.price && (
                        <span className="text-xs text-muted-foreground">
                          ${rec.mentor.price}/hr
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <Badge variant="secondary" className="gap-1">
                  <Star className="h-3 w-3 fill-accent text-accent" />
                  {rec.matchScore}% Match
                </Badge>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium mb-1">Why this mentor?</p>
                  <p className="text-sm text-muted-foreground">{rec.reasoning}</p>
                </div>

                <div>
                  <p className="text-sm font-medium mb-2">Key Benefits:</p>
                  <ul className="space-y-1">
                    {rec.keyBenefits.map((benefit, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-accent mt-1">•</span>
                        <span>{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex flex-wrap gap-2 pt-2">
                  {rec.mentor.expertise.slice(0, 3).map((skill, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>

                <Button 
                  className="w-full mt-4" 
                  onClick={() => navigate(`/mentors/${rec.mentor.id}`)}
                >
                  View Profile
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </CardContent>
    </Card>
  );
};