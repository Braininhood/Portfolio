import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface LegalLayoutProps {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}

export const LegalLayout = ({ title, lastUpdated, children }: LegalLayoutProps) => (
  <div className="min-h-screen bg-background">
    <Navbar />

    {/* Hero / Header - matches project gradient style */}
    <section className="pt-24 sm:pt-32 pb-8 sm:pb-12 bg-gradient-accent">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Brain Bulders
        </Link>
        <h1 className="text-3xl sm:text-4xl font-display font-bold">{title}</h1>
        <p className="text-sm text-muted-foreground mt-2">Last updated: {lastUpdated}</p>
      </div>
    </section>

    {/* Content */}
    <section className="py-12 sm:py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <article className="max-w-3xl mx-auto prose prose-neutral dark:prose-invert max-w-none prose-headings:font-semibold prose-h2:mt-10 prose-h2:mb-4 prose-h2:text-xl prose-h3:mt-6 prose-h3:mb-3 prose-h3:text-lg prose-p:leading-relaxed prose-p:text-muted-foreground prose-li:my-1 prose-a:text-primary prose-a:underline hover:prose-a:no-underline">
          {children}
        </article>
      </div>
    </section>

    <Footer />
  </div>
);
