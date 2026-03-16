import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, Star, Globe, Award, Calendar, MessageSquare, Bot, ShoppingBag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ReviewCard from "@/components/ReviewCard";
import ShopProductCard from "@/components/ShopProductCard";
import TimeSlotSelector from "@/components/TimeSlotSelector";
import { QuestionSubmissionForm } from "@/components/QuestionSubmissionForm";
import type { Mentor, Review } from "@/data/mentors";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
interface TimeSlot {
  id: string;
  mentor_id: string;
  date: string;
  time: string;
  is_available: boolean;
}

interface WeeklySlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  file_type: string;
  preview_image_url: string | null;
  average_rating: number;
  review_count: number;
}

// Generate 1-hour slots from weekly availability for the next 4 weeks
const generateSlotsFromWeekly = (mentorId: string, weeklySlots: WeeklySlot[]): TimeSlot[] => {
  const slots: TimeSlot[] = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  // Generate for next 28 days (4 weeks)
  for (let dayOffset = 0; dayOffset < 28; dayOffset++) {
    const date = new Date(today);
    date.setDate(today.getDate() + dayOffset);
    const dayOfWeek = date.getDay(); // 0 = Sunday, 1 = Monday, etc.
    
    // Find weekly slots for this day
    const daySlots = weeklySlots.filter(s => s.day_of_week === dayOfWeek);
    
    daySlots.forEach(slot => {
      const startHour = parseInt(slot.start_time.split(':')[0]);
      const endHour = parseInt(slot.end_time.split(':')[0]);
      
      // Generate 1-hour slots between start and end
      for (let hour = startHour; hour < endHour; hour++) {
        const timeStr = `${hour.toString().padStart(2, '0')}:00:00`;
        const dateStr = date.toISOString().split('T')[0];
        
        // Skip if slot is in the past
        const slotDateTime = new Date(`${dateStr}T${timeStr}`);
        if (slotDateTime <= new Date()) continue;
        
        slots.push({
          id: `${mentorId}_${dateStr}_${timeStr}`,
          mentor_id: mentorId,
          date: dateStr,
          time: timeStr,
          is_available: true
        });
      }
    });
  }
  
  return slots.sort((a, b) => {
    const dateCompare = a.date.localeCompare(b.date);
    if (dateCompare !== 0) return dateCompare;
    return a.time.localeCompare(b.time);
  });
};

const MentorProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [mentor, setMentor] = useState<Mentor | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [isBooking, setIsBooking] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [avatar, setAvatar] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });
  }, []);

  useEffect(() => {
    if (id) {
      fetchMentorData();
    }
  }, [id]);

  const fetchMentorData = async () => {
    setLoading(true);
    
    // Fetch mentor profile
    const { data: mentorData, error: mentorError } = await supabase
      .from("mentor_profiles")
      .select("*")
      .eq("id", id)
      .maybeSingle();

    if (mentorError || !mentorData) {
      console.error("Error fetching mentor:", mentorError);
      setLoading(false);
      return;
    }

    setMentor({
      id: mentorData.id,
      name: mentorData.name,
      title: mentorData.title,
      category: mentorData.category as "Business" | "Tech" | "Creators",
      image: mentorData.image_url || "/placeholder.svg",
      rating: parseFloat(mentorData.rating?.toString() || "0"),
      reviewCount: mentorData.review_count || 0,
      price: parseFloat(mentorData.price.toString()),
      bio: mentorData.bio,
      fullBio: mentorData.full_bio,
      expertise: mentorData.expertise || [],
      languages: mentorData.languages || [],
      availability: mentorData.availability,
      experience: mentorData.experience,
      education: mentorData.education,
      certifications: mentorData.certifications || [],
    });

    // Fetch reviews
    const { data: reviewsData } = await supabase
      .from("mentor_reviews")
      .select("*")
      .eq("mentor_id", id)
      .order("created_at", { ascending: false });

    if (reviewsData) {
      setReviews(reviewsData.map(r => ({
        id: r.id,
        mentorId: r.mentor_id,
        userName: r.user_name,
        userAvatar: r.user_avatar || "/placeholder.svg",
        rating: r.rating,
        date: new Date(r.created_at).toISOString().split('T')[0],
        comment: r.comment,
      })));
    }

    // Fetch products
    const { data: productsData } = await supabase
      .from("mentor_products")
      .select("*")
      .eq("mentor_id", id)
      .eq("is_active", true);

    if (productsData) {
      setProducts(productsData.map(p => ({
        id: p.id,
        title: p.title,
        description: p.description,
        price: parseFloat(p.price.toString()),
        file_type: p.file_type,
        preview_image_url: p.preview_image_url,
        average_rating: parseFloat(p.average_rating?.toString() || "0"),
        review_count: p.review_count || 0,
      })));
    }

    // Fetch weekly availability and generate time slots
    const { data: weeklyData } = await (supabase
      .from("mentor_weekly_availability" as any)
      .select("day_of_week, start_time, end_time")
      .eq("mentor_id", id)
      .eq("is_active", true) as any);

    if (weeklyData && weeklyData.length > 0) {
      // Generate slots for the next 4 weeks from weekly availability
      const generatedSlots = generateSlotsFromWeekly(id!, weeklyData as WeeklySlot[]);
      
      // Fetch existing bookings to mark slots as unavailable
      const { data: bookingsData } = await supabase
        .from("bookings")
        .select("booking_date, booking_time")
        .eq("mentor_id", id)
        .in("status", ["pending", "confirmed"])
        .gte("booking_date", new Date().toISOString().split('T')[0]);
      
      const bookedSlots = new Set(
        (bookingsData || []).map(b => `${b.booking_date}_${b.booking_time}`)
      );
      
      // Mark booked slots as unavailable
      const slotsWithAvailability = generatedSlots.map(slot => ({
        ...slot,
        is_available: !bookedSlots.has(`${slot.date}_${slot.time}`)
      }));
      
      setTimeSlots(slotsWithAvailability);
    } else {
      // Fallback to old mentor_time_slots table
      const { data: slotsData } = await supabase
        .from("mentor_time_slots")
        .select("*")
        .eq("mentor_id", id)
        .eq("is_available", true)
        .gte("date", new Date().toISOString().split('T')[0])
        .order("date", { ascending: true })
        .order("time", { ascending: true });

      if (slotsData) {
        setTimeSlots(slotsData.map(s => ({
          id: s.id,
          mentor_id: s.mentor_id,
          date: s.date,
          time: s.time,
          is_available: s.is_available ?? true,
        })));
      }
    }

    // Fetch avatar if available (take most recent if multiple)
    const { data: avatarData } = await supabase
      .from('mentor_avatars')
      .select('*')
      .eq('mentor_id', id)
      .eq('status', 'ready')
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (avatarData) {
      setAvatar(avatarData);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-32">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  const mentorReviews = reviews;
  const mentorProducts = products;

  if (!mentor) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="min-h-screen flex items-center justify-center pt-16">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Mentor not found</h1>
            <Button onClick={() => navigate("/mentors")}>Back to Mentors</Button>
          </div>
        </div>
      </div>
    );
  }

  const handleStartConversation = async () => {
    if (!user) {
      toast.error("Please sign in to message mentors");
      navigate(`/auth?redirect=${encodeURIComponent(window.location.pathname + window.location.hash)}`);
      return;
    }

    // Check if conversation already exists
    const { data: existingConv } = await supabase
      .from("conversations")
      .select("id")
      .eq("user_id", user.id)
      .eq("mentor_id", mentor.id)
      .maybeSingle();

    if (existingConv) {
      navigate(`/learner/messages/${existingConv.id}`);
      return;
    }

    // Create new conversation — any logged-in learner can message a mentor
    const { data: newConv, error } = await supabase
      .from("conversations")
      .insert({
        user_id: user.id,
        mentor_id: mentor.id,
        mentor_name: mentor.name,
      })
      .select()
      .single();

    if (error) {
      console.error("Error creating conversation:", error);
      toast.error("Failed to start conversation");
    } else {
      navigate(`/learner/messages/${newConv.id}`);
    }
  };

  const handleBookSession = async () => {
    if (!selectedSlot) {
      toast.error("Please select a time slot first");
      return;
    }

    // Force refresh so we send a fresh token (avoids 401 from expired JWT)
    const { data: { session: refreshedSession }, error: refreshErr } = await supabase.auth.refreshSession();
    if (refreshErr || !refreshedSession?.access_token) {
      toast.error("Please sign in to book a session");
      navigate("/auth");
      return;
    }

    setIsBooking(true);

    try {
      const { data, error } = await supabase.functions.invoke("create-booking", {
        body: {
          mentorId: mentor.id,
          mentorName: mentor.name,
          bookingDate: selectedSlot.date,
          bookingTime: selectedSlot.time,
          price: mentor.price,
        },
        headers: { Authorization: `Bearer ${refreshedSession.access_token}` },
      });

      if (error) {
        const status = (error as { context?: { status?: number } })?.context?.status;
        if (status === 401) {
          toast.error("Session expired or invalid. Please sign in again.");
          navigate("/auth");
          return;
        }
        throw error;
      }

      // Redirect to Stripe checkout
      if (data?.sessionUrl) {
        window.location.href = data.sessionUrl;
      } else {
        throw new Error("No session URL received");
      }
    } catch (error) {
      console.error("Booking error:", error);
      toast.error("Failed to create booking", {
        description: error instanceof Error ? error.message : "Please try again",
      });
    } finally {
      setIsBooking(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section */}
      <section className="pt-24 sm:pt-32 pb-8 sm:pb-16 bg-gradient-accent">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            onClick={() => navigate("/mentors")}
            className="mb-4 sm:mb-6 -ml-2"
            size="sm"
          >
            <ArrowLeft size={18} className="mr-1.5" />
            Back
          </Button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
            {/* Profile Card */}
            <div className="lg:col-span-1">
              <Card className="lg:sticky lg:top-24">
                <CardContent className="p-4 sm:p-6 space-y-4 sm:space-y-6">
                  {/* Image */}
                  <div className="relative">
                    <img
                      src={mentor.image}
                      alt={mentor.name}
                      className="w-full aspect-square object-cover rounded-lg max-w-[200px] sm:max-w-none mx-auto"
                    />
                    <Badge className="absolute top-3 right-3 sm:top-4 sm:right-4 bg-accent text-accent-foreground shadow-medium text-xs sm:text-sm">
                      {mentor.category}
                    </Badge>
                  </div>

                  {/* Name & Title */}
                  <div className="text-center">
                    <h1 className="text-2xl sm:text-3xl font-display font-bold mb-1 sm:mb-2">
                      {mentor.name}
                    </h1>
                    <p className="text-sm sm:text-base text-muted-foreground mb-3 sm:mb-4">{mentor.title}</p>

                    {/* Rating */}
                    <div className="flex items-center justify-center gap-2 mb-3 sm:mb-4">
                      <div className="flex items-center gap-1">
                        <Star className="text-accent fill-accent" size={18} />
                        <span className="text-lg sm:text-xl font-semibold">{mentor.rating}</span>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        ({mentor.reviewCount} reviews)
                      </span>
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="space-y-2 sm:space-y-3 pt-3 sm:pt-4 border-t border-border">
                    <div className="flex items-center gap-2 text-xs sm:text-sm">
                      <Globe size={14} className="text-muted-foreground shrink-0" />
                      <span className="truncate">{mentor.languages.join(", ")}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs sm:text-sm">
                      <Calendar size={14} className="text-muted-foreground shrink-0" />
                      <span>{mentor.availability}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs sm:text-sm">
                      <Award size={14} className="text-muted-foreground shrink-0" />
                      <span>{mentor.experience}</span>
                    </div>
                  </div>

                  {/* Price & CTA */}
                  <div className="pt-3 sm:pt-4 border-t border-border space-y-3 sm:space-y-4">
                    <div className="text-center">
                      <div className="text-3xl sm:text-4xl font-display font-bold gradient-text mb-1">
                        ${mentor.price}
                      </div>
                      <div className="text-xs sm:text-sm text-muted-foreground">per session (60 min)</div>
                    </div>
                    <Button 
                      variant="hero" 
                      size="default"
                      className="w-full"
                      onClick={() => setActiveTab("booking")}
                    >
                      Book a Session
                    </Button>
                    <Button 
                      variant="outline" 
                      size="default"
                      className="w-full"
                      onClick={handleStartConversation}
                    >
                      <MessageSquare size={16} className="mr-2" />
                      Send Message
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Content Area */}
            <div className="lg:col-span-2">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6 sm:space-y-8">
                {/* Scrollable tabs for mobile */}
                <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
                  <TabsList className="inline-flex w-max sm:grid sm:w-full sm:grid-cols-4 gap-1">
                    <TabsTrigger value="overview" className="text-xs sm:text-sm whitespace-nowrap px-3 sm:px-4">
                      Overview
                    </TabsTrigger>
                    <TabsTrigger value="shop" className="text-xs sm:text-sm whitespace-nowrap px-3 sm:px-4">
                      <ShoppingBag size={14} className="mr-1 sm:mr-1.5" />
                      Shop ({mentorProducts.length})
                    </TabsTrigger>
                    <TabsTrigger value="booking" className="text-xs sm:text-sm whitespace-nowrap px-3 sm:px-4">
                      Book Session
                    </TabsTrigger>
                    <TabsTrigger value="question" className="text-xs sm:text-sm whitespace-nowrap px-3 sm:px-4">
                      Ask Question
                    </TabsTrigger>
                  </TabsList>
                </div>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-6">
                  {avatar && (
                    <Card className="border-accent/20 bg-gradient-to-br from-accent/5 to-primary/5">
                      <CardHeader>
                        <div className="flex items-center gap-3">
                          <Bot className="text-accent" size={24} />
                          <div>
                            <CardTitle>Chat with AI Avatar</CardTitle>
                            <p className="text-sm text-muted-foreground mt-1">
                              Get instant answers 24/7 from {mentor.name}'s AI assistant
                            </p>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <Button 
                          variant="hero" 
                          onClick={() => navigate(`/learner/avatar-chat/${avatar.id}`)}
                          className="w-full"
                        >
                          <Bot className="mr-2" size={18} />
                          Start AI Chat
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardHeader>
                      <CardTitle>About {mentor.name}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-muted-foreground leading-relaxed">
                        {mentor.fullBio}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Expertise</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {mentor.expertise.map((skill, index) => (
                          <Badge key={index} variant="secondary" className="text-sm">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Education & Certifications</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Education</h4>
                        <p className="text-muted-foreground">{mentor.education}</p>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2">Certifications</h4>
                        <ul className="space-y-2">
                          {mentor.certifications.map((cert, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <Award size={16} className="text-accent mt-1" />
                              <span className="text-muted-foreground">{cert}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Reviews Section */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Star size={20} className="text-accent" />
                        Reviews ({mentorReviews.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {mentorReviews.length > 0 ? (
                          mentorReviews.map((review) => (
                            <ReviewCard key={review.id} review={review} />
                          ))
                        ) : (
                          <p className="text-muted-foreground text-center py-4">No reviews yet</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>


                {/* Shop Tab */}
                <TabsContent value="shop" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <ShoppingBag size={20} />
                        Digital Products by {mentor.name}
                      </CardTitle>
                      <p className="text-muted-foreground text-sm">
                        Exclusive digital resources, templates, and guides
                      </p>
                    </CardHeader>
                  </Card>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {mentorProducts.length > 0 ? (
                      mentorProducts.map((product) => (
                        <ShopProductCard 
                          key={product.id} 
                          product={product} 
                          mentorName={mentor.name}
                        />
                      ))
                    ) : (
                      <Card className="col-span-2">
                        <CardContent className="p-12 text-center">
                          <ShoppingBag size={48} className="mx-auto text-muted-foreground/50 mb-4" />
                          <p className="text-muted-foreground">No products available yet</p>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </TabsContent>

                {/* Booking Tab */}
                <TabsContent value="booking" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Book a Session with {mentor.name}</CardTitle>
                      <p className="text-muted-foreground">
                        Select an available time slot below. All times are shown in your local timezone.
                      </p>
                    </CardHeader>
                    <CardContent>
                      <TimeSlotSelector
                        timeSlots={timeSlots as any}
                        onSelectSlot={(slot: any) => setSelectedSlot(slot as TimeSlot)}
                      />

                      {selectedSlot && (
                        <div className="mt-6 p-6 bg-accent/10 rounded-lg border border-accent/20 space-y-4">
                          <h4 className="font-semibold text-lg">Selected Time Slot:</h4>
                          <p className="text-sm text-muted-foreground">
                            {new Date(selectedSlot.date).toLocaleDateString('en-US', {
                              weekday: 'long',
                              month: 'long',
                              day: 'numeric',
                              year: 'numeric'
                            })} at {selectedSlot.time}
                          </p>

                          <div className="space-y-3">
                            <div className="flex items-center justify-between pt-4 border-t border-border">
                              <div>
                                <div className="text-2xl font-display font-bold">${mentor.price}</div>
                                <div className="text-xs text-muted-foreground">60-minute session</div>
                              </div>
                              <Button 
                                variant="hero" 
                                onClick={handleBookSession}
                                disabled={isBooking}
                              >
                                {isBooking ? "Processing..." : "Proceed to Payment"}
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Question Tab */}
                <TabsContent value="question" className="space-y-6">
                  <QuestionSubmissionForm
                    mentorId={id!}
                    mentorName={mentor.name}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default MentorProfile;