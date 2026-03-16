import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Upload, Image, Loader2 } from "lucide-react";

interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  file_url: string;
  file_name: string;
  file_type: string;
  preview_image_url: string | null;
}

interface ProductFormProps {
  mentorId: string;
  product: Product | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const ProductForm = ({ mentorId, product, onClose, onSuccess }: ProductFormProps) => {
  const [title, setTitle] = useState(product?.title || "");
  const [description, setDescription] = useState(product?.description || "");
  const [price, setPrice] = useState(product?.price?.toString() || "");
  const [file, setFile] = useState<File | null>(null);
  const [previewImage, setPreviewImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState(product?.preview_image_url || "");
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadingPreview, setUploadingPreview] = useState(false);
  const { toast } = useToast();

  const getFileExtension = (filename: string) => {
    return filename.split(".").pop()?.toLowerCase() || "";
  };

  const uploadFile = async (file: File, bucket: string): Promise<string | null> => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return null;

    const fileExt = getFileExtension(file.name);
    const fileName = `${user.id}/${Date.now()}-${Math.random().toString(36).substring(7)}.${fileExt}`;

    const { error } = await supabase.storage
      .from(bucket)
      .upload(fileName, file);

    if (error) {
      console.error("Upload error:", error);
      return null;
    }

    const { data } = supabase.storage.from(bucket).getPublicUrl(fileName);
    return data.publicUrl;
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file size (max 100MB)
    if (selectedFile.size > 100 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Maximum file size is 100MB",
        variant: "destructive",
      });
      return;
    }

    setFile(selectedFile);
  };

  const handlePreviewChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file size (max 5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      toast({
        title: "Image too large",
        description: "Maximum preview image size is 5MB",
        variant: "destructive",
      });
      return;
    }

    // Validate file type
    if (!selectedFile.type.startsWith("image/")) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file",
        variant: "destructive",
      });
      return;
    }

    setPreviewImage(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim() || !description.trim() || !price) {
      toast({
        title: "Missing fields",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    if (!product && !file) {
      toast({
        title: "Missing file",
        description: "Please upload a product file",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      let fileUrl = product?.file_url || "";
      let fileName = product?.file_name || "";
      let fileType = product?.file_type || "";
      let imageUrl = product?.preview_image_url || null;

      // Upload product file if new
      if (file) {
        setUploadingFile(true);
        const url = await uploadFile(file, "product-files");
        setUploadingFile(false);
        
        if (!url) {
          throw new Error("Failed to upload product file");
        }
        fileUrl = url;
        fileName = file.name;
        fileType = getFileExtension(file.name);
      }

      // Upload preview image if new
      if (previewImage) {
        setUploadingPreview(true);
        const url = await uploadFile(previewImage, "product-previews");
        setUploadingPreview(false);
        
        if (url) {
          imageUrl = url;
        }
      }

      const productData = {
        mentor_id: mentorId,
        title: title.trim(),
        description: description.trim(),
        price: parseFloat(price),
        file_url: fileUrl,
        file_name: fileName,
        file_type: fileType,
        preview_image_url: imageUrl,
      };

      if (product) {
        // Update existing product
        const { error } = await supabase
          .from("mentor_products")
          .update(productData)
          .eq("id", product.id);

        if (error) throw error;

        toast({
          title: "Success",
          description: "Product updated successfully",
        });
      } else {
        // Create new product
        const { error } = await supabase
          .from("mentor_products")
          .insert(productData);

        if (error) throw error;

        toast({
          title: "Success",
          description: "Product created successfully",
        });
      }

      onSuccess();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to save product",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onClose}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <CardTitle>{product ? "Edit Product" : "Add New Product"}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="title">Product Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Social Media Template Pack"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Price (USD) *</Label>
              <Input
                id="price"
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="29.99"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what's included in this product..."
              rows={4}
              required
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Product File Upload */}
            <div className="space-y-2">
              <Label>Product File {!product && "*"}</Label>
              <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
                <input
                  type="file"
                  id="product-file"
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.mp3,.mp4,.wav,.mov,.avi,.jpg,.jpeg,.png,.gif,.webp,.epub,.mobi"
                />
                <label htmlFor="product-file" className="cursor-pointer">
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm font-medium">
                    {file ? file.name : product?.file_name || "Click to upload"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    PDF, ZIP, MP3, MP4, etc. (Max 100MB)
                  </p>
                </label>
              </div>
            </div>

            {/* Preview Image Upload */}
            <div className="space-y-2">
              <Label>Preview Image</Label>
              <div className="border-2 border-dashed border-border rounded-lg p-6 text-center overflow-hidden">
                <input
                  type="file"
                  id="preview-image"
                  className="hidden"
                  onChange={handlePreviewChange}
                  accept="image/*"
                />
                <label htmlFor="preview-image" className="cursor-pointer block">
                  {previewUrl ? (
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="w-full h-24 object-cover rounded-lg mb-2"
                    />
                  ) : (
                    <Image className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  )}
                  <p className="text-sm font-medium">
                    {previewImage ? previewImage.name : previewUrl ? "Change image" : "Add preview image"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    JPG, PNG, WebP (Max 5MB)
                  </p>
                </label>
              </div>
            </div>
          </div>

          <div className="flex gap-4 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {uploadingFile ? "Uploading file..." : uploadingPreview ? "Uploading image..." : product ? "Update Product" : "Create Product"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
