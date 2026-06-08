import { useEffect, useMemo, useState } from "react";
import type { JobProgress } from "../hooks/useJobProgress";

type Props = {
  progress: JobProgress | null;
  startedAt?: string | null;
  className?: string;
};

function formatDuration(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  if (m < 60) return `${m}m ${s}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export default function JobProgressBar({ progress, startedAt, className = "" }: Props) {
  const [now, setNow] = useState(() => Date.now());
  const startMs = useMemo(() => {
    if (!startedAt) return null;
    const t = Date.parse(startedAt);
    return Number.isNaN(t) ? null : t;
  }, [startedAt]);

  useEffect(() => {
    if (!progress || progress.status === "done" || progress.status === "error") return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [progress]);

  if (!progress) return null;

  const status = progress.status;
  const detail = progress.detail;
  const workers =
    detail && typeof detail.workers === "number" ? Math.max(1, detail.workers) : 1;
  const shardsDone =
    detail && typeof detail.shards_done === "number" ? detail.shards_done : 0;
  const parallel = Boolean(detail && detail.parallel);
  const pct = Math.min(100, Math.max(0, progress.pct ?? 0));
  const elapsedSec = startMs != null ? (now - startMs) / 1000 : null;
  const etaSec = (() => {
    if (elapsedSec == null || pct <= 2 || pct >= 100) return null;
    if (parallel && workers > 1 && shardsDone > 0) {
      const shardPct = 7 + (83 * shardsDone) / workers;
      if (shardPct <= 2) return null;
      return (elapsedSec / shardPct) * (100 - shardPct);
    }
    return (elapsedSec / pct) * (100 - pct);
  })();

  const barColor =
    status === "error"
      ? "bg-red-500"
      : status === "cancelled"
        ? "bg-slate-500"
        : status === "done"
          ? "bg-emerald-500"
          : "bg-emerald-400";

  return (
    <div className={`rounded-lg border border-slate-700 bg-slate-900/60 p-4 ${className}`}>
      <div className="flex items-center justify-between gap-2 text-sm mb-2">
        <span className="text-slate-200 truncate" title={progress.msg}>
          {status === "done" ? "✓ " : status === "error" ? "✗ " : ""}
          {progress.msg || "Working…"}
        </span>
        <span className="text-slate-400 tabular-nums shrink-0">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
        {elapsedSec != null && <span>Elapsed: {formatDuration(elapsedSec)}</span>}
        {etaSec != null && <span>Est. remaining: {formatDuration(etaSec)}</span>}
      </div>
      {status === "error" && progress.error && (
        <p className="mt-2 text-sm text-red-400 break-words">
          {progress.friendly?.explanation ?? progress.error}
        </p>
      )}
    </div>
  );
}
