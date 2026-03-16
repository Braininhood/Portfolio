import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { DollarSign, TrendingUp, ShoppingBag, Users, Calendar } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Purchase {
  id: string;
  amount: number;
  status: string;
  created_at: string;
  buyer_email: string;
  product: {
    id: string;
    title: string;
    price: number;
  } | null;
}

interface Product {
  id: string;
  title: string;
  price: number;
  sales_count: number;
  total_earnings: number;
}

interface MentorSalesTabProps {
  mentorId: string;
}

export const MentorSalesTab = ({ mentorId }: MentorSalesTabProps) => {
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadSalesData();
  }, [mentorId]);

  const loadSalesData = async () => {
    setLoading(true);

    // Load products for this mentor
    const { data: productsData, error: productsError } = await supabase
      .from("mentor_products")
      .select("id, title, price, sales_count, total_earnings")
      .eq("mentor_id", mentorId)
      .order("total_earnings", { ascending: false });

    if (productsError) {
      toast({
        title: "Error",
        description: "Failed to load products",
        variant: "destructive",
      });
    } else {
      setProducts(productsData || []);
    }

    // Load purchases for this mentor's products
    const { data: purchasesData, error: purchasesError } = await supabase
      .from("product_purchases")
      .select(`
        id,
        amount,
        status,
        created_at,
        buyer_email,
        product:mentor_products!inner(
          id,
          title,
          price,
          mentor_id
        )
      `)
      .eq("mentor_products.mentor_id", mentorId)
      .order("created_at", { ascending: false })
      .limit(50);

    if (purchasesError) {
      console.error("Purchases error:", purchasesError);
    } else {
      setPurchases((purchasesData as unknown as Purchase[]) || []);
    }

    setLoading(false);
  };

  const totalGross = products.reduce((sum, p) => sum + Number(p.total_earnings), 0);
  
  // Calculate net earnings (after platform and Stripe fees)
  const platformFeePercent = 0.15; // 15%
  const stripeFeePercent = 0.029; // 2.9%
  const stripeFeeFixed = 0.30; // $0.30
  
  const totalPlatformFee = totalGross * platformFeePercent;
  const totalStripeFee = (totalGross * stripeFeePercent) + (products.reduce((sum, p) => sum + p.sales_count, 0) * stripeFeeFixed);
  const totalNet = totalGross - totalPlatformFee - totalStripeFee;
  
  const totalSales = products.reduce((sum, p) => sum + p.sales_count, 0);
  const uniqueBuyers = new Set(purchases.map(p => p.buyer_email)).size;
  const completedPurchases = purchases.filter(p => p.status === "completed");

  // Calculate this month's earnings
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const monthlyGross = completedPurchases
    .filter(p => new Date(p.created_at) >= startOfMonth)
    .reduce((sum, p) => sum + Number(p.amount), 0);
  const monthlyPlatformFee = monthlyGross * platformFeePercent;
  const monthlyPurchasesCount = completedPurchases.filter(p => new Date(p.created_at) >= startOfMonth).length;
  const monthlyStripeFee = (monthlyGross * stripeFeePercent) + (monthlyPurchasesCount * stripeFeeFixed);
  const monthlyNet = monthlyGross - monthlyPlatformFee - monthlyStripeFee;

  if (loading) {
    return <div className="text-center py-8">Loading sales data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Gross Revenue</p>
                <p className="text-2xl font-bold">${totalGross.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">Before fees</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Net Earnings</p>
                <p className="text-2xl font-bold text-green-600">${totalNet.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">After fees</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <ShoppingBag className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Sales</p>
                <p className="text-2xl font-bold">{totalSales}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Users className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Unique Buyers</p>
                <p className="text-2xl font-bold">{uniqueBuyers}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fee Breakdown Info */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Breakdown</CardTitle>
          <CardDescription>Understanding your product sales earnings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span className="text-sm">Gross Revenue</span>
              <span className="font-bold">${totalGross.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
              <span className="text-sm">Platform Fee (15%)</span>
              <span className="font-bold text-red-600">-${totalPlatformFee.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
              <span className="text-sm">Stripe Fee (~3%)</span>
              <span className="font-bold text-red-600">-${totalStripeFee.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-3 border-2 border-green-500/20 rounded-lg bg-green-500/5">
              <span className="text-sm font-medium text-green-600">Your Net Earnings</span>
              <span className="text-lg font-bold text-green-600">${totalNet.toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Earnings by Product */}
      <Card>
        <CardHeader>
          <CardTitle>Earnings by Product</CardTitle>
          <CardDescription>Revenue breakdown for each of your products</CardDescription>
        </CardHeader>
        <CardContent>
          {products.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <ShoppingBag className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No products yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {products.map((product) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{product.title}</p>
                    <p className="text-sm text-muted-foreground">
                      ${Number(product.price).toFixed(2)} per sale · {product.sales_count} sales
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-lg font-bold text-green-600">
                      ${Number(product.total_earnings).toFixed(2)}
                    </p>
                    <p className="text-sm text-muted-foreground">earned</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Purchases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Recent Purchases
          </CardTitle>
          <CardDescription>Your latest product sales</CardDescription>
        </CardHeader>
        <CardContent>
          {purchases.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No purchases yet</p>
              <p className="text-sm">Sales will appear here when customers buy your products</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Buyer</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {purchases.map((purchase) => (
                  <TableRow key={purchase.id}>
                    <TableCell className="whitespace-nowrap">
                      {new Date(purchase.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="font-medium">
                      {purchase.product?.title || "Unknown"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {purchase.buyer_email}
                    </TableCell>
                    <TableCell className="font-semibold">
                      ${Number(purchase.amount).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={purchase.status === "completed" ? "default" : "secondary"}
                      >
                        {purchase.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
