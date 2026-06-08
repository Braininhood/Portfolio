import { useCallback, useEffect, useRef, useState } from "react";
import { jobWebSocketUrl } from "../api/client";
import type { JobFriendlySummary } from "../components/JobResultCard";

export type JobProgress = {
  pct: number;
  msg: string;
  detail?: Record<string, unknown>;
  status?: "done" | "error" | "cancelled" | "running" | "queued";
  result?: Record<string, unknown>;
  error?: string;
  friendly?: JobFriendlySummary;
};

export function useJobProgress(jobId: string | null) {
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const close = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!jobId) {
      setProgress(null);
      close();
      return;
    }
    setProgress({ pct: 0, msg: "Connecting…" });
    const ws = new WebSocket(jobWebSocketUrl(jobId));
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      ws.send("ping");
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as JobProgress;
        setProgress(data);
        if (data.status === "done" || data.status === "error" || data.status === "cancelled") {
          ws.close();
        }
      } catch {
        /* ignore malformed */
      }
    };
    ws.onerror = () => {
      setProgress((p) => ({
        pct: p?.pct ?? 0,
        msg: "WebSocket error — check API is running",
        status: "error",
        error: "connection failed",
      }));
    };
    ws.onclose = () => setConnected(false);
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [jobId, close]);

  return { progress, connected, close };
}
