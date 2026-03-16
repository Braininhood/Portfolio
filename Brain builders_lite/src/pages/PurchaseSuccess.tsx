import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, Download, ArrowLeft } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const PurchaseSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isProcessing, setIsProcessing] = useState(false);
  const [purchaseDetails, setPurchaseDetails] = useState<any>(null);
  const [product, setProduct] = useState<any>(null);

  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (sessionId && !isProcessing && !purchaseDetails) {
      processPurchase();
    }
  }, [sessionId]);

  const processPurchase = async () => {
    setIsProcessing(true);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const headers = session?.access_token
        ? { Authorization: `Bearer ${session.access_token}` }
        : undefined;

      const { data, error } = await supabase.functions.invoke("verify-product-purchase", {
        body: { sessionId },
        headers,
      });

      if (error) throw error;

      setPurchaseDetails(data.purchase);
      setProduct(data.product);
      
      toast.success("Purchase confirmed!", {
        description: "You can now download your product.",
      });
    } catch (error) {
      console.error("Error confirming purchase:", error);
      toast.error("Error confirming purchase", {
        description: "Please contact support if payment was processed.",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!product?.file_url) {
      toast.error("Download link not available");
      return;
    }

    try {
      // Get signed URL for download
      const { data: signedData, error: signedError } = await supabase.storage
        .from("products")
        .createSignedUrl(product.file_url, 3600); // 1 hour expiry

      if (signedError) throw signedError;

      // Download the file
      window.open(signedData.signedUrl, "_blank");
      
      toast.success("Download started!");
    } catch (error) {
      console.error("Download error:", error);
      toast.error("Failed to download product");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-32 pb-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto">
            <Card className="border-2 border-accent/20">
              <CardContent className="p-12">
                <div className="text-center space-y-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 mb-4">
                    <CheckCircle2 className="text-green-600" size={48} />
                  </div>

                  <div>
                    <h1 className="text-4xl font-display font-bold mb-2">
                      Purchase Successful!
                    </h1>
                    <p className="text-xl text-muted-foreground">
                      Your digital product is ready to download
                    </p>
                  </div>

                  {isProcessing && (
                    <div className="py-8">
                      <div className="animate-pulse space-y-4">
                        <div className="h-4 bg-muted rounded w-3/4 mx-auto" />
                        <div className="h-4 bg-muted rounded w-1/2 mx-auto" />
                      </div>
                      <p className="text-sm text-muted-foreground mt-4">
                        Processing your purchase...
                      </p>
                    </div>
                  )}

                  {product && (
                    <Card className="bg-gradient-accent">
                      <CardContent className="p-6 text-left space-y-4">
                        <h2 className="text-xl font-display font-bold mb-4">
                          Product Details
                        </h2>
                        
                        {product.preview_image_url && (
                          <div className="w-full h-48 rounded-lg overflow-hidden mb-4">
                            <img
                              src={product.preview_image_url}
                              alt={product.title}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        
                        <div className="space-y-2">
                          <div>
                            <span className="text-muted-foreground">Product:</span>
                            <p className="font-semibold text-lg">{product.title}</p>
                          </div>
                          
                          <div>
                            <span className="text-muted-foreground">Description:</span>
                            <p className="text-sm">{product.description}</p>
                          </div>
                          
                          <div className="flex justify-between pt-2 border-t border-border">
                            <span className="text-muted-foreground">Amount Paid:</span>
                            <span className="font-bold text-lg">
                              ${parseFloat(product.price).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <div className="space-y-3 pt-4">
                    {product && (
                      <Button
                        variant="hero"
                        size="lg"
                        className="w-full"
                        onClick={handleDownload}
                      >
                        <Download size={20} className="mr-2" />
                        Download Product
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      size="lg"
                      className="w-full"
                      onClick={() => navigate("/learner/dashboard")}
                    >
                      <ArrowLeft size={20} className="mr-2" />
                      Go to Dashboard
                    </Button>
                  </div>

                  <div className="pt-6 border-t border-border">
                    <p className="text-sm text-muted-foreground">
                      A receipt has been sent to <strong>{purchaseDetails?.buyer_email}</strong>
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      You can download this product anytime from your dashboard.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default PurchaseSuccess;
