import { useState } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Download, FileText, FileImage, FileVideo, File, Loader2, Eye, Calendar } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { formatDistanceToNow } from "date-fns";

interface Purchase {
  id: string;
  amount: number;
  status: string;
  created_at: string;
  product: {
    id: string;
    title: string;
    description: string;
    file_type: string;
    preview_image_url: string | null;
    mentor_id: string;
    mentor_profiles?: {
      name: string;
      image_url: string | null;
    } | null;
  } | null;
}

interface PurchasedProductCardProps {
  purchase: Purchase;
}

export const PurchasedProductCard = ({ purchase }: PurchasedProductCardProps) => {
  const [downloading, setDownloading] = useState(false);
  const { toast } = useToast();

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType) {
      case "pdf":
        return <FileText className="h-8 w-8 text-muted-foreground" />;
      case "image":
        return <FileImage className="h-8 w-8 text-muted-foreground" />;
      case "video":
        return <FileVideo className="h-8 w-8 text-muted-foreground" />;
      default:
        return <File className="h-8 w-8 text-muted-foreground" />;
    }
  };

  const getFileTypeLabel = (fileType: string) => {
    switch (fileType) {
      case "pdf":
        return "PDF";
      case "image":
        return "Image";
      case "video":
        return "Video";
      case "audio":
        return "Audio";
      case "document":
        return "Document";
      default:
        return "File";
    }
  };

  const handleDownload = async () => {
    if (!purchase.product) return;
    
    setDownloading(true);
    try {
      const { data, error } = await supabase.functions.invoke("verify-product-purchase", {
        body: { 
          productId: purchase.product.id,
          redownload: true 
        },
      });

      if (error) throw error;

      if (data?.downloadUrl) {
        window.open(data.downloadUrl, "_blank");
        toast({
          title: "Download started",
          description: "Your file download has begun.",
        });
      } else {
        throw new Error("No download URL returned");
      }
    } catch (error: any) {
      console.error("Download error:", error);
      toast({
        title: "Download failed",
        description: error.message || "Could not download the file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setDownloading(false);
    }
  };

  if (!purchase.product) {
    return null;
  }

  const mentorName = purchase.product.mentor_profiles?.name || "Unknown Mentor";
  const mentorImage = purchase.product.mentor_profiles?.image_url;

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <div className="aspect-video relative bg-muted">
        {purchase.product.preview_image_url ? (
          <img
            src={purchase.product.preview_image_url}
            alt={purchase.product.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-muted/50">
            {getFileTypeIcon(purchase.product.file_type)}
          </div>
        )}
        <Badge className="absolute top-2 right-2" variant="secondary">
          {getFileTypeLabel(purchase.product.file_type)}
        </Badge>
      </div>
      
      <CardHeader className="pb-2">
        <CardTitle className="text-lg line-clamp-1">{purchase.product.title}</CardTitle>
        <div className="flex items-center gap-2 mt-2">
          <Avatar className="h-6 w-6">
            <AvatarImage src={mentorImage || undefined} alt={mentorName} />
            <AvatarFallback className="text-xs">
              {mentorName.split(" ").map(n => n[0]).join("").slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <span className="text-sm text-muted-foreground">{mentorName}</span>
        </div>
      </CardHeader>
      
      <CardContent className="pb-2">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {purchase.product.description}
        </p>
        <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span>Purchased {formatDistanceToNow(new Date(purchase.created_at), { addSuffix: true })}</span>
        </div>
      </CardContent>
      
      <CardFooter className="gap-2">
        <Button 
          onClick={handleDownload} 
          disabled={downloading || purchase.status !== "completed"}
          className="flex-1"
        >
          {downloading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Preparing...
            </>
          ) : (
            <>
              <Download className="mr-2 h-4 w-4" />
              Download
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};
