import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Edit, Trash2 } from "lucide-react";

interface Booking {
  id: string;
  mentor_id: string;
  mentor_name: string;
  user_id: string | null;
  user_email: string;
  booking_date: string;
  booking_time: string;
  status: string;
  price: number;
  notes: string | null;
  meeting_link: string | null;
  meeting_platform: string | null;
  created_at: string | null;
}

interface MentorOption {
  id: string;
  name: string;
}

export default function AdminBookings() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [mentors, setMentors] = useState<MentorOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingBooking, setEditingBooking] = useState<Booking | null>(null);
  const [formData, setFormData] = useState({
    mentor_id: "",
    mentor_name: "",
    user_email: "",
    booking_date: "",
    booking_time: "",
    status: "pending",
    price: "0",
    notes: "",
    meeting_link: "",
    meeting_platform: "",
  });

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("bookings")
      .select("*")
      .order("booking_date", { ascending: false })
      .order("booking_time", { ascending: false });
    if (error) {
      toast.error("Failed to load bookings");
      setBookings([]);
    } else {
      setBookings(data ?? []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  useEffect(() => {
    const loadMentors = async () => {
      const { data } = await supabase.from("mentor_profiles").select("id, name").order("name");
      setMentors(data ?? []);
    };
    loadMentors();
  }, []);

  const resetForm = () => {
    setFormData({
      mentor_id: "",
      mentor_name: "",
      user_email: "",
      booking_date: "",
      booking_time: "",
      status: "pending",
      price: "0",
      notes: "",
      meeting_link: "",
      meeting_platform: "",
    });
    setEditingBooking(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const mentor = mentors.find((m) => m.id === formData.mentor_id);
    const payload = {
      mentor_id: formData.mentor_id,
      mentor_name: mentor?.name ?? formData.mentor_name,
      user_email: formData.user_email.trim(),
      booking_date: formData.booking_date,
      booking_time: formData.booking_time,
      status: formData.status,
      price: parseFloat(formData.price) || 0,
      notes: formData.notes.trim() || null,
      meeting_link: formData.meeting_link.trim() || null,
      meeting_platform: formData.meeting_platform.trim() || null,
    };

    if (editingBooking) {
      const { error } = await supabase.from("bookings").update(payload).eq("id", editingBooking.id);
      if (error) {
        toast.error(error.message);
        return;
      }
      toast.success("Booking updated");
    } else {
      const { error } = await supabase.from("bookings").insert(payload);
      if (error) {
        toast.error(error.message);
        return;
      }
      toast.success("Booking created");
    }
    setShowDialog(false);
    resetForm();
    fetchBookings();
  };

  const handleEdit = (b: Booking) => {
    setEditingBooking(b);
    setFormData({
      mentor_id: b.mentor_id,
      mentor_name: b.mentor_name,
      user_email: b.user_email,
      booking_date: b.booking_date,
      booking_time: b.booking_time,
      status: b.status,
      price: String(b.price),
      notes: b.notes ?? "",
      meeting_link: b.meeting_link ?? "",
      meeting_platform: b.meeting_platform ?? "",
    });
    setShowDialog(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this booking?")) return;
    const { error } = await supabase.from("bookings").delete().eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Booking deleted");
    fetchBookings();
  };

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Bookings</h1>
            <p className="text-sm text-muted-foreground">Manage mentorship session bookings</p>
          </div>
          <Dialog
            open={showDialog}
            onOpenChange={(open) => {
              setShowDialog(open);
              if (!open) resetForm();
            }}
          >
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add booking
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{editingBooking ? "Edit booking" : "Add booking"}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label>Mentor *</Label>
                  <Select
                    value={formData.mentor_id}
                    onValueChange={(v) => {
                      const m = mentors.find((x) => x.id === v) ?? (editingBooking && editingBooking.mentor_id === v ? { id: v, name: editingBooking.mentor_name } : null);
                      setFormData({ ...formData, mentor_id: v, mentor_name: m?.name ?? "" });
                    }}
                    required
                  >
                    <SelectTrigger><SelectValue placeholder="Select mentor" /></SelectTrigger>
                    <SelectContent>
                      {editingBooking && !mentors.some((m) => m.id === editingBooking.mentor_id) && (
                        <SelectItem value={editingBooking.mentor_id}>{editingBooking.mentor_name || editingBooking.mentor_id}</SelectItem>
                      )}
                      {mentors.map((m) => (
                        <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Learner email *</Label>
                  <Input
                    type="email"
                    value={formData.user_email}
                    onChange={(e) => setFormData({ ...formData, user_email: e.target.value })}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Date *</Label>
                    <Input
                      type="date"
                      value={formData.booking_date}
                      onChange={(e) => setFormData({ ...formData, booking_date: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Time *</Label>
                    <Input
                      type="time"
                      value={formData.booking_time}
                      onChange={(e) => setFormData({ ...formData, booking_time: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Status *</Label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="confirmed">Confirmed</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="refunded">Refunded</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Price (USD) *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div>
                  <Label>Meeting link</Label>
                  <Input
                    value={formData.meeting_link}
                    onChange={(e) => setFormData({ ...formData, meeting_link: e.target.value })}
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <Label>Meeting platform</Label>
                  <Input
                    value={formData.meeting_platform}
                    onChange={(e) => setFormData({ ...formData, meeting_platform: e.target.value })}
                    placeholder="Zoom, Google Meet, etc."
                  />
                </div>
                <div>
                  <Label>Notes</Label>
                  <Input
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => { setShowDialog(false); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit">{editingBooking ? "Update" : "Create"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          {loading ? (
            <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
          ) : bookings.length === 0 ? (
            <CardContent className="py-12 text-center text-muted-foreground">No bookings yet. Add one to get started.</CardContent>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date / Time</TableHead>
                  <TableHead>Mentor</TableHead>
                  <TableHead>Learner</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="w-[100px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {bookings.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>
                      <span className="font-medium">{b.booking_date}</span>
                      <span className="text-muted-foreground ml-2">{b.booking_time}</span>
                    </TableCell>
                    <TableCell>{b.mentor_name}</TableCell>
                    <TableCell>{b.user_email}</TableCell>
                    <TableCell>
                      <Badge variant={
                        b.status === "confirmed" ? "default" :
                        b.status === "completed" ? "secondary" :
                        b.status === "cancelled" || b.status === "failed" || b.status === "refunded" ? "destructive" : "secondary"
                      }>
                        {b.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">${Number(b.price).toFixed(2)}</TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(b)} title="Edit">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(b.id)} title="Delete" className="text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  );
}
