import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Star } from "lucide-react";

interface ProductReview {
  id: string;
  user_name: string;
  user_avatar: string | null;
  rating: number;
  comment: string | null;
  created_at: string;
}

interface ProductReviewCardProps {
  review: ProductReview;
}

const ProductReviewCard = ({ review }: ProductReviewCardProps) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <Card className="hover:shadow-medium transition-shadow duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <img
              src={review.user_avatar || "/placeholder.svg"}
              alt={review.user_name}
              className="w-10 h-10 rounded-full object-cover"
            />
            <div>
              <h4 className="font-semibold text-sm">{review.user_name}</h4>
              <p className="text-xs text-muted-foreground">{formatDate(review.created_at)}</p>
            </div>
          </div>
          <div className="flex items-center gap-0.5">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                size={14}
                className={i < review.rating ? "text-accent fill-accent" : "text-muted"}
              />
            ))}
          </div>
        </div>
      </CardHeader>
      {review.comment && (
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground">{review.comment}</p>
        </CardContent>
      )}
    </Card>
  );
};

export default ProductReviewCard;
