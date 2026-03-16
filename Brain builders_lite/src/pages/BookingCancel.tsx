import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { XCircle, ArrowLeft, Home } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const BookingCancel = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-32 pb-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto">
            <Card className="border-2 border-destructive/20">
              <CardContent className="p-12">
                <div className="text-center space-y-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-destructive/10 mb-4">
                    <XCircle className="text-destructive" size={48} />
                  </div>

                  <div>
                    <h1 className="text-4xl font-display font-bold mb-2">
                      Payment Cancelled
                    </h1>
                    <p className="text-xl text-muted-foreground">
                      Your booking was not completed
                    </p>
                  </div>

                  <Card className="bg-muted/50">
                    <CardContent className="p-6 text-left space-y-4">
                      <p className="text-muted-foreground">
                        Don't worry! Your payment was not processed and you have not been charged.
                      </p>
                      <p className="text-muted-foreground">
                        If you experienced any issues or have questions, please contact our support team.
                      </p>
                    </CardContent>
                  </Card>

                  <div className="space-y-3 pt-4">
                    <Button
                      variant="hero"
                      size="lg"
                      className="w-full"
                      onClick={() => navigate(-1)}
                    >
                      <ArrowLeft size={20} className="mr-2" />
                      Try Again
                    </Button>

                    <Button
                      variant="outline"
                      size="lg"
                      className="w-full"
                      onClick={() => navigate("/mentors")}
                    >
                      <Home size={20} className="mr-2" />
                      Browse Mentors
                    </Button>
                  </div>

                  <div className="pt-6 border-t border-border">
                    <p className="text-sm text-muted-foreground">
                      Need help? Contact us at{" "}
                      <a
                        href="mailto:support@gcreators.me"
                        className="text-accent hover:underline"
                      >
                        support@gcreators.me
                      </a>
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

export default BookingCancel;
