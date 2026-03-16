import { z } from "zod";

// Mentor Profile Schema
export const mentorProfileSchema = z.object({
  name: z.string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be less than 100 characters")
    .trim(),
  title: z.string()
    .min(2, "Title must be at least 2 characters")
    .max(100, "Title must be less than 100 characters")
    .trim(),
  category: z.enum(["Business", "Tech", "Creators"], {
    errorMap: () => ({ message: "Please select a valid category" }),
  }),
  image_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  price: z.number()
    .positive("Price must be positive")
    .min(0.01, "Price must be at least $0.01")
    .max(10000, "Price must be less than $10,000"),
  bio: z.string()
    .min(10, "Bio must be at least 10 characters")
    .max(500, "Bio must be less than 500 characters")
    .trim(),
  full_bio: z.string()
    .min(50, "Full bio must be at least 50 characters")
    .max(5000, "Full bio must be less than 5000 characters")
    .trim(),
  expertise: z.array(z.string().trim().min(1))
    .min(1, "At least one expertise is required")
    .max(10, "Maximum 10 expertise areas"),
  languages: z.array(z.string().trim().min(1))
    .min(1, "At least one language is required")
    .max(10, "Maximum 10 languages"),
  availability: z.string()
    .min(3, "Availability must be at least 3 characters")
    .max(200, "Availability must be less than 200 characters")
    .trim(),
  experience: z.string()
    .min(10, "Experience must be at least 10 characters")
    .max(1000, "Experience must be less than 1000 characters")
    .trim(),
  education: z.string()
    .min(5, "Education must be at least 5 characters")
    .max(500, "Education must be less than 500 characters")
    .trim(),
  certifications: z.array(z.string().trim().min(1))
    .max(20, "Maximum 20 certifications")
    .optional(),
});

export type MentorProfileInput = z.infer<typeof mentorProfileSchema>;

// Profile Schema (Learner)
export const profileSchema = z.object({
  full_name: z.string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be less than 100 characters")
    .trim()
    .optional(),
  skill_level: z.enum(["beginner", "intermediate", "advanced"], {
    errorMap: () => ({ message: "Please select a valid skill level" }),
  }).optional(),
  goals: z.string()
    .max(500, "Goals must be less than 500 characters")
    .trim()
    .optional(),
  preferred_language: z.string()
    .max(50, "Language must be less than 50 characters")
    .trim()
    .optional(),
});

export type ProfileInput = z.infer<typeof profileSchema>;

// Message Schema
export const messageSchema = z.object({
  content: z.string()
    .min(1, "Message cannot be empty")
    .max(5000, "Message must be less than 5000 characters")
    .trim(),
  conversation_id: z.string().uuid("Invalid conversation ID"),
  sender_id: z.string().uuid("Invalid sender ID"),
  sender_name: z.string()
    .min(1, "Sender name is required")
    .max(100, "Sender name must be less than 100 characters")
    .trim(),
});

export type MessageInput = z.infer<typeof messageSchema>;

// Booking Schema
export const bookingSchema = z.object({
  user_id: z.string().uuid("Invalid user ID"),
  user_email: z.string()
    .email("Invalid email address")
    .max(255, "Email must be less than 255 characters")
    .toLowerCase()
    .trim(),
  mentor_id: z.string().uuid("Invalid mentor ID"),
  mentor_name: z.string()
    .min(2, "Mentor name is required")
    .max(100, "Mentor name must be less than 100 characters")
    .trim(),
  booking_date: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format")
    .refine((date) => {
      const bookingDate = new Date(date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return bookingDate >= today;
    }, "Booking date must be today or in the future"),
  booking_time: z.string()
    .regex(/^\d{2}:\d{2}$/, "Time must be in HH:MM format"),
  price: z.number()
    .positive("Price must be positive")
    .min(0.01, "Price must be at least $0.01")
    .max(10000, "Price must be less than $10,000"),
  status: z.enum(["pending", "confirmed", "cancelled"], {
    errorMap: () => ({ message: "Invalid booking status" }),
  }).default("pending"),
});

export type BookingInput = z.infer<typeof bookingSchema>;

// Auth Schema
export const authSchema = z.object({
  email: z.string()
    .email("Invalid email address")
    .max(255, "Email must be less than 255 characters")
    .toLowerCase()
    .trim(),
  password: z.string()
    .min(8, "Password must be at least 8 characters")
    .max(100, "Password must be less than 100 characters")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    ),
});

export type AuthInput = z.infer<typeof authSchema>;

// Sign In Schema (less strict for password)
export const signInSchema = z.object({
  email: z.string()
    .email("Invalid email address")
    .toLowerCase()
    .trim(),
  password: z.string()
    .min(1, "Password is required"),
});

export type SignInInput = z.infer<typeof signInSchema>;

// Product Schema
export const productSchema = z.object({
  name: z.string()
    .min(3, "Product name must be at least 3 characters")
    .max(200, "Product name must be less than 200 characters")
    .trim(),
  description: z.string()
    .min(10, "Description must be at least 10 characters")
    .max(2000, "Description must be less than 2000 characters")
    .trim(),
  price: z.number()
    .positive("Price must be positive")
    .min(0.01, "Price must be at least $0.01")
    .max(100000, "Price must be less than $100,000"),
  type: z.enum(["course", "ebook", "template", "consultation", "other"], {
    errorMap: () => ({ message: "Please select a valid product type" }),
  }),
});

export type ProductInput = z.infer<typeof productSchema>;

// Helper function to safely parse and validate data
export function validateData<T>(schema: z.ZodSchema<T>, data: unknown): { success: true; data: T } | { success: false; errors: string[] } {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  }
  
  const errors = result.error.errors.map(err => 
    err.path.length > 0 ? `${err.path.join('.')}: ${err.message}` : err.message
  );
  
  return { success: false, errors };
}
