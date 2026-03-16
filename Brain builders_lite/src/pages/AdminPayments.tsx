import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

interface BookingPayment {
  id: string;
  mentor_name: string;
  user_email: string;
  booking_date: string;
  booking_time: string;
  status: string;
  price: number;
  created_at: string | null;
}

interface ProductPurchase {
  id: string;
  buyer_email: string;
  amount: number;
  status: string;
  created_at: string;
}

const BOOKING_STATUSES = ["pending", "confirmed", "cancelled", "completed", "failed", "refunded"];
const PURCHASE_STATUSES = ["pending", "completed", "refunded", "failed"];

export default function AdminPayments() {
  const [bookings, setBookings] = useState<BookingPayment[]>([]);
  const [purchases, setPurchases] = useState<ProductPurchase[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [bookRes, purchRes] = await Promise.all([
      supabase.from("bookings").select("id, mentor_name, user_email, booking_date, booking_time, status, price, created_at").order("created_at", { ascending: false }),
      supabase.from("product_purchases").select("id, buyer_email, amount, status, created_at").order("created_at", { ascending: false }),
    ]);
    setBookings(bookRes.data ?? []);
    setPurchases(purchRes.data ?? []);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleBookingStatusChange = async (id: string, status: string) => {
    const { error } = await supabase.from("bookings").update({ status }).eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Booking status updated");
    fetchData();
  };

  const handlePurchaseStatusChange = async (id: string, status: string) => {
    const { error } = await supabase.from("product_purchases").update({ status }).eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Purchase status updated");
    fetchData();
  };

  const handleDeletePurchase = async (id: string) => {
    if (!confirm("Delete this purchase record? This does not refund the payment.")) return;
    const { error } = await supabase.from("product_purchases").delete().eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Purchase record deleted");
    fetchData();
  };

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Sales Management</h1>
          <p className="text-sm text-muted-foreground">Full management of session bookings and product purchases — change status, delete purchase records.</p>
        </div>
        <Tabs defaultValue="bookings">
          <TabsList>
            <TabsTrigger value="bookings">Session bookings</TabsTrigger>
            <TabsTrigger value="products">Product purchases</TabsTrigger>
          </TabsList>
          <TabsContent value="bookings">
            <Card>
              {loading ? (
                <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
              ) : bookings.length === 0 ? (
                <CardContent className="py-12 text-center text-muted-foreground">No session payments yet.</CardContent>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Mentor</TableHead>
                      <TableHead>Buyer</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bookings.map((b) => (
                      <TableRow key={b.id}>
                        <TableCell>{b.booking_date} {b.booking_time}</TableCell>
                        <TableCell>{b.mentor_name}</TableCell>
                        <TableCell>{b.user_email}</TableCell>
                        <TableCell>
                          <Select value={b.status} onValueChange={(v) => handleBookingStatusChange(b.id, v)}>
                            <SelectTrigger className="w-[120px] h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {BOOKING_STATUSES.map((s) => (
                                <SelectItem key={s} value={s}>{s}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-right">${Number(b.price).toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>
          </TabsContent>
          <TabsContent value="products">
            <Card>
              {loading ? (
                <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
              ) : purchases.length === 0 ? (
                <CardContent className="py-12 text-center text-muted-foreground">No product purchases yet.</CardContent>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Buyer</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="w-[80px]" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {purchases.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell>{new Date(p.created_at).toLocaleString()}</TableCell>
                        <TableCell>{p.buyer_email}</TableCell>
                        <TableCell>
                          <Select value={p.status} onValueChange={(v) => handlePurchaseStatusChange(p.id, v)}>
                            <SelectTrigger className="w-[120px] h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {PURCHASE_STATUSES.map((s) => (
                                <SelectItem key={s} value={s}>{s}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-right">${Number(p.amount).toFixed(2)}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" onClick={() => handleDeletePurchase(p.id)} title="Delete record" className="text-destructive hover:text-destructive">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
