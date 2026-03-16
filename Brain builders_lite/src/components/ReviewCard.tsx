import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Star } from "lucide-react";
import { Review } from "@/data/mentors";

interface ReviewCardProps {
  review: Review;
}

const ReviewCard = ({ review }: ReviewCardProps) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <Card className="hover:shadow-medium transition-shadow duration-300">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <img
              src={review.userAvatar}
              alt={review.userName}
              className="w-12 h-12 rounded-full object-cover"
            />
            <div>
              <h4 className="font-semibold">{review.userName}</h4>
              <p className="text-sm text-muted-foreground">{formatDate(review.date)}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                size={16}
                className={i < review.rating ? "text-accent fill-accent" : "text-muted"}
              />
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{review.comment}</p>
      </CardContent>
    </Card>
  );
};

export default ReviewCard;