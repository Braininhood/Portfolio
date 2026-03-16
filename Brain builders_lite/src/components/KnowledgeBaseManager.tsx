import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Plus, Pencil, Trash2, BookOpen, Info, Upload,
  FileText, FileSpreadsheet, Presentation, Video, Music, File, CheckCircle2
} from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  content_type: string;
  file_url: string | null;
  file_name: string | null;
  file_type: string | null;
  is_active: boolean;
  created_at: string;
}

interface KnowledgeBaseManagerProps {
  mentorId: string;
  avatarId?: string;
  onRetrain?: () => void;
}

const CONTENT_TYPES = [
  { value: "text", label: "General Info" },
  { value: "faq", label: "FAQ" },
  { value: "service", label: "Service / Offering" },
  { value: "bio", label: "Bio / Background" },
  { value: "product", label: "Product Info" },
];

const ACCEPTED_FILES = ".pdf,.txt,.csv,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.mp4,.webm,.mov,.mp3,.wav,.m4a";

const MIME_TYPES: Record<string, string> = {
  pdf: "application/pdf",
  txt: "text/plain",
  csv: "text/csv",
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  xls: "application/vnd.ms-excel",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ppt: "application/vnd.ms-powerpoint",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  mp4: "video/mp4",
  webm: "video/webm",
  mov: "video/quicktime",
  mp3: "audio/mpeg",
  wav: "audio/wav",
  m4a: "audio/mp4",
};

function getFileIcon(ext: string) {
  if (["pdf", "doc", "docx", "txt"].includes(ext)) return <FileText className="h-4 w-4" />;
  if (["xls", "xlsx", "csv"].includes(ext)) return <FileSpreadsheet className="h-4 w-4" />;
  if (["ppt", "pptx"].includes(ext)) return <Presentation className="h-4 w-4" />;
  if (["mp4", "webm", "mov"].includes(ext)) return <Video className="h-4 w-4" />;
  if (["mp3", "wav", "m4a"].includes(ext)) return <Music className="h-4 w-4" />;
  return <File className="h-4 w-4" />;
}

export const KnowledgeBaseManager = ({ mentorId, avatarId, onRetrain }: KnowledgeBaseManagerProps) => {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<KnowledgeEntry | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const [form, setForm] = useState({ title: "", content: "", content_type: "text" });
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<"text" | "file">("text");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => { fetchEntries(); }, [mentorId]);

  const fetchEntries = async () => {
    setLoading(true);
    const { data, error } = await (supabase as any)
      .from("mentor_knowledge_base")
      .select("*")
      .eq("mentor_id", mentorId)
      .order("created_at", { ascending: false });
    if (!error) setEntries((data as KnowledgeEntry[]) || []);
    setLoading(false);
  };

  const openCreate = () => {
    setEditingEntry(null);
    setForm({ title: "", content: "", content_type: "text" });
    setPendingFile(null);
    setInputMode("text");
    setUploadProgress(0);
    setUploadStatus("");
    setDialogOpen(true);
  };

  const openEdit = (entry: KnowledgeEntry) => {
    setEditingEntry(entry);
    setForm({ title: entry.title, content: entry.content, content_type: entry.content_type });
    setPendingFile(null);
    setInputMode(entry.file_name ? "file" : "text");
    setUploadProgress(0);
    setUploadStatus("");
    setDialogOpen(true);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPendingFile(file);
    if (!form.title) {
      setForm(f => ({ ...f, title: file.name.replace(/\.[^.]+$/, "") }));
    }
  };

  const handleSave = async () => {
    if (!form.title.trim()) {
      toast({ title: "Error", description: "Title is required.", variant: "destructive" });
      return;
    }
    if (inputMode === "text" && !form.content.trim()) {
      toast({ title: "Error", description: "Please write some content.", variant: "destructive" });
      return;
    }
    if (inputMode === "file" && !pendingFile && !editingEntry?.file_name) {
      toast({ title: "Error", description: "Please select a file to upload.", variant: "destructive" });
      return;
    }

    setSaving(true);
    let finalContent = form.content;
    let fileUrl: string | null = null;
    let fileName: string | null = null;
    let fileType: string | null = null;

    try {
      // Upload and extract file if in file mode
      if (inputMode === "file" && pendingFile) {
        setUploadStatus("Uploading file...");
        setUploadProgress(20);

        const ext = pendingFile.name.split(".").pop()?.toLowerCase() || "";
        const filePath = `${mentorId}/${Date.now()}-${pendingFile.name}`;
        const mimeType = MIME_TYPES[ext] || pendingFile.type;

        const { error: uploadError } = await supabase.storage
          .from("knowledge-base-files")
          .upload(filePath, pendingFile, { contentType: mimeType });

        if (uploadError) throw new Error(`Upload failed: ${uploadError.message}`);

        const { data: { publicUrl } } = supabase.storage
          .from("knowledge-base-files")
          .getPublicUrl(filePath);

        fileUrl = publicUrl;
        fileName = pendingFile.name;
        fileType = ext;

        setUploadProgress(50);
        setUploadStatus("Extracting content...");

        // Extract text content
        const { data: extractData, error: extractError } = await supabase.functions.invoke(
          "extract-file-content",
          { body: { filePath, fileName: pendingFile.name, mimeType } }
        );

        if (extractError) {
          console.warn("Extraction warning:", extractError);
          finalContent = form.content || `[File: ${pendingFile.name} uploaded. Add a description above.]`;
        } else {
          finalContent = form.content
            ? `${form.content}\n\n--- Extracted from file ---\n${extractData.extractedText}`
            : extractData.extractedText;
        }

        setUploadProgress(80);
        setUploadStatus("Saving...");
      }

      const payload: any = {
        title: form.title,
        content: finalContent,
        content_type: form.content_type,
        updated_at: new Date().toISOString(),
      };
      if (fileUrl) { payload.file_url = fileUrl; payload.file_name = fileName; payload.file_type = fileType; }

      if (editingEntry) {
        const { error } = await (supabase as any)
          .from("mentor_knowledge_base")
          .update(payload)
          .eq("id", editingEntry.id);
        if (error) throw error;
        toast({ title: "Updated", description: "Knowledge entry updated." });
      } else {
        const { error } = await (supabase as any)
          .from("mentor_knowledge_base")
          .insert({ mentor_id: mentorId, avatar_id: avatarId || null, is_active: true, ...payload });
        if (error) throw error;
        toast({
          title: "Entry added",
          description: onRetrain
            ? "Click 'Retrain Now' to apply this to your avatar."
            : "Retrain your avatar to include this entry.",
          action: onRetrain ? (
            <button
              onClick={onRetrain}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-3"
            >
              Retrain Now
            </button>
          ) : undefined,
        });
      }

      setUploadProgress(100);
      setDialogOpen(false);
      fetchEntries();
    } catch (error: any) {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    } finally {
      setSaving(false);
      setUploadProgress(0);
      setUploadStatus("");
    }
  };

  const handleToggleActive = async (entry: KnowledgeEntry) => {
    const { error } = await (supabase as any)
      .from("mentor_knowledge_base")
      .update({ is_active: !entry.is_active })
      .eq("id", entry.id);
    if (error) toast({ title: "Error", description: error.message, variant: "destructive" });
    else fetchEntries();
  };

  const handleDelete = async (id: string) => {
    const { error } = await (supabase as any).from("mentor_knowledge_base").delete().eq("id", id);
    if (error) toast({ title: "Error", description: error.message, variant: "destructive" });
    else { toast({ title: "Deleted" }); fetchEntries(); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-base">Knowledge Base</h3>
          <p className="text-sm text-muted-foreground">
            Add text, documents, or media your AI avatar will use when answering questions
          </p>
        </div>
        <Button size="sm" onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Add Entry
        </Button>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription className="text-xs">
          Supported: PDF, Word, Excel, PowerPoint, TXT, CSV, MP4, MP3 and more (max 50MB).
          After adding or editing entries, click <strong>Retrain Now</strong> — your avatar will use
          all active knowledge base entries plus your profile, products, and courses.
        </AlertDescription>
      </Alert>

      {loading ? (
        <div className="py-8 text-center text-muted-foreground text-sm">Loading...</div>
      ) : entries.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <BookOpen className="h-10 w-10 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-sm font-medium mb-1">No knowledge entries yet</p>
            <p className="text-xs text-muted-foreground mb-4">
              Add text, upload PDFs, videos, spreadsheets or presentations
            </p>
            <Button size="sm" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Add First Entry
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => {
            const ext = entry.file_type || "";
            return (
              <Card key={entry.id} className={entry.is_active ? "" : "opacity-50"}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        {entry.file_name && (
                          <span className="text-muted-foreground">{getFileIcon(ext)}</span>
                        )}
                        <span className="font-medium text-sm truncate">{entry.title}</span>
                        <Badge variant="secondary" className="text-xs shrink-0">
                          {CONTENT_TYPES.find(t => t.value === entry.content_type)?.label || entry.content_type}
                        </Badge>
                        {entry.file_name && (
                          <Badge variant="outline" className="text-xs shrink-0 font-mono">
                            {entry.file_name.split(".").pop()?.toUpperCase()}
                          </Badge>
                        )}
                        {!entry.is_active && (
                          <Badge variant="outline" className="text-xs shrink-0">Disabled</Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2">{entry.content}</p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => openEdit(entry)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost" size="sm" className="h-8 px-2 text-xs text-muted-foreground"
                        onClick={() => handleToggleActive(entry)}
                        title={entry.is_active ? "Disable" : "Enable"}
                      >
                        {entry.is_active ? "Off" : "On"}
                      </Button>
                      <Button
                        variant="ghost" size="sm" className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(entry.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] flex flex-col overflow-hidden">
          <DialogHeader className="shrink-0">
            <DialogTitle>{editingEntry ? "Edit Entry" : "Add Knowledge Entry"}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            {/* Title + Type row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5 col-span-2">
                <Label>Title *</Label>
                <Input
                  placeholder="e.g. My coaching approach, Pricing FAQ..."
                  value={form.title}
                  onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))}
                />
              </div>
              <div className="space-y-1.5 col-span-2">
                <Label>Category</Label>
                <Select value={form.content_type} onValueChange={(v) => setForm(f => ({ ...f, content_type: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CONTENT_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Mode tabs */}
            <Tabs value={inputMode} onValueChange={(v) => {
              setInputMode(v as "text" | "file");
              setPendingFile(null);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}>
              <TabsList className="w-full">
                <TabsTrigger value="text" className="flex-1">
                  <FileText className="h-4 w-4 mr-2" />
                  Write Text
                </TabsTrigger>
                <TabsTrigger value="file" className="flex-1">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload File
                </TabsTrigger>
              </TabsList>

              <TabsContent value="text" className="mt-3 space-y-2">
                <Textarea
                  placeholder="Write the content your AI avatar should know about you, your services, FAQs, pricing, etc."
                  rows={6}
                  value={form.content}
                  onChange={(e) => setForm(f => ({ ...f, content: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">{form.content.length} characters</p>
              </TabsContent>

              <TabsContent value="file" className="mt-3 space-y-3">
                {/* File drop zone */}
                {!pendingFile ? (
                  <div
                    className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 hover:bg-muted/30 transition-colors"
                    onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const file = e.dataTransfer.files[0];
                      if (file) {
                        setPendingFile(file);
                        if (!form.title) setForm(f => ({ ...f, title: file.name.replace(/\.[^.]+$/, "") }));
                      }
                    }}
                  >
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm font-medium mb-1">Click to browse or drag & drop</p>
                    <p className="text-xs text-muted-foreground">
                      PDF, Word, Excel, PowerPoint, TXT, CSV, MP4, MP3, WAV
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Max 50MB · Text is extracted automatically</p>
                  </div>
                ) : (
                  <div className="border rounded-lg p-4 bg-muted/30">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                        {getFileIcon(pendingFile.name.split(".").pop() || "")}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{pendingFile.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(pendingFile.size / 1024).toFixed(0)} KB · Text will be extracted automatically
                        </p>
                      </div>
                      <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                    </div>
                    <Button
                      variant="ghost" size="sm" className="mt-2 text-xs h-7 text-muted-foreground"
                      onClick={() => { setPendingFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
                    >
                      Remove and choose another
                    </Button>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_FILES}
                  className="hidden"
                  onChange={handleFileSelect}
                />

                {/* Optional description for the file */}
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">
                    Additional context (optional)
                  </Label>
                  <Textarea
                    placeholder="Add any extra context about this file that the AI should know..."
                    rows={3}
                    value={form.content}
                    onChange={(e) => setForm(f => ({ ...f, content: e.target.value }))}
                  />
                </div>

                {/* Show existing file if editing */}
                {editingEntry?.file_name && !pendingFile && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground p-2 bg-muted/20 rounded">
                    {getFileIcon(editingEntry.file_type || "")}
                    <span>Current file: <strong>{editingEntry.file_name}</strong></span>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* Progress bar during save */}
            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="space-y-1">
                <Progress value={uploadProgress} className="h-2" />
                <p className="text-xs text-muted-foreground text-center">{uploadStatus}</p>
              </div>
            )}
          </div>
          <DialogFooter className="shrink-0 pt-2 border-t mt-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving
                ? (inputMode === "file" ? "Processing file..." : "Saving...")
                : editingEntry ? "Update" : "Add Entry"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
