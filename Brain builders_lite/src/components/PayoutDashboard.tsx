import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  DollarSign, 
  TrendingUp, 
  Clock, 
  Receipt,
  Calendar
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Transaction {
  id: string;
  type: string;
  gross_amount: number;
  platform_fee: number;
  stripe_fee: number;
  net_amount: number;
  status: string;
  created_at: string;
  payout_status: string | null;
  related_id: string | null;
}

interface PayoutDashboardProps {
  mentorId: string;
}

export const PayoutDashboard = ({ mentorId }: PayoutDashboardProps) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadTransactions();
  }, [mentorId]);

  const PLATFORM_FEE_PERCENT = 0.15;
  const STRIPE_FEE_RATE = 0.029;
  const STRIPE_FEE_FIXED = 0.30;

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const { data: txData, error } = await supabase
        .from("transactions")
        .select("*")
        .eq("mentor_id", mentorId)
        .order("created_at", { ascending: false })
        .limit(100);

      if (error) throw error;

      if ((txData?.length ?? 0) > 0) {
        setTransactions((txData || []).map((t) => ({
          ...t,
          created_at: t.created_at ?? new Date().toISOString(),
        })) as Transaction[]);
        setLoading(false);
        return;
      }

      // No transactions yet (e.g. webhook didn't run for past payments): build from bookings + product_purchases
      const [bookingsRes, purchasesRes] = await Promise.all([
        supabase
          .from("bookings")
          .select("id, price, created_at, user_id")
          .eq("mentor_id", mentorId)
          .eq("status", "confirmed"),
        supabase
          .from("product_purchases")
          .select("id, product_id, amount, created_at, buyer_id")
          .eq("status", "completed"),
      ]);

      const bookingRows = bookingsRes.data ?? [];
      const purchaseRows = purchasesRes.data ?? [];
      const productIds = [...new Set(purchaseRows.map((p: { product_id: string }) => p.product_id))];
      const { data: products } = productIds.length > 0
        ? await supabase.from("mentor_products").select("id, mentor_id").in("id", productIds)
        : { data: [] };
      const mentorProductIds = new Set((products ?? []).filter((p: { mentor_id: string }) => p.mentor_id === mentorId).map((p: { id: string }) => p.id));

      const fromBooking = (b: { id: string; price: number; created_at: string | null; user_id?: string | null }): Transaction => {
        const gross = Number(b.price);
        const platformFee = gross * PLATFORM_FEE_PERCENT;
        const stripeFee = gross * STRIPE_FEE_RATE + STRIPE_FEE_FIXED;
        const net = gross - platformFee - stripeFee;
        return {
          id: `booking-${b.id}`,
          type: "booking",
          gross_amount: gross,
          platform_fee: platformFee,
          stripe_fee: stripeFee,
          net_amount: net,
          status: "completed",
          created_at: b.created_at ?? new Date().toISOString(),
          payout_status: null,
          related_id: b.id,
        };
      };
      const fromPurchase = (p: { id: string; product_id: string; amount: number; created_at: string | null; buyer_id?: string | null }): Transaction | null => {
        if (!mentorProductIds.has(p.product_id)) return null;
        const gross = Number(p.amount);
        const platformFee = gross * PLATFORM_FEE_PERCENT;
        const stripeFee = gross * STRIPE_FEE_RATE + STRIPE_FEE_FIXED;
        const net = gross - platformFee - stripeFee;
        return {
          id: `purchase-${p.id}`,
          type: "product_sale",
          gross_amount: gross,
          platform_fee: platformFee,
          stripe_fee: stripeFee,
          net_amount: net,
          status: "completed",
          created_at: p.created_at ?? new Date().toISOString(),
          payout_status: null,
          related_id: p.product_id,
        };
      };

      const combined: Transaction[] = [
        ...bookingRows.map(fromBooking),
        ...purchaseRows.map((p) => fromPurchase(p)).filter(Boolean) as Transaction[],
      ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 100);

      setTransactions(combined);
    } catch (error: any) {
      console.error("[PAYOUT-DASHBOARD] Error loading transactions:", error);
      toast({
        title: "Error",
        description: "Failed to load transaction history",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Calculate stats
  const totalNet = transactions
    .filter(t => t.status === "completed")
    .reduce((sum, t) => sum + Number(t.net_amount), 0);

  // This month's earnings
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const monthlyNet = transactions
    .filter(t => t.status === "completed" && new Date(t.created_at) >= startOfMonth)
    .reduce((sum, t) => sum + Number(t.net_amount), 0);

  // Pending balance (completed but not paid out yet)
  const pendingBalance = transactions
    .filter(t => t.status === "completed" && (!t.payout_status || t.payout_status === "pending"))
    .reduce((sum, t) => sum + Number(t.net_amount), 0);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "booking":
        return "Consultation";
      case "product_sale":
        return "Product Sale";
      default:
        return type;
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading earnings data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Earnings Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Net Earnings</p>
                <p className="text-2xl font-bold">${totalNet.toFixed(2)}</p>
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
                <p className="text-sm text-muted-foreground">This Month</p>
                <p className="text-2xl font-bold">${monthlyNet.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending Balance</p>
                <p className="text-2xl font-bold">${pendingBalance.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Receipt className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Transactions</p>
                <p className="text-2xl font-bold">{transactions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Transaction History
          </CardTitle>
          <CardDescription>Your recent earnings and payouts</CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground space-y-2">
              <Receipt className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">No transactions yet</p>
              <p className="text-sm max-w-sm mx-auto">
                Transactions appear here after a learner pays for a booking or a product sale is completed.
                Future or pending sessions will show once payment is confirmed. If you just completed a sale, it may take a moment to appear.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Gross</TableHead>
                  <TableHead>Fees</TableHead>
                  <TableHead>Net</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((transaction) => {
                  const totalFees = Number(transaction.platform_fee) + Number(transaction.stripe_fee);
                  return (
                    <TableRow key={transaction.id}>
                      <TableCell className="whitespace-nowrap">
                        {formatDate(transaction.created_at)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {getTypeLabel(transaction.type)}
                      </TableCell>
                      <TableCell className="font-semibold">
                        ${Number(transaction.gross_amount).toFixed(2)}
                      </TableCell>
                      <TableCell className="text-red-600">
                        -${totalFees.toFixed(2)}
                      </TableCell>
                      <TableCell className="font-bold text-green-600">
                        ${Number(transaction.net_amount).toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={transaction.status === "completed" ? "default" : "secondary"}
                        >
                          {transaction.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
