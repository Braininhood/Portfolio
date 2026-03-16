import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useToast } from "@/hooks/use-toast";
import { ShoppingBag, Star, Loader2, ExternalLink, CheckCircle2 } from "lucide-react";

interface MentorProfile {
  id: string;
  name: string;
  title: string;
  bio: string;
  image_url: string | null;
  rating: number | null;
  review_count: number | null;
  username: string | null;
}

interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  preview_image_url: string | null;
  file_type: string;
  sales_count: number;
}

const MentorShop = () => {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const [mentor, setMentor] = useState<MentorProfile | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchaseLoading, setPurchaseLoading] = useState<string | null>(null);
  const [purchasedProductIds, setPurchasedProductIds] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  useEffect(() => {
    if (username) {
      loadShopData();
    }
  }, [username]);

  const loadShopData = async () => {
    if (!username) return;
    setLoading(true);

    // Load mentor profile by username
    const { data: mentorData, error: mentorError } = await supabase
      .from("mentor_profiles")
      .select("id, name, title, bio, image_url, rating, review_count, username")
      .eq("username", username)
      .eq("is_active", true)
      .maybeSingle();

    if (mentorError || !mentorData) {
      setLoading(false);
      return;
    }

    setMentor(mentorData);

    // Load active products
    const { data: productsData } = await supabase
      .from("mentor_products")
      .select("id, title, description, price, preview_image_url, file_type, sales_count")
      .eq("mentor_id", mentorData.id)
      .eq("is_active", true)
      .order("created_at", { ascending: false });

    setProducts(productsData || []);

    // Load which of these products the current user has already purchased
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.user && (productsData?.length ?? 0) > 0) {
      const ids = (productsData ?? []).map((p) => p.id);
      const { data: purchases } = await supabase
        .from("product_purchases")
        .select("product_id")
        .eq("buyer_id", session.user.id)
        .eq("status", "completed")
        .in("product_id", ids);
      setPurchasedProductIds(new Set((purchases ?? []).map((p) => p.product_id)));
    }

    setLoading(false);
  };

  const handlePurchase = async (product: Product) => {
    if (purchasedProductIds.has(product.id)) return;
    setPurchaseLoading(product.id);

    try {
      const { data: { session }, error: refreshErr } = await supabase.auth.refreshSession();
      if (refreshErr || !session?.access_token) {
        navigate(`/auth?redirect=/shop/${username}`);
        return;
      }

      const { data, error } = await supabase.functions.invoke("create-product-checkout", {
        body: {
          productId: product.id,
          successUrl: `${window.location.origin}/learner/purchase-success`,
          cancelUrl: window.location.href,
        },
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (error) {
        const status = (error as { context?: { status?: number; json?: () => Promise<{ error?: string }> } })?.context?.status;
        if (status === 401) {
          toast({
            title: "Session expired or invalid",
            description: "Please sign in again.",
            variant: "destructive",
          });
          navigate("/auth");
          return;
        }
        const ctx = (error as { context?: { json?: () => Promise<{ error?: string }> } }).context;
        let serverMessage = error.message;
        if (typeof ctx?.json === "function") {
          try {
            const body = await ctx.json();
            if (body?.error) serverMessage = body.error;
          } catch {
            // ignore
          }
        }
        if (status === 409 || (typeof serverMessage === "string" && serverMessage.toLowerCase().includes("already purchased"))) {
          setPurchasedProductIds((prev) => new Set(prev).add(product.id));
          return;
        }
        throw new Error(serverMessage);
      }

      if (data?.url) {
        window.open(data.url, "_blank");
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to start checkout",
        variant: "destructive",
      });
    } finally {
      setPurchaseLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container pt-32 px-4 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!mentor) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container pt-32 px-4 text-center">
          <h1 className="text-2xl font-bold mb-4">Shop Not Found</h1>
          <p className="text-muted-foreground mb-8">
            This mentor shop doesn't exist or is no longer available.
          </p>
          <Button onClick={() => navigate("/mentors")}>Browse Mentors</Button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-32 px-4 pb-16">
        {/* Mentor Header */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex flex-col md:flex-row items-center gap-6 text-center md:text-left">
            <Avatar className="h-24 w-24">
              <AvatarImage src={mentor.image_url || undefined} alt={mentor.name} />
              <AvatarFallback className="text-2xl">
                {mentor.name.split(" ").map((n) => n[0]).join("")}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-3xl font-bold mb-2">{mentor.name}'s Shop</h1>
              <p className="text-muted-foreground mb-2">{mentor.title}</p>
              <div className="flex items-center justify-center md:justify-start gap-4">
                {mentor.rating && (
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span className="font-medium">{mentor.rating.toFixed(1)}</span>
                    {mentor.review_count && (
                      <span className="text-muted-foreground">
                        ({mentor.review_count} reviews)
                      </span>
                    )}
                  </div>
                )}
                <Button
                  variant="link"
                  className="p-0 h-auto"
                  onClick={() => navigate(`/mentors/${mentor.id}`)}
                >
                  View Profile <ExternalLink className="ml-1 h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {products.length === 0 ? (
          <div className="text-center py-16">
            <ShoppingBag className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No products yet</h2>
            <p className="text-muted-foreground">
              This mentor hasn't added any products yet. Check back later!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {products.map((product) => (
              <Card key={product.id} className="overflow-hidden group hover:shadow-lg transition-shadow">
                {/* Product Image */}
                <div className="aspect-video bg-muted overflow-hidden">
                  {product.preview_image_url ? (
                    <img
                      src={product.preview_image_url}
                      alt={product.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ShoppingBag className="h-12 w-12 text-muted-foreground" />
                    </div>
                  )}
                </div>

                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="font-semibold line-clamp-1">{product.title}</h3>
                      <Badge variant="secondary" className="mt-1">
                        {product.file_type.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xl font-bold text-primary">
                      ${Number(product.price).toFixed(2)}
                    </p>
                  </div>

                  <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                    {product.description}
                  </p>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {product.sales_count} {product.sales_count === 1 ? "sale" : "sales"}
                    </span>
                    {purchasedProductIds.has(product.id) ? (
                      <Button size="sm" variant="secondary" disabled className="gap-1.5">
                        <CheckCircle2 className="h-4 w-4" />
                        Already in your dashboard
                      </Button>
                    ) : (
                      <Button
                        onClick={() => handlePurchase(product)}
                        disabled={purchaseLoading === product.id}
                        size="sm"
                      >
                        {purchaseLoading === product.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          "Buy Now"
                        )}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default MentorShop;
