import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppErrorBoundary } from "@/components/AppErrorBoundary";
import Index from "./pages/Index";
import Mentors from "./pages/Mentors";
import MentorProfile from "./pages/MentorProfile";
import BookingSuccess from "./pages/BookingSuccess";
import BookingCancel from "./pages/BookingCancel";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import Messages from "./pages/Messages";
import AdminCabinet from "./pages/AdminCabinet";
import AdminMessagesChat from "./pages/AdminMessagesChat";
import MentorCabinet from "./pages/MentorCabinet";
import MentorQuestions from "./pages/MentorQuestions";
import MyQuestions from "./pages/MyQuestions";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import AvatarChat from "./pages/AvatarChat";
import MentorShop from "./pages/MentorShop";
import PurchaseSuccess from "./pages/PurchaseSuccess";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import TermsOfService from "./pages/TermsOfService";
import CookiePolicy from "./pages/CookiePolicy";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppErrorBoundary>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/mentors" element={<Mentors />} />
            <Route path="/mentors/:id" element={<MentorProfile />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/auth/mentor" element={<Auth />} />
            <Route path="/auth/learner" element={<Auth />} />
            <Route path="/shop/:username" element={<MentorShop />} />
            <Route path="/admin" element={<AdminCabinet />} />
            <Route path="/admin/messages" element={<Navigate to="/admin?tab=messages" replace />} />
            <Route path="/admin/messages/:conversationId" element={<AdminMessagesChat />} />
            {/* Learner routes */}
            <Route path="/learner/dashboard" element={<Dashboard />} />
            <Route path="/learner/profile" element={<Profile />} />
            <Route path="/learner/messages/:conversationId" element={<Messages />} />
            <Route path="/learner/my-questions" element={<MyQuestions />} />
            <Route path="/learner/booking-success" element={<BookingSuccess />} />
            <Route path="/learner/booking-cancel" element={<BookingCancel />} />
            <Route path="/learner/purchase-success" element={<PurchaseSuccess />} />
            <Route path="/learner/avatar-chat/:avatarId" element={<AvatarChat />} />
            {/* Mentor routes */}
            <Route path="/mentor/dashboard" element={<MentorCabinet />} />
            <Route path="/mentor/questions" element={<MentorQuestions />} />
            {/* Legal */}
            <Route path="/privacy-policy" element={<PrivacyPolicy />} />
            <Route path="/terms-of-service" element={<TermsOfService />} />
            <Route path="/cookie-policy" element={<CookiePolicy />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AppErrorBoundary>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
