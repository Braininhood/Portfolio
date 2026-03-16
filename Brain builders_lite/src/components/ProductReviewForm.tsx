import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Star, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface ProductReviewFormProps {
  productId: string;
  productTitle: string;
  onReviewSubmitted: () => void;
  existingReview?: {
    id: string;
    rating: number;
    comment: string | null;
  } | null;
}

const ProductReviewForm = ({ 
  productId, 
  productTitle, 
  onReviewSubmitted,
  existingReview 
}: ProductReviewFormProps) => {
  const [rating, setRating] = useState(existingReview?.rating || 0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [comment, setComment] = useState(existingReview?.comment || "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.error("Please select a rating");
      return;
    }

    setIsSubmitting(true);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        toast.error("Please sign in to leave a review");
        return;
      }

      // Get user profile for name/avatar
      const { data: profile } = await supabase
        .from("profiles")
        .select("full_name, avatar_url")
        .eq("id", user.id)
        .single();

      const reviewData = {
        product_id: productId,
        user_id: user.id,
        rating,
        comment: comment.trim() || null,
        user_name: profile?.full_name || user.email?.split("@")[0] || "Anonymous",
        user_avatar: profile?.avatar_url,
      };

      if (existingReview) {
        // Update existing review
        const { error } = await supabase
          .from("product_reviews")
          .update({
            rating,
            comment: comment.trim() || null,
            updated_at: new Date().toISOString(),
          })
          .eq("id", existingReview.id);

        if (error) throw error;
        toast.success("Review updated successfully!");
      } else {
        // Create new review
        const { error } = await supabase
          .from("product_reviews")
          .insert(reviewData);

        if (error) {
          if (error.code === "23505") {
            toast.error("You've already reviewed this product");
          } else {
            throw error;
          }
          return;
        }
        toast.success("Review submitted successfully!");
      }

      onReviewSubmitted();
    } catch (error) {
      console.error("Error submitting review:", error);
      toast.error("Failed to submit review");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          {existingReview ? "Update Your Review" : "Rate This Product"}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{productTitle}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Your Rating</label>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredRating(star)}
                onMouseLeave={() => setHoveredRating(0)}
                className="p-1 transition-transform hover:scale-110"
              >
                <Star
                  size={28}
                  className={
                    star <= (hoveredRating || rating)
                      ? "text-accent fill-accent"
                      : "text-muted-foreground"
                  }
                />
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">
            Your Review (optional)
          </label>
          <Textarea
            placeholder="Share your experience with this product..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
        </div>

        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || rating === 0}
          className="w-full"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : existingReview ? (
            "Update Review"
          ) : (
            "Submit Review"
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

export default ProductReviewForm;
