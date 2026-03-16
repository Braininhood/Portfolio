import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

interface SubRow {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export default function AdminSubscriptions() {
  const [subs, setSubs] = useState<SubRow[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSubs = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("push_subscriptions")
      .select("id, user_id, created_at, updated_at")
      .order("created_at", { ascending: false });
    if (error) {
      toast.error("Failed to load subscriptions");
      setSubs([]);
    } else {
      setSubs(data ?? []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSubs();
  }, [fetchSubs]);

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this push subscription? The user will stop receiving push notifications until they re-subscribe.")) return;
    const { error } = await supabase.from("push_subscriptions").delete().eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Subscription removed");
    fetchSubs();
  };

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Subscriptions</h1>
          <p className="text-sm text-muted-foreground">Push notification subscriptions. You can remove a subscription to revoke push for that device.</p>
        </div>
        <Card>
          {loading ? (
            <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
          ) : subs.length === 0 ? (
            <CardContent className="py-12 text-center text-muted-foreground">No push subscriptions yet.</CardContent>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User ID</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="w-[80px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {subs.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono text-xs">{s.user_id.slice(0, 8)}…</TableCell>
                    <TableCell className="text-muted-foreground">{new Date(s.created_at).toLocaleString()}</TableCell>
                    <TableCell className="text-muted-foreground">{new Date(s.updated_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={() => handleDelete(s.id)} title="Remove subscription" className="text-destructive hover:text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
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
