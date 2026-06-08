import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost, apiPostForm } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import JobProgressBar from "../components/JobProgressBar";
import JobResultCard, { type JobFriendlySummary } from "../components/JobResultCard";
import PageIntro from "../components/PageIntro";
import WorkerControl from "../components/WorkerControl";
import { useJobProgress } from "../hooks/useJobProgress";
import { mergeJobProgress } from "../lib/mergeJobProgress";

type IngestStatus = {
  total_hands: number;
  last_job_id: string | null;
  last_job_status: string | null;
  message: string;
};

type SuggestedPath = { label: string; path: string; exists: boolean };

type IngestPreview = {
  path: string;
  files_found: number;
  includes_subfolders: boolean;
  total_hands_in_library: number;
  message: string;
};

type JobDetail = {
  job_id: string;
  type: string;
  status: string;
  started_at: string | null;
  progress: { pct: number; msg: string } | null;
  friendly: JobFriendlySummary | null;
  result: Record<string, unknown> | null;
};

const NEW_HAND_PRESETS = [
  { label: "All new hands", value: 0 },
  { label: "1,000 new", value: 1000 },
  { label: "5,000 new", value: 5000 },
  { label: "10,000 new", value: 10000 },
  { label: "25,000 new", value: 25000 },
] as const;

