import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import ArtifactPathLink from "../components/ArtifactPathLink";
import ModelTaskActions from "../components/ModelTaskActions";
import { Card } from "../components/Card";
import PageIntro from "../components/PageIntro";
import { useSystemStatus, type ModelStatus, type SystemStatus } from "../hooks/useSystemStatus";
import { computeReadiness, countMissingModels } from "../lib/systemReadiness";
import { buildTaskJobsUrl } from "../lib/taskNavigation";
import SmokeTestPanel from "../components/SmokeTestPanel";
import { invalidateSystemStatus } from "../lib/statusEvents";

// ---------------------------------------------------------------------------
// Row helpers
// ---------------------------------------------------------------------------

function OkBadge({ ok }: { ok: boolean }) {
  return (
    <span
      className={`text-sm font-medium tabular-nums ${ok ? "text-emerald-400" : "text-red-400"}`}
      aria-label={ok ? "Ready" : "Not ready"}
    >
      {ok ? "✓" : "✗"}
    </span>
  );
}

function StatusRow({
  label,
  value,
  ok,
  detail,
  children,
}: {
  label: string;
  value: string;
  ok: boolean;
  detail?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2 py-3 border-b border-slate-700/60 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-slate-200">{label}</div>
          <div className="text-sm text-slate-400 mt-0.5 break-words">{value}</div>
          {detail && <p className="text-xs text-slate-500 mt-1 leading-relaxed">{detail}</p>}
        </div>
        <OkBadge ok={ok} />
      </div>
      {children}
    </div>
  );
}

function formatHands(n: number | null | undefined): string {
  if (n == null) return "Unknown";
  return n.toLocaleString();
}

function workerLabel(w: SystemStatus["workers"]): string {
  const cur = w.current_env;
  if (cur === 0) return `Auto (≈ ${w.recommended} recommended on this PC)`;
  return `${cur} worker${cur === 1 ? "" : "s"} configured`;
}

type SystemRow = {
  key: string;
  label: string;
  value: string;
  ok: boolean;
  detail?: string;
  extra?: ReactNode;
};

