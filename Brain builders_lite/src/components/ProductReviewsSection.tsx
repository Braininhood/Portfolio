import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Star, MessageSquare } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import ProductReviewCard from "./ProductReviewCard";
import ProductReviewForm from "./ProductReviewForm";

interface ProductReview {
  id: string;
  user_id: string;
  user_name: string;
  user_avatar: string | null;
  rating: number;
  comment: string | null;
  created_at: string;
}

interface ProductReviewsSectionProps {
  productId: string;
  productTitle: string;
  averageRating: number;
  reviewCount: number;
}

const ProductReviewsSection = ({
  productId,
  productTitle,
  averageRating,
  reviewCount,
}: ProductReviewsSectionProps) => {
  const [reviews, setReviews] = useState<ProductReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [canReview, setCanReview] = useState(false);
  const [userReview, setUserReview] = useState<ProductReview | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  useEffect(() => {
    loadReviewsAndCheckPurchase();
  }, [productId]);

  const loadReviewsAndCheckPurchase = async () => {
    setLoading(true);

    // Get current user
    const { data: { user } } = await supabase.auth.getUser();
    setCurrentUserId(user?.id || null);

    // Fetch reviews
    const { data: reviewsData } = await supabase
      .from("product_reviews")
      .select("*")
      .eq("product_id", productId)
      .order("created_at", { ascending: false });

    if (reviewsData) {
      setReviews(reviewsData);
      
      // Check if user already reviewed
      if (user) {
        const existingReview = reviewsData.find(r => r.user_id === user.id);
        setUserReview(existingReview || null);
      }
    }

    // Check if user can review (has purchased)
    if (user) {
      const { data: purchase } = await supabase
        .from("product_purchases")
        .select("id")
        .eq("product_id", productId)
        .eq("buyer_id", user.id)
        .eq("status", "completed")
        .maybeSingle();

      setCanReview(!!purchase);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground text-center">Loading reviews...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Rating Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare size={20} />
            Customer Reviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-4xl font-bold">
                {averageRating > 0 ? averageRating.toFixed(1) : "—"}
              </div>
              <div className="flex items-center gap-0.5 justify-center mt-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    size={16}
                    className={
                      i < Math.round(averageRating)
                        ? "text-accent fill-accent"
                        : "text-muted"
                    }
                  />
                ))}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {reviewCount} {reviewCount === 1 ? "review" : "reviews"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Review Form (only for purchasers) */}
      {canReview && (
        <ProductReviewForm
          productId={productId}
          productTitle={productTitle}
          onReviewSubmitted={loadReviewsAndCheckPurchase}
          existingReview={userReview ? {
            id: userReview.id,
            rating: userReview.rating,
            comment: userReview.comment,
          } : null}
        />
      )}

      {/* Reviews List */}
      <div className="space-y-4">
        {reviews.length > 0 ? (
          reviews.map((review) => (
            <ProductReviewCard key={review.id} review={review} />
          ))
        ) : (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-muted-foreground">
                No reviews yet. Be the first to review this product!
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ProductReviewsSection;
