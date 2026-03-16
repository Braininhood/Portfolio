import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Plus, Edit, Trash2, Eye, Share2, DollarSign, ShoppingBag, Star, MessageSquare } from "lucide-react";
import { ProductForm } from "./ProductForm";
import { ShareShopDialog } from "./ShareShopDialog";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  file_url: string;
  file_name: string;
  file_type: string;
  preview_image_url: string | null;
  sales_count: number;
  total_earnings: number;
  is_active: boolean;
  created_at: string;
  average_rating: number;
  review_count: number;
}

interface MentorProductsTabProps {
  mentorId: string;
  mentorUsername: string | null;
  mentorName: string;
}

export const MentorProductsTab = ({ mentorId, mentorUsername, mentorName }: MentorProductsTabProps) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deleteProduct, setDeleteProduct] = useState<Product | null>(null);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadProducts();
  }, [mentorId]);

  const loadProducts = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("mentor_products")
      .select("*")
      .eq("mentor_id", mentorId)
      .order("created_at", { ascending: false });

    if (error) {
      toast({
        title: "Error",
        description: "Failed to load products",
        variant: "destructive",
      });
    } else {
      setProducts(data || []);
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!deleteProduct) return;

    const { error } = await supabase
      .from("mentor_products")
      .delete()
      .eq("id", deleteProduct.id);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to delete product",
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Product deleted successfully",
      });
      loadProducts();
    }
    setDeleteProduct(null);
  };

  const handleToggleActive = async (product: Product) => {
    const { error } = await supabase
      .from("mentor_products")
      .update({ is_active: !product.is_active })
      .eq("id", product.id);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to update product",
        variant: "destructive",
      });
    } else {
      loadProducts();
    }
  };

  const totalEarnings = products.reduce((sum, p) => sum + Number(p.total_earnings), 0);
  const totalSales = products.reduce((sum, p) => sum + p.sales_count, 0);

  if (loading) {
    return <div className="text-center py-8">Loading products...</div>;
  }

  if (showForm || editingProduct) {
    return (
      <ProductForm
        mentorId={mentorId}
        product={editingProduct}
        onClose={() => {
          setShowForm(false);
          setEditingProduct(null);
        }}
        onSuccess={() => {
          setShowForm(false);
          setEditingProduct(null);
          loadProducts();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <ShoppingBag className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Products</p>
                <p className="text-2xl font-bold">{products.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Earnings</p>
                <p className="text-2xl font-bold">${totalEarnings.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Eye className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Sales</p>
                <p className="text-2xl font-bold">{totalSales}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-4">
        <Button onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Product
        </Button>
        <Button variant="outline" onClick={() => setShowShareDialog(true)}>
          <Share2 className="mr-2 h-4 w-4" />
          Share My Shop
        </Button>
        {mentorUsername && (
          <Button
            variant="ghost"
            onClick={() => window.open(`/shop/${mentorUsername}`, "_blank")}
          >
            <Eye className="mr-2 h-4 w-4" />
            View My Shop
          </Button>
        )}
      </div>

      {/* Products List */}
      {products.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ShoppingBag className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No products yet</h3>
            <p className="text-muted-foreground mb-4">
              Start selling digital products to your audience
            </p>
            <Button onClick={() => setShowForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Product
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {products.map((product) => (
            <Card key={product.id}>
              <CardContent className="p-4">
                <div className="flex flex-col md:flex-row gap-4">
                  {/* Preview Image */}
                  <div className="w-full md:w-32 h-32 rounded-lg bg-muted overflow-hidden flex-shrink-0">
                    {product.preview_image_url ? (
                      <img
                        src={product.preview_image_url}
                        alt={product.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <ShoppingBag className="h-8 w-8 text-muted-foreground" />
                      </div>
                    )}
                  </div>

                  {/* Product Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold truncate">{product.title}</h3>
                          <Badge variant={product.is_active ? "default" : "secondary"}>
                            {product.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {product.description}
                        </p>
                      </div>
                      <p className="text-lg font-bold text-primary whitespace-nowrap">
                        ${Number(product.price).toFixed(2)}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-muted-foreground">
                      <span>{product.sales_count} sales</span>
                      <span>${Number(product.total_earnings).toFixed(2)} earned</span>
                      <span>{product.file_type.toUpperCase()}</span>
                      <div className="flex items-center gap-1">
                        <Star size={14} className={product.average_rating > 0 ? "text-accent fill-accent" : "text-muted"} />
                        <span>
                          {product.average_rating > 0 
                            ? `${Number(product.average_rating).toFixed(1)} (${product.review_count} reviews)`
                            : "No reviews"}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingProduct(product)}
                      >
                        <Edit className="mr-1 h-3 w-3" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleActive(product)}
                      >
                        {product.is_active ? "Deactivate" : "Activate"}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setDeleteProduct(product)}
                      >
                        <Trash2 className="mr-1 h-3 w-3" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Share Dialog */}
      <ShareShopDialog
        open={showShareDialog}
        onOpenChange={setShowShareDialog}
        mentorUsername={mentorUsername}
        mentorName={mentorName}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteProduct} onOpenChange={() => setDeleteProduct(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Product</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteProduct?.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