function buildSystemRows(data: SystemStatus): { dbOk: boolean; rows: SystemRow[] } {
  const dbOk = (data.db_hands ?? 0) > 0;
  const gpuOk = data.gpu?.cuda_available === true;
  const workersOk = !data.workers.warning;
  const texasOk = data.texas_solver.found;

  return {
    dbOk,
    rows: [
      {
        key: "db",
        label: "Database",
        value: `${formatHands(data.db_hands)} hands · schema ${data.db_revision ?? "?"}`,
        ok: dbOk,
        detail: dbOk
          ? "Hand library is loaded and migrations are up to date."
          : "Import hand histories first, then run Prepare hands on Tasks.",
        extra: !dbOk ? (
          <Link
            to="/import"
            className="inline-flex text-sm text-emerald-400 hover:text-emerald-300 underline"
          >
            Import hands →
          </Link>
        ) : null,
      },
      {
        key: "gpu",
        label: "GPU / CUDA",
        value: data.gpu
          ? `${data.gpu.name} · ${data.gpu.vram_gb.toFixed(1)} GB VRAM${
              data.gpu.cuda_version ? ` · CUDA ${data.gpu.cuda_version}` : ""
            }`
          : "No NVIDIA GPU detected",
        ok: gpuOk,
        detail: data.gpu
          ? data.gpu.cuda_available
            ? `Driver ${data.gpu.driver_version}. Use device “Auto” or “CUDA” when training.`
            : "GPU present but CUDA not available in PyTorch — install a CUDA build for faster training."
          : "CPU-only works for quick tests; HHFormer and student train much faster on GPU.",
      },
      {
        key: "workers",
        label: "CPU workers",
        value: workerLabel(data.workers),
        ok: workersOk,
        detail: data.workers.warning ?? data.workers.explanation,
        extra: data.workers.warning ? (
          <p className="text-xs text-amber-200/90 rounded-md border border-amber-800/40 bg-amber-900/20 px-3 py-2">
            {data.workers.warning}
          </p>
        ) : (
          <Link
            to="/jobs"
            className="text-xs text-slate-500 hover:text-emerald-400"
          >
            Adjust workers when starting CPU tasks on Tasks →
          </Link>
        ),
      },
      {
        key: "texas",
        label: "TexasSolver",
        value: data.texas_solver.found
          ? (data.texas_solver.version ?? "Installed")
          : "Not installed",
        ok: texasOk,
        detail: data.texas_solver.note ?? undefined,
        extra: !texasOk ? (
          <Link
            to="/health"
            className="inline-flex text-sm text-emerald-400 hover:text-emerald-300 underline"
          >
            Install via System health →
          </Link>
        ) : null,
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StatusPage() {
  const { status, data, error, lastUpdated, recheck } = useSystemStatus({ pollMs: 5000 });
  const [showWorkerTasks, setShowWorkerTasks] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const jobsActive = ((data?.jobs_running ?? 0) + (data?.jobs_queued ?? 0)) > 0;

  async function handleRefresh() {
    setRefreshing(true);
    recheck();
    invalidateSystemStatus();
    await new Promise((r) => setTimeout(r, 400));
    setRefreshing(false);
  }

  const readiness = computeReadiness(data);
  const system = data ? buildSystemRows(data) : null;
  const missing = data ? countMissingModels(data) : 0;

  return (
    <div>
      <PageIntro
        title="System status"
        description="Everything the app uses — database, hardware, and all trained models. Each missing item has a Quick test or Configure & run button with the same settings as the CLI and Tasks page."
      />

      <ApiOfflineBanner suppressWhenBusy={jobsActive} />

      {status === "error" && error && (
        <p className="text-sm text-red-300 mb-4">{error}</p>
      )}

      {status === "loading" && !data && (
        <p className="text-sm text-slate-400 animate-pulse">Loading system status…</p>
      )}

      {data && system && (
        <div className="space-y-6">
          <div
            className={`rounded-lg border px-4 py-3 flex flex-wrap items-center gap-3 ${
              readiness === "ready"
                ? "border-emerald-800/50 bg-emerald-900/15"
                : readiness === "partial"
                  ? "border-amber-800/50 bg-amber-900/15"
                  : "border-red-800/50 bg-red-900/15"
            }`}
          >
            <span
              className={`text-sm font-medium ${
                readiness === "ready"
                  ? "text-emerald-300"
                  : readiness === "partial"
                    ? "text-amber-300"
                    : "text-red-300"
              }`}
            >
              {readiness === "ready"
                ? "Full pipeline ready — all 7 artifacts built"
                : missing > 0
                  ? `${missing} item${missing === 1 ? "" : "s"} still to build — use the buttons below`
                  : "Import hands to begin"}
            </span>
            <span className="text-xs text-slate-500">
              {data.os_name} · poker_ai v{data.version}
              {lastUpdated && (
                <> · updated {lastUpdated.toLocaleTimeString()}</>
              )}
              {jobsActive && (
                <span className="text-amber-400/90"> · task running (auto-refresh)</span>
              )}
            </span>
            <button
              type="button"
              onClick={() => void handleRefresh()}
              disabled={refreshing}
              className="ml-auto text-xs px-3 py-1 rounded-md border border-slate-600 text-slate-300 hover:border-slate-500 disabled:opacity-50"
            >
              {refreshing ? "Refreshing…" : "Refresh now"}
            </button>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="System">
              {system.rows.map((row) => (
                <StatusRow
                  key={row.key}
                  label={row.label}
                  value={row.value}
                  ok={row.ok}
                  detail={row.detail}
                >
                  {row.extra}
                </StatusRow>
              ))}

              <details
                className="mt-3 pt-3 border-t border-slate-700/60"
                open={showWorkerTasks}
                onToggle={(e) => setShowWorkerTasks((e.target as HTMLDetailsElement).open)}
              >
                <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400">
                  Per-task worker hints (CPU-bound jobs)
                </summary>
                <ul className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs font-mono text-slate-400">
                  {Object.entries(data.workers.by_task).map(([task, n]) => (
                    <li key={task} className="flex justify-between gap-2">
                      <span className="truncate">{task}</span>
                      <span className="text-slate-300">{n}</span>
                    </li>
                  ))}
                </ul>
              </details>

              <div className="mt-3 pt-3 border-t border-slate-700/60 text-xs text-slate-500 space-y-1">
                <p>
                  {data.cpu.name} · {data.cpu.physical_cores} physical /{" "}
                  {data.cpu.logical_cores} logical cores
                </p>
                <p>
                  RAM {data.ram.available_gb.toFixed(1)} / {data.ram.total_gb.toFixed(1)} GB free ·
                  Disk {data.disk.free_gb.toFixed(0)} / {data.disk.total_gb.toFixed(0)} GB free
                </p>
              </div>
            </Card>

            <Card title="Models & strategy files">
              <p className="text-xs text-slate-500 mb-3 -mt-1 leading-relaxed">
                All seven artifacts are used in production. Quick test runs small CLI-equivalent
                jobs; Configure & run lets you set epochs, device (CPU/CUDA), workers, and spot
                counts before starting.
              </p>
              <div className="space-y-4">
                {data.models.map((m) => (
                  <ModelRow
                    key={m.name}
                    model={m}
                    status={data}
                    hasActiveJob={jobsActive}
                    defaultOpen={!m.ready}
                  />
                ))}
              </div>
            </Card>
          </div>

          <SmokeTestPanel />

          <Card>
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <p className="text-sm text-slate-300">
                  Active jobs:{" "}
                  <span className="font-medium text-slate-100">
                    {data.jobs_running} running · {data.jobs_queued} queued
                  </span>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Only one task runs at a time. Progress updates here when you refresh or every few
                  seconds.
                </p>
              </div>
              <div className="ml-auto flex flex-wrap gap-2">
                <Link
                  to="/setup"
                  className="rounded-lg border border-emerald-700 px-4 py-2 text-sm font-semibold text-emerald-200 hover:bg-emerald-900/30"
                >
                  Setup wizard →
                </Link>
                <Link
                  to="/jobs"
                  className="rounded-lg bg-emerald-700 hover:bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
                >
                  All tasks →
                </Link>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

function ModelRow({
  model,
  status,
  hasActiveJob,
  defaultOpen,
}: {
  model: ModelStatus;
  status: SystemStatus;
  hasActiveJob: boolean;
  defaultOpen?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border px-3 py-2.5 ${
        model.ready ? "border-slate-700/80 bg-slate-950/30" : "border-amber-800/40 bg-amber-950/15"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-slate-200">{model.name}</div>
          <div className="text-xs text-slate-500 mt-0.5">
            {model.ready
              ? model.trained_at
                ? `Ready · trained ${model.trained_at}`
                : "Ready"
              : "Not built yet"}
            {model.ready && model.path && (
              <span className="block mt-1">
                <ArtifactPathLink path={model.path} />
              </span>
            )}
          </div>
        </div>
        <OkBadge ok={model.ready} />
      </div>

      {!model.ready && (
        <ModelTaskActions
          model={model}
          status={status}
          hasActiveJob={hasActiveJob}
          defaultOpen={defaultOpen}
          onStarted={() => {
            /* poll will pick up active job */
          }}
        />
      )}

      {model.ready && (
        <div className="mt-2 flex flex-wrap gap-2">
          <Link
            to={buildTaskJobsUrl(model.job_type ?? "", {
              status,
              model: model.name,
              preset: "recommended",
              forceTask: true,
            })}
            className="text-xs text-slate-500 hover:text-emerald-400"
          >
            Rebuild on Tasks →
          </Link>
        </div>
      )}
    </div>
  );
}
