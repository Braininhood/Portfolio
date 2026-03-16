import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Plus, Edit, Trash2, ExternalLink, MessageSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface QuestionRow {
  id: string;
  mentor_id: string;
  user_id: string;
  question_text: string;
  status: string;
  created_at: string;
  mentor_profiles?: { name: string } | null;
}

interface MentorOption {
  id: string;
  name: string;
}

export default function AdminQuestions() {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<QuestionRow[]>([]);
  const [mentors, setMentors] = useState<MentorOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<QuestionRow | null>(null);
  const [formData, setFormData] = useState({
    mentor_id: "",
    user_id: "",
    question_text: "",
    status: "submitted",
  });

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("mentor_questions")
      .select(`
        id,
        mentor_id,
        user_id,
        question_text,
        status,
        created_at,
        mentor_profiles ( name )
      `)
      .order("created_at", { ascending: false });
    if (error) {
      toast.error("Failed to load questions");
      setQuestions([]);
    } else {
      setQuestions(data ?? []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  useEffect(() => {
    supabase.from("mentor_profiles").select("id, name").order("name").then(({ data }) => setMentors(data ?? []));
  }, []);

  const resetForm = () => {
    setFormData({ mentor_id: "", user_id: "", question_text: "", status: "submitted" });
    setEditingQuestion(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.mentor_id || !formData.user_id || !formData.question_text.trim()) {
      toast.error("Mentor, user and question text are required");
      return;
    }
    if (editingQuestion) {
      const { error } = await supabase
        .from("mentor_questions")
        .update({ question_text: formData.question_text.trim(), status: formData.status })
        .eq("id", editingQuestion.id);
      if (error) {
        toast.error(error.message);
        return;
      }
      toast.success("Question updated");
    } else {
      const { error } = await supabase.from("mentor_questions").insert({
        mentor_id: formData.mentor_id,
        user_id: formData.user_id,
        question_text: formData.question_text.trim(),
        status: formData.status,
      });
      if (error) {
        toast.error(error.message);
        return;
      }
      toast.success("Question added");
    }
    setShowDialog(false);
    resetForm();
    fetchQuestions();
  };

  const handleEdit = (q: QuestionRow) => {
    setEditingQuestion(q);
    setFormData({
      mentor_id: q.mentor_id,
      user_id: q.user_id,
      question_text: q.question_text,
      status: q.status,
    });
    setShowDialog(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this question?")) return;
    const { error } = await supabase.from("mentor_questions").delete().eq("id", id);
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Question deleted");
    fetchQuestions();
  };

  const handleViewConversation = async (userId: string, mentorId: string) => {
    const { data } = await supabase
      .from("conversations")
      .select("id")
      .eq("user_id", userId)
      .eq("mentor_id", mentorId)
      .maybeSingle();
    if (data?.id) {
      navigate(`/admin/messages/${data.id}`);
    } else {
      toast.info("No conversation between this learner and mentor yet.");
    }
  };

  return (
    <div className="p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Questions</h1>
            <p className="text-sm text-muted-foreground">
              This is the line that connects admin with questions. Learners ask from mentor profile pages or <strong>Learner dashboard → My Questions</strong>. Mentors answer from <strong>Mentor dashboard → Questions</strong>. To receive questions as admin, add an &quot;Admin&quot; mentor profile and share its Ask question link.
            </p>
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
                Add question
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md" aria-describedby="admin-question-dialog-desc">
              <DialogHeader>
                <DialogTitle>{editingQuestion ? "Edit question" : "Add question"}</DialogTitle>
                <DialogDescription id="admin-question-dialog-desc">
                  {editingQuestion ? "Update the question text and status." : "Create a new mentor question for a user."}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label>Mentor *</Label>
                  <Select
                    value={formData.mentor_id}
                    onValueChange={(v) => setFormData({ ...formData, mentor_id: v })}
                    required
                    disabled={!!editingQuestion}
                  >
                    <SelectTrigger><SelectValue placeholder="Select mentor" /></SelectTrigger>
                    <SelectContent>
                      {mentors.map((m) => (
                        <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>User ID (asker) *</Label>
                  <Input
                    value={formData.user_id}
                    onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                    placeholder="UUID"
                    required
                    disabled={!!editingQuestion}
                  />
                </div>
                <div>
                  <Label>Question text *</Label>
                  <Textarea
                    value={formData.question_text}
                    onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
                    rows={3}
                    required
                  />
                </div>
                <div>
                  <Label>Status *</Label>
                  <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="submitted">Submitted</SelectItem>
                      <SelectItem value="answered">Answered</SelectItem>
                      <SelectItem value="closed">Closed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => { setShowDialog(false); resetForm(); }}>Cancel</Button>
                  <Button type="submit">{editingQuestion ? "Update" : "Create"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          {loading ? (
            <CardContent className="py-12 text-center text-muted-foreground">Loading…</CardContent>
          ) : questions.length === 0 ? (
            <CardContent className="py-12 text-center text-muted-foreground">No questions yet. Add one or share a mentor profile so learners can ask.</CardContent>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Mentor</TableHead>
                  <TableHead>Question</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[140px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {questions.map((q) => (
                  <TableRow key={q.id}>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {new Date(q.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{(q.mentor_profiles as { name?: string } | null)?.name ?? "—"}</TableCell>
                    <TableCell className="max-w-xs truncate">{q.question_text}</TableCell>
                    <TableCell><Badge variant="secondary">{q.status}</Badge></TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewConversation(q.user_id, q.mentor_id)}
                          title="View conversation"
                        >
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" asChild>
                          <Link to="/mentor/questions" target="_blank" rel="noopener noreferrer" title="Mentor Q&A">
                            <ExternalLink className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(q)} title="Edit">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(q.id)} title="Delete" className="text-destructive hover:text-destructive">
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
