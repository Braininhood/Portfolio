export interface Mentor {
  id: string;
  name: string;
  title: string;
  category: "Business" | "Tech" | "Creators";
  image: string;
  rating: number;
  reviewCount: number;
  price: number;
  bio: string;
  fullBio: string;
  expertise: string[];
  languages: string[];
  availability: string;
  experience: string;
  education: string;
  certifications: string[];
}

export interface Review {
  id: string;
  mentorId: string;
  userName: string;
  userAvatar: string;
  rating: number;
  date: string;
  comment: string;
}

export interface Course {
  id: string;
  mentorId: string;
  title: string;
  description: string;
  price: number;
  duration: string;
  lessons: number;
  level: "Beginner" | "Intermediate" | "Advanced";
  thumbnail: string;
}

export interface TimeSlot {
  id: string;
  mentorId: string;
  date: string;
  time: string;
  available: boolean;
}

export const mentors: Mentor[] = [
  {
    id: "1",
    name: "Sarah Mitchell",
    title: "Business Strategy Expert",
    category: "Business",
    image: "/src/assets/mentors/mentor-1.jpg",
    rating: 4.9,
    reviewCount: 127,
    price: 150,
    bio: "15+ years helping entrepreneurs scale their businesses from startup to acquisition.",
    fullBio: "Sarah Mitchell is a seasoned business strategist with over 15 years of experience in helping startups and established companies achieve exponential growth. She has successfully guided over 200 entrepreneurs through fundraising, scaling operations, and eventual exits. Her expertise spans strategic planning, market positioning, and building high-performing teams. Sarah holds an MBA from Harvard Business School and has been featured in Forbes, Inc., and TechCrunch for her innovative approaches to business development.",
    expertise: ["Business Strategy", "Scaling", "Fundraising", "Leadership"],
    languages: ["English", "Spanish"],
    availability: "Available this week",
    experience: "15+ years in business strategy and growth consulting",
    education: "MBA, Harvard Business School",
    certifications: ["Certified Strategic Planner", "Executive Leadership Coach"],
  },
  {
    id: "2",
    name: "David Chen",
    title: "Senior Software Architect",
    category: "Tech",
    image: "/src/assets/mentors/mentor-2.jpg",
    rating: 5.0,
    reviewCount: 89,
    price: 120,
    bio: "Former Tech Lead at major tech companies. Specialized in system design and cloud architecture.",
    fullBio: "David Chen is a distinguished software architect with extensive experience building scalable systems for companies like Google and Amazon. He specializes in distributed systems, microservices architecture, and cloud-native applications. David has led engineering teams of 50+ developers and architected systems handling billions of requests daily. He's passionate about mentoring the next generation of software engineers and has helped over 300 developers advance their careers.",
    expertise: ["System Design", "Cloud Computing", "AWS", "Microservices"],
    languages: ["English", "Mandarin"],
    availability: "Available this week",
    experience: "12+ years in software engineering and architecture",
    education: "MS Computer Science, Stanford University",
    certifications: ["AWS Solutions Architect Professional", "Google Cloud Architect"],
  },
  {
    id: "3",
    name: "Maya Rodriguez",
    title: "Content Creator & Brand Strategist",
    category: "Creators",
    image: "/src/assets/mentors/mentor-3.jpg",
    rating: 4.8,
    reviewCount: 201,
    price: 100,
    bio: "Built a 500K+ following across platforms. Expert in personal branding and monetization.",
    fullBio: "Maya Rodriguez is a digital content creator who built her personal brand from zero to 500,000+ followers across Instagram, TikTok, and YouTube. She specializes in helping creators develop authentic voices, grow engaged audiences, and monetize their content through multiple revenue streams. Maya has generated over $2M in revenue through brand partnerships, digital products, and online courses. She's known for her data-driven approach to content strategy and audience growth.",
    expertise: ["Content Strategy", "Social Media", "Branding", "Monetization"],
    languages: ["English", "French"],
    availability: "Limited availability",
    experience: "8+ years in content creation and brand building",
    education: "BA Marketing & Communications, NYU",
    certifications: ["Digital Marketing Professional", "Brand Strategy Specialist"],
  },
  {
    id: "4",
    name: "Michael Thompson",
    title: "Executive Coach & CEO",
    category: "Business",
    image: "/src/assets/mentors/mentor-4.jpg",
    rating: 4.9,
    reviewCount: 156,
    price: 200,
    bio: "C-suite executive with 20+ years experience. Specialized in leadership development and organizational growth.",
    fullBio: "Michael Thompson brings over 20 years of C-suite experience to his executive coaching practice. As former CEO of multiple Fortune 500 companies, he has deep expertise in leadership development, organizational transformation, and strategic decision-making. Michael has coached over 100 executives to successful leadership transitions and has a proven track record in driving organizational change. His coaching philosophy emphasizes authenticity, strategic thinking, and sustainable performance.",
    expertise: ["Executive Coaching", "Leadership", "Management", "Change Management"],
    languages: ["English"],
    availability: "Available next week",
    experience: "20+ years in executive leadership",
    education: "MBA, Wharton School of Business",
    certifications: ["ICF Professional Certified Coach", "Leadership Development Specialist"],
  },
  {
    id: "5",
    name: "Emily Zhang",
    title: "Full-Stack Developer & Tech Educator",
    category: "Tech",
    image: "/src/assets/mentors/mentor-5.jpg",
    rating: 4.7,
    reviewCount: 143,
    price: 90,
    bio: "Passionate about teaching modern web development. Over 1000 students mentored to successful careers.",
    fullBio: "Emily Zhang is a full-stack developer and educator who has successfully mentored over 1,000 students into thriving tech careers. She specializes in modern web development technologies including React, Node.js, and cloud platforms. Emily has worked at leading tech companies and now dedicates her time to making tech education accessible and practical. Her teaching style focuses on hands-on projects, real-world applications, and career preparation. Many of her mentees have landed positions at top tech companies.",
    expertise: ["Web Development", "React", "Node.js", "Career Transitions"],
    languages: ["English", "Korean"],
    availability: "Available this week",
    experience: "10+ years in software development and education",
    education: "BS Computer Science, MIT",
    certifications: ["AWS Certified Developer", "React Advanced Certification"],
  },
  {
    id: "6",
    name: "Alex Rivera",
    title: "Video Producer & YouTube Strategist",
    category: "Creators",
    image: "/src/assets/mentors/mentor-6.jpg",
    rating: 4.9,
    reviewCount: 178,
    price: 110,
    bio: "Grew YouTube channel to 2M+ subscribers. Expert in video production and audience growth strategies.",
    fullBio: "Alex Rivera is a successful YouTube creator and video production expert who grew his channel from zero to 2 million subscribers in just 3 years. He specializes in content strategy, video production, editing techniques, and audience analytics. Alex has helped dozens of creators achieve monetization, secure brand deals, and build sustainable content businesses. His approach combines creative storytelling with data-driven optimization to maximize reach and engagement.",
    expertise: ["Video Production", "YouTube Growth", "Editing", "Analytics"],
    languages: ["English", "Portuguese"],
    availability: "Available this week",
    experience: "7+ years in video production and content creation",
    education: "BA Film & Media Studies, UCLA",
    certifications: ["YouTube Creator Certification", "Advanced Video Production"],
  },
];

export const reviews: Review[] = [
  {
    id: "1",
    mentorId: "1",
    userName: "James Wilson",
    userAvatar: "/src/assets/mentors/mentor-2.jpg",
    rating: 5,
    date: "2024-01-15",
    comment: "Sarah's guidance was instrumental in securing our Series A funding. Her strategic insights and network connections made all the difference. Highly recommend!",
  },
  {
    id: "2",
    mentorId: "1",
    userName: "Lisa Chen",
    userAvatar: "/src/assets/mentors/mentor-5.jpg",
    rating: 5,
    date: "2024-01-10",
    comment: "Working with Sarah transformed how I approach business strategy. Her frameworks are practical and her feedback is always actionable. Worth every penny!",
  },
  {
    id: "3",
    mentorId: "1",
    userName: "Robert Martinez",
    userAvatar: "/src/assets/mentors/mentor-4.jpg",
    rating: 4,
    date: "2024-01-05",
    comment: "Great mentor with deep expertise. She helped me refine my go-to-market strategy and scale our operations efficiently.",
  },
  {
    id: "4",
    mentorId: "2",
    userName: "Sophie Anderson",
    userAvatar: "/src/assets/mentors/mentor-3.jpg",
    rating: 5,
    date: "2024-01-18",
    comment: "David's system design expertise is unmatched. He helped me prepare for my senior engineer interviews and I landed my dream job at a FAANG company!",
  },
  {
    id: "5",
    mentorId: "2",
    userName: "Marcus Johnson",
    userAvatar: "/src/assets/mentors/mentor-6.jpg",
    rating: 5,
    date: "2024-01-12",
    comment: "Incredible mentor! David's real-world experience shows in every session. His architectural insights have made me a much better engineer.",
  },
  {
    id: "6",
    mentorId: "3",
    userName: "Emma Thompson",
    userAvatar: "/src/assets/mentors/mentor-1.jpg",
    rating: 5,
    date: "2024-01-20",
    comment: "Maya helped me grow my Instagram from 5K to 50K followers in just 3 months! Her content strategies are pure gold.",
  },
  {
    id: "7",
    mentorId: "3",
    userName: "Carlos Garcia",
    userAvatar: "/src/assets/mentors/mentor-2.jpg",
    rating: 4,
    date: "2024-01-14",
    comment: "Great insights into brand building and monetization. Maya's approach is authentic and results-driven.",
  },
];

export const courses: Course[] = [
  {
    id: "1",
    mentorId: "1",
    title: "Strategic Business Planning Masterclass",
    description: "Learn how to create comprehensive business strategies that drive growth and attract investors.",
    price: 299,
    duration: "6 weeks",
    lessons: 24,
    level: "Intermediate",
    thumbnail: "/src/assets/learning-path.jpg",
  },
  {
    id: "2",
    mentorId: "1",
    title: "Fundraising Fundamentals",
    description: "Master the art of raising capital from angels to VCs. Includes pitch deck templates and investor outreach strategies.",
    price: 199,
    duration: "4 weeks",
    lessons: 16,
    level: "Beginner",
    thumbnail: "/src/assets/consultation.jpg",
  },
  {
    id: "3",
    mentorId: "2",
    title: "System Design Interview Prep",
    description: "Comprehensive guide to acing system design interviews at top tech companies.",
    price: 249,
    duration: "8 weeks",
    lessons: 32,
    level: "Advanced",
    thumbnail: "/src/assets/ai-matching.jpg",
  },
  {
    id: "4",
    mentorId: "2",
    title: "Cloud Architecture Essentials",
    description: "Learn to design scalable, reliable cloud architectures using AWS and modern best practices.",
    price: 279,
    duration: "6 weeks",
    lessons: 28,
    level: "Intermediate",
    thumbnail: "/src/assets/learning-path.jpg",
  },
  {
    id: "5",
    mentorId: "3",
    title: "Content Creator Bootcamp",
    description: "Everything you need to build, grow, and monetize your personal brand across social platforms.",
    price: 179,
    duration: "5 weeks",
    lessons: 20,
    level: "Beginner",
    thumbnail: "/src/assets/consultation.jpg",
  },
  {
    id: "6",
    mentorId: "3",
    title: "Advanced Monetization Strategies",
    description: "Learn how to diversify income streams and scale your creator business to 6-figures.",
    price: 349,
    duration: "8 weeks",
    lessons: 30,
    level: "Advanced",
    thumbnail: "/src/assets/ai-matching.jpg",
  },
];

export const generateTimeSlots = (mentorId: string): TimeSlot[] => {
  const slots: TimeSlot[] = [];
  const times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"];
  const today = new Date();
  
  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    
    times.forEach((time, idx) => {
      slots.push({
        id: `${mentorId}-${dateStr}-${time}`,
        mentorId,
        date: dateStr,
        time,
        available: Math.random() > 0.3, // 70% available
      });
    });
  }
  
  return slots;
};