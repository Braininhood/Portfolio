import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Star, Clock, MessageSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Mentor } from "@/data/mentors";

interface MentorCardProps {
  mentor: Mentor;
}

const MentorCard = ({ mentor }: MentorCardProps) => {
  const navigate = useNavigate();
  return (
    <Card 
      className="group hover:shadow-strong transition-all duration-300 hover:-translate-y-1 overflow-hidden cursor-pointer"
      onClick={() => navigate(`/mentors/${mentor.id}`)}
    >
      {/* Image Section */}
      <div className="relative h-64 overflow-hidden bg-muted">
        <img
          src={mentor.image}
          alt={mentor.name}
          className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
        />
        <div className="absolute top-4 right-4">
          <Badge className="bg-accent text-accent-foreground shadow-medium">
            {mentor.category}
          </Badge>
        </div>
      </div>

      <CardContent className="p-6 space-y-4">
        {/* Name & Title */}
        <div>
          <h3 className="text-xl font-display font-bold mb-1">{mentor.name}</h3>
          <p className="text-muted-foreground text-sm">{mentor.title}</p>
        </div>

        {/* Rating */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Star className="text-accent fill-accent" size={16} />
            <span className="font-semibold">{mentor.rating}</span>
          </div>
          <span className="text-muted-foreground text-sm">
            ({mentor.reviewCount} reviews)
          </span>
        </div>

        {/* Bio */}
        <p className="text-sm text-muted-foreground line-clamp-2">
          {mentor.bio}
        </p>

        {/* Expertise Tags */}
        <div className="flex flex-wrap gap-2">
          {mentor.expertise.slice(0, 3).map((skill, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {skill}
            </Badge>
          ))}
          {mentor.expertise.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{mentor.expertise.length - 3}
            </Badge>
          )}
        </div>

        {/* Availability & Languages */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock size={14} />
            <span>{mentor.availability}</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageSquare size={14} />
            <span>{mentor.languages.join(", ")}</span>
          </div>
        </div>

        {/* Price & CTA */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div>
            <div className="text-2xl font-display font-bold">
              ${mentor.price}
            </div>
            <div className="text-xs text-muted-foreground">per session</div>
          </div>
          <Button 
            variant="hero" 
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/mentors/${mentor.id}`);
            }}
          >
            View Profile
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default MentorCard;