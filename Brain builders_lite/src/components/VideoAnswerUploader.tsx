import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Loader2, Upload, Video, X, Camera, Square, Play } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface VideoAnswerUploaderProps {
  questionId: string;
  questionText: string;
  onSuccess?: () => void;
}

export const VideoAnswerUploader = ({ questionId, questionText, onSuccess }: VideoAnswerUploaderProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mode, setMode] = useState<"select" | "upload" | "record">("select");
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  const { toast } = useToast();

  const MAX_DURATION = 10 * 60; // 10 minutes in seconds

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("video/")) {
      toast({
        title: "Invalid File",
        description: "Please select a video file",
        variant: "destructive",
      });
      return;
    }

    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      toast({
        title: "File Too Large",
        description: "Video must be under 100MB (approximately 10 minutes)",
        variant: "destructive",
      });
      return;
    }

    setSelectedFile(file);
    setRecordedBlob(null);
    setRecordedUrl(null);
  };

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 1280, height: 720 },
        audio: true,
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        videoRef.current.play();
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
          ? "video/webm;codecs=vp9"
          : "video/webm",
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        setRecordedBlob(blob);
        setRecordedUrl(url);
        setIsRecording(false);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      };

      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= MAX_DURATION - 1) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (error) {
      console.error("Error starting recording:", error);
      toast({
        title: "Camera Access Denied",
        description: "Please allow camera and microphone access to record video.",
        variant: "destructive",
      });
    }
  }, [toast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const resetRecording = () => {
    if (recordedUrl) {
      URL.revokeObjectURL(recordedUrl);
    }
    setRecordedBlob(null);
    setRecordedUrl(null);
    setRecordingTime(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const sendNotification = async (mentorName: string) => {
    try {
      await supabase.functions.invoke("notify-video-answer", {
        body: { questionId, mentorName },
      });
      console.log("Notification sent successfully");
    } catch (error) {
      console.error("Error sending notification:", error);
      // Don't throw - notification failure shouldn't block the upload success
    }
  };

  const handleUpload = async () => {
    const fileToUpload = selectedFile || (recordedBlob ? new File([recordedBlob], `recording-${Date.now()}.webm`, { type: "video/webm" }) : null);
    
    if (!fileToUpload) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not authenticated");

      // Get mentor name for notification
      const { data: mentorProfile } = await supabase
        .from("mentor_profiles")
        .select("name")
        .eq("user_id", user.id)
        .single();

      const mentorName = mentorProfile?.name || "Your mentor";

      const fileExt = fileToUpload.name.split(".").pop();
      const fileName = `${questionId}-${Date.now()}.${fileExt}`;
      const filePath = `${user.id}/${fileName}`;

      const { error: uploadError } = await supabase.storage
        .from("mentor-videos")
        .upload(filePath, fileToUpload, {
          cacheControl: "3600",
          upsert: false,
        });

      if (uploadError) throw uploadError;

      const { data: { publicUrl } } = supabase.storage
        .from("mentor-videos")
        .getPublicUrl(filePath);

      // Get duration
      const video = document.createElement("video");
      video.preload = "metadata";
      
      video.onloadedmetadata = async () => {
        const duration = Math.round(video.duration);

        const { error: dbError } = await supabase
          .from("mentor_video_answers")
          .insert({
            question_id: questionId,
            video_url: publicUrl,
            video_file_name: fileName,
            duration_seconds: duration,
          });

        if (dbError) throw dbError;

        const { error: updateError } = await supabase
          .from("mentor_questions")
          .update({ status: "answered" })
          .eq("id", questionId);

        if (updateError) throw updateError;

        // Send notification to user
        await sendNotification(mentorName);

        toast({
          title: "Video Uploaded!",
          description: "Your video answer has been sent to the user.",
        });

        setSelectedFile(null);
        setRecordedBlob(null);
        setRecordedUrl(null);
        setUploadProgress(0);
        setMode("select");
        onSuccess?.();
      };

      video.onerror = () => {
        // Fallback if we can't get duration
        handleSaveWithDuration(recordingTime || 0, publicUrl, fileName, mentorName);
      };

      video.src = URL.createObjectURL(fileToUpload);
    } catch (error) {
      console.error("Error uploading video:", error);
      toast({
        title: "Upload Failed",
        description: "Failed to upload video. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSaveWithDuration = async (duration: number, publicUrl: string, fileName: string, mentorName: string) => {
    try {
      const { error: dbError } = await supabase
        .from("mentor_video_answers")
        .insert({
          question_id: questionId,
          video_url: publicUrl,
          video_file_name: fileName,
          duration_seconds: duration,
        });

      if (dbError) throw dbError;

      const { error: updateError } = await supabase
        .from("mentor_questions")
        .update({ status: "answered" })
        .eq("id", questionId);

      if (updateError) throw updateError;

      // Send notification to user
      await sendNotification(mentorName);

      toast({
        title: "Video Uploaded!",
        description: "Your video answer has been sent to the user.",
      });

      setSelectedFile(null);
      setRecordedBlob(null);
      setRecordedUrl(null);
      setUploadProgress(0);
      setMode("select");
      onSuccess?.();
    } catch (error) {
      console.error("Error saving video:", error);
    }
  };

  const goBack = () => {
    setMode("select");
    setSelectedFile(null);
    resetRecording();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Record Your Answer</CardTitle>
        <CardDescription className="line-clamp-2">{questionText}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        {mode === "select" && (
          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="outline"
              onClick={() => setMode("record")}
              className="h-24 flex-col gap-2"
            >
              <Camera className="h-6 w-6" />
              <span>Record Video</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setMode("upload");
                fileInputRef.current?.click();
              }}
              className="h-24 flex-col gap-2"
            >
              <Upload className="h-6 w-6" />
              <span>Upload Video</span>
            </Button>
          </div>
        )}

        {mode === "record" && (
          <div className="space-y-4">
            <div className="relative bg-muted rounded-lg overflow-hidden aspect-video">
              {!recordedUrl ? (
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                />
              ) : (
                <video
                  controls
                  className="w-full h-full object-cover"
                  src={recordedUrl}
                />
              )}
              
              {isRecording && (
                <div className="absolute top-3 left-3 flex items-center gap-2 bg-destructive text-destructive-foreground px-3 py-1 rounded-full text-sm">
                  <span className="h-2 w-2 bg-white rounded-full animate-pulse" />
                  {formatTime(recordingTime)} / {formatTime(MAX_DURATION)}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              {!recordedUrl ? (
                <>
                  {!isRecording ? (
                    <Button onClick={startRecording} className="flex-1">
                      <Camera className="mr-2 h-4 w-4" />
                      Start Recording
                    </Button>
                  ) : (
                    <Button onClick={stopRecording} variant="destructive" className="flex-1">
                      <Square className="mr-2 h-4 w-4" />
                      Stop Recording
                    </Button>
                  )}
                </>
              ) : (
                <>
                  <Button variant="outline" onClick={resetRecording} className="flex-1">
                    <Camera className="mr-2 h-4 w-4" />
                    Re-record
                  </Button>
                  <Button onClick={handleUpload} disabled={isUploading} className="flex-1">
                    {isUploading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload
                      </>
                    )}
                  </Button>
                </>
              )}
            </div>

            <Button variant="ghost" onClick={goBack} className="w-full">
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          </div>
        )}

        {mode === "upload" && (
          <div className="space-y-3">
            {selectedFile ? (
              <>
                <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                  <Video className="h-5 w-5 text-primary" />
                  <span className="flex-1 text-sm truncate">{selectedFile.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                    disabled={isUploading}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                
                {isUploading && (
                  <Progress value={uploadProgress} className="w-full" />
                )}
                
                <Button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="w-full"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Video Answer
                    </>
                  )}
                </Button>
              </>
            ) : (
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                className="w-full"
              >
                <Video className="mr-2 h-4 w-4" />
                Select Video File
              </Button>
            )}
            
            <Button variant="ghost" onClick={goBack} className="w-full">
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          </div>
        )}
        
        <p className="text-xs text-muted-foreground text-center">
          Maximum duration: 10 minutes • Maximum file size: 100MB
        </p>
      </CardContent>
    </Card>
  );
};