export default function ImportPage() {
  const [status, setStatus] = useState<IngestStatus | null>(null);
  const [suggested, setSuggested] = useState<SuggestedPath[]>([]);
  const [folderPath, setFolderPath] = useState("");
  const [maxNewHands, setMaxNewHands] = useState(10_000);
  const [preview, setPreview] = useState<IngestPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [workers, setWorkers] = useState(0);
  const [workerInfo, setWorkerInfo] = useState<{
    recommended: number;
    max_safe: number;
    current_env: number;
    explanation: string;
    by_task?: Record<string, number>;
  } | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const progressRef = useRef<HTMLElement>(null);
  const { progress: wsProgress, connected } = useJobProgress(activeJobId);

  const refreshStatus = useCallback(async () => {
    try {
      const s = await apiGet<IngestStatus>("/ingest/status");
      setStatus(s);
      setError(null);
      if (
        s.last_job_id &&
        (s.last_job_status === "running" || s.last_job_status === "queued") &&
        !activeJobId
      ) {
        setActiveJobId(s.last_job_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [activeJobId]);

  useEffect(() => {
    void refreshStatus();
    void (async () => {
      try {
        const s = await apiGet<{ workers: typeof workerInfo }>("/status");
        setWorkerInfo(s.workers);
      } catch {
        /* API offline — ApiOfflineBanner handles UX */
      }
    })();
    void (async () => {
      try {
        const paths = await apiGet<SuggestedPath[]>("/ingest/suggested-paths");
        setSuggested(paths);
        const project = paths.find((p) => p.label.includes("Hand histories") && p.exists);
        if (project && !folderPath) setFolderPath(project.path);
      } catch {
        /* ignore when server down */
      }
    })();
  }, [refreshStatus, folderPath]);

  useEffect(() => {
    if (!activeJobId) return;
    const load = async () => {
      try {
        const d = await apiGet<JobDetail>(`/jobs/${activeJobId}`);
        setJobDetail(d);
        if (d.status === "done" || d.status === "error" || d.status === "cancelled") {
          void refreshStatus();
        }
      } catch {
        /* ignore */
      }
    };
    void load();
    const id = window.setInterval(() => void load(), 1500);
    return () => clearInterval(id);
  }, [activeJobId, wsProgress?.pct, refreshStatus]);

  useEffect(() => {
    if (activeJobId && progressRef.current) {
      progressRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeJobId]);

  const libraryTotal = status?.total_hands ?? 0;
  const projectedTotal = maxNewHands > 0 ? libraryTotal + maxNewHands : null;
  const displayProgress = mergeJobProgress(wsProgress, jobDetail);
  const importActive =
    jobDetail?.status === "running" ||
    jobDetail?.status === "queued" ||
    wsProgress?.status === "running";

  async function startJob(jobId: string) {
    setActiveJobId(jobId);
    setError(null);
    setJobDetail(null);
  }

  async function browseFolder() {
    setBusy(true);
    setError(null);
    try {
      const res = await apiPost<{ path: string; cancelled: boolean }>("/ingest/browse-folder", {});
      if (res.cancelled || !res.path) {
        return;
      }
      setFolderPath(res.path);
      setPreview(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runPreview() {
    const path = folderPath.trim();
    if (!path) {
      setError('Click "Browse on this PC" or paste a folder path below.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const p = await apiPost<IngestPreview>("/ingest/preview", {
        path,
        max_hands: maxNewHands,
        workers: 0,
      });
      setPreview(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function importFolder() {
    const path = folderPath.trim();
    if (!path) {
      setError('Choose a folder with "Browse on this PC" or paste the full path.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const { job_id } = await apiPost<{ job_id: string }>("/ingest/local", {
        path,
        max_hands: maxNewHands,
        workers: maxNewHands > 0 ? 1 : workers,
      });
      await startJob(job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const friendly = wsProgress?.friendly ?? jobDetail?.friendly ?? null;
  const technical = wsProgress?.result ?? jobDetail?.result ?? null;
  async function uploadFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    setUploadBusy(true);
    setError(null);
    try {
      const form = new FormData();
      for (const f of Array.from(fileList)) {
        form.append("files", f);
      }
      const qs = new URLSearchParams({
        max_hands: String(maxNewHands),
        workers: String(workers),
      });
      const { job_id } = await apiPostForm<{ job_id: string }>(
        `/ingest/upload?${qs}`,
        form,
      );
      await startJob(job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploadBusy(false);
    }
  }

  async function cancelImport() {
    if (!activeJobId) return;
    setCancelling(true);
    try {
      await apiPost(`/jobs/${activeJobId}/cancel`, {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCancelling(false);
    }
  }

  const showResult =
    jobDetail?.status === "done" ||
    jobDetail?.status === "error" ||
    wsProgress?.status === "done" ||
    wsProgress?.status === "error";

  return (
    <div className="space-y-8 max-w-3xl">
      <ApiOfflineBanner suppressWhenBusy={busy || importActive || uploadBusy} />

      <PageIntro
        title="Import hand histories"
        description="For large folders on your PC (tens or hundreds of GB), use the path below — we read files directly from disk. All subfolders are included. Duplicates are skipped for your library count."
      />

      {status && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 px-4 py-3">
          <p className="text-lg text-slate-100">
            Library size: <strong>{libraryTotal.toLocaleString()}</strong> hands
          </p>
          <p className="text-sm text-slate-400 mt-1">{status.message}</p>
          {libraryTotal > 0 && (
            <p className="text-sm mt-2">
              <Link to="/" className="text-emerald-400 hover:underline">
                Browse hands in replayer
              </Link>
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400 border border-red-900/50 rounded-md px-3 py-2">{error}</p>
      )}

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-slate-300">How many new hands to add?</h3>
        <p className="text-xs text-slate-500">
          Only <strong className="text-slate-400">new</strong> hands count. Re-importing the same
          hands updates them but does not increase library size.
        </p>
        <div className="flex flex-wrap gap-2">
          {NEW_HAND_PRESETS.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => setMaxNewHands(p.value)}
              className={`px-3 py-1.5 text-sm rounded-md border ${
                maxNewHands === p.value
                  ? "border-emerald-500 bg-emerald-900/40 text-emerald-100"
                  : "border-slate-600 text-slate-300 hover:border-slate-500"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        {projectedTotal !== null && (
          <p className="text-sm text-emerald-300/90">
            Up to <strong>{maxNewHands.toLocaleString()}</strong> new hands this run → library could
            reach ~{projectedTotal.toLocaleString()} (from {libraryTotal.toLocaleString()} now).
          </p>
        )}
        {maxNewHands === 0 && (
          <WorkerControl
            value={workers}
            onChange={setWorkers}
            workers={workerInfo}
            taskHint="ingest"
            disabled={importActive || busy}
            note="Used only when importing all new hands with no cap."
          />
        )}
        {maxNewHands > 0 && (
          <p className="text-xs text-slate-500">
            With a new-hands limit, import uses 1 worker so it can stop exactly at your cap.
          </p>
        )}
      </section>

      <section className="space-y-3 rounded-xl border border-emerald-900/40 bg-slate-900/30 p-4">
        <h3 className="text-base font-medium text-slate-100">Your hand history folder</h3>
        <p className="text-xs text-slate-500 leading-relaxed">
          Do <strong className="text-slate-400">not</strong> use browser upload for huge collections
          (200 GB+). Paste a path or use <strong className="text-slate-400">Browse on this PC</strong>{" "}
          — the same as <code className="text-slate-400">poker_ai ingest D:\your\folder</code> in the
          terminal.
        </p>
        <div className="flex flex-wrap gap-2">
          {suggested
            .filter((s) => s.exists)
            .map((s) => (
              <button
                key={s.path}
                type="button"
                onClick={() => {
                  setFolderPath(s.path);
                  setPreview(null);
                }}
                className="px-3 py-1.5 text-xs rounded-md bg-slate-800 text-slate-200 hover:bg-slate-700"
              >
                {s.label}
              </button>
            ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void browseFolder()}
            className="px-4 py-2 rounded-md bg-slate-700 text-white text-sm hover:bg-slate-600 disabled:opacity-50"
          >
            Browse on this PC…
          </button>
        </div>
        <input
          type="text"
          value={folderPath}
          onChange={(e) => {
            setFolderPath(e.target.value);
            setPreview(null);
          }}
          placeholder="D:\Poker AI\hand\poker-hand-histories"
          className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-600 text-slate-100 text-sm font-mono"
        />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || importActive}
            onClick={() => void runPreview()}
            className="px-4 py-2 rounded-md border border-slate-600 text-slate-200 text-sm hover:bg-slate-800 disabled:opacity-50"
          >
            {busy && !importActive ? "Scanning folder…" : "Scan folder first"}
          </button>
          <button
            type="button"
            disabled={busy || importActive}
            onClick={() => void importFolder()}
            className="px-5 py-2.5 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
          >
            {importActive ? "Import running…" : "Start import"}
          </button>
        </div>
        {preview && (
          <p className="text-sm text-slate-300 border border-slate-700 rounded-md px-3 py-2 bg-slate-950/50">
            {preview.message}
          </p>
        )}
      </section>

      {(activeJobId || importActive) && (
        <section
          ref={progressRef}
          className="space-y-3 rounded-xl border-2 border-emerald-600/50 bg-emerald-950/20 p-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-emerald-100">Import progress</h3>
            {connected && (
              <span className="text-xs text-emerald-400 bg-emerald-900/50 px-2 py-0.5 rounded">
                Live
              </span>
            )}
            {importActive && (
              <span className="text-xs text-amber-200/90">
                Large folders can take hours — keep this page open or check Tasks later.
              </span>
            )}
            {importActive && (
              <button
                type="button"
                disabled={cancelling}
                onClick={() => void cancelImport()}
                className="text-sm px-3 py-1 rounded-md border border-amber-600 text-amber-300 hover:bg-amber-950/50 disabled:opacity-50"
              >
                {cancelling ? "Stopping…" : "Stop import"}
              </button>
            )}
            <Link
              to="/jobs"
              className="text-xs text-emerald-400 hover:underline ml-auto"
            >
              Open Tasks page
            </Link>
          </div>
          <JobProgressBar
            progress={displayProgress}
            startedAt={jobDetail?.started_at}
          />
          {showResult && (
            <JobResultCard
              friendly={friendly}
              jobType={jobDetail?.type ?? "ingest"}
              technicalResult={technical}
              hasActiveJob={importActive}
            />
          )}
        </section>
      )}

      <details className="text-sm text-slate-500 rounded-lg border border-slate-800 p-3">
        <summary className="cursor-pointer text-slate-400 hover:text-slate-300">
          Small upload only (not for large folders)
        </summary>
        <p className="mt-2 text-xs leading-relaxed">
          Drag-and-drop copies files through the browser. Use only for a few hundred files, not
          200 GB archives. Uses the same new-hands cap and workers as above.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.json,.phh,.phhs"
          className="hidden"
          onChange={(e) => {
            void uploadFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <div
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click();
          }}
          onDragOver={(e) => {
            e.preventDefault();
            e.currentTarget.classList.add("border-emerald-500");
          }}
          onDragLeave={(e) => {
            e.currentTarget.classList.remove("border-emerald-500");
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.currentTarget.classList.remove("border-emerald-500");
            void uploadFiles(e.dataTransfer.files);
          }}
          onClick={() => fileInputRef.current?.click()}
          className="mt-3 rounded-lg border-2 border-dashed border-slate-600 bg-slate-950/40 px-4 py-8 text-center cursor-pointer hover:border-slate-500 transition-colors"
        >
          <p className="text-slate-300 text-sm">
            {uploadBusy ? "Uploading…" : "Drag files here or click to browse"}
          </p>
          <p className="text-xs text-slate-500 mt-1">Supported: .txt · .phh · .phhs · .json</p>
        </div>
      </details>
    </div>
  );
}
