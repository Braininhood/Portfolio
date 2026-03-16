import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ShoppingCart, Loader2, Lock, CheckCircle2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

interface ProductCheckoutProps {
  productId: string;
  productTitle: string;
  productDescription: string;
  productPrice: number;
  productImage?: string;
  mentorName: string;
}

export const ProductCheckout = ({
  productId,
  productTitle,
  productDescription,
  productPrice,
  productImage,
  mentorName,
}: ProductCheckoutProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPurchased, setIsPurchased] = useState(false);
  const [checkingPurchase, setCheckingPurchase] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkPurchased = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.user) {
        setCheckingPurchase(false);
        return;
      }
      const { data } = await supabase
        .from("product_purchases")
        .select("id")
        .eq("product_id", productId)
        .eq("buyer_id", session.user.id)
        .eq("status", "completed")
        .maybeSingle();
      setIsPurchased(!!data);
      setCheckingPurchase(false);
    };
    checkPurchased();
  }, [productId]);

  const handlePurchase = async () => {
    if (isPurchased) return;
    setIsProcessing(true);

    try {
      const { data: { session: authSession }, error: refreshErr } = await supabase.auth.refreshSession();
      if (refreshErr || !authSession?.access_token) {
        toast.error("Please sign in to purchase", {
          description: "You need to be logged in to buy digital products.",
        });
        navigate("/auth");
        return;
      }

      const { data, error } = await supabase.functions.invoke("create-product-checkout", {
        body: {
          productId,
        },
        headers: { Authorization: `Bearer ${authSession.access_token}` },
      });

      if (error) {
        const status = (error as { context?: { status?: number; json?: () => Promise<{ error?: string }> } })?.context?.status;
        if (status === 401) {
          toast.error("Session expired or invalid. Please sign in again.");
          navigate("/auth");
          return;
        }
        let serverMessage = error.message;
        const ctx = (error as { context?: { json?: () => Promise<{ error?: string }> } }).context;
        if (typeof ctx?.json === "function") {
          try {
            const body = await ctx.json();
            if (body?.error) serverMessage = body.error;
          } catch {
            // ignore
          }
        }
        if (status === 409 || (typeof serverMessage === "string" && serverMessage.toLowerCase().includes("already purchased"))) {
          setIsPurchased(true);
          setIsProcessing(false);
          return;
        }
        throw new Error(serverMessage);
      }

      // Redirect to Stripe Checkout
      if (data?.url) {
        window.location.href = data.url;
      } else {
        throw new Error("No checkout URL returned");
      }
    } catch (error: any) {
      console.error("Error creating checkout:", error);
      toast.error("Purchase Failed", {
        description: error.message || "Failed to initiate checkout. Please try again.",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="border-2 border-accent/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShoppingCart className="h-5 w-5" />
          Purchase Product
        </CardTitle>
        <CardDescription>
          Secure checkout powered by Stripe
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {productImage && (
          <div className="w-full h-48 rounded-lg overflow-hidden">
            <img
              src={productImage}
              alt={productTitle}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        <div className="space-y-2">
          <h3 className="font-semibold text-lg">{productTitle}</h3>
          <p className="text-sm text-muted-foreground">{productDescription}</p>
          <p className="text-sm text-muted-foreground">
            Created by <span className="font-medium">{mentorName}</span>
          </p>
        </div>

        <div className="pt-4 border-t">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-muted-foreground">Total Price</span>
            <span className="text-3xl font-bold">${productPrice.toFixed(2)}</span>
          </div>

          {isPurchased ? (
            <Button
              size="lg"
              className="w-full"
              variant="secondary"
              onClick={() => navigate("/learner/dashboard")}
            >
              <CheckCircle2 className="mr-2 h-5 w-5" />
              Already in your dashboard – view in dashboard
            </Button>
          ) : (
            <Button
              onClick={handlePurchase}
              disabled={isProcessing || checkingPurchase}
              size="lg"
              className="w-full"
              variant="hero"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : checkingPurchase ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  ...
                </>
              ) : (
                <>
                  <Lock className="mr-2 h-5 w-5" />
                  Buy Now - ${productPrice.toFixed(2)}
                </>
              )}
            </Button>
          )}
        </div>

        <div className="pt-4 border-t">
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Lock className="h-4 w-4" />
              <span>Secure payment via Stripe</span>
            </li>
            <li className="flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              <span>Instant access after purchase</span>
            </li>
            <li className="flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              <span>Download anytime from your dashboard</span>
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
