import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import JobProgressBar from "../components/JobProgressBar";
import JobResultCard, { type JobFriendlySummary } from "../components/JobResultCard";
import PageIntro from "../components/PageIntro";
import DatasetSnapshotsPanel from "../components/DatasetSnapshotsPanel";
import ScheduledRetrainPanel from "../components/ScheduledRetrainPanel";
import TaskPipelineCard from "../components/TaskPipelineCard";
import { useJobProgress } from "../hooks/useJobProgress";
import { useJobSubmit } from "../hooks/useJobSubmit";
import { useSetupSteps, type SetupStep } from "../hooks/useSetupSteps";
import { useSystemStatus } from "../hooks/useSystemStatus";
import { getTaskById, type TaskPresetId } from "../lib/pipelineTasks";
import { mergeJobProgress } from "../lib/mergeJobProgress";
import { invalidateSystemStatus } from "../lib/statusEvents";

function defaultPresetForStep(stepId: string): TaskPresetId {
  if (stepId === "solve_preflop_8max") return "ring8";
  if (stepId === "solve_preflop_9max") return "ring9";
  if (stepId === "solve_preflop_10max") return "ring10";
  return "recommended";
}

const STEP_TO_TASK: Record<string, string> = {
  features: "features_build",
  equity_backfill: "equity_backfill",
  train_hhformer: "train_hhformer",
  solve_preflop: "solve_preflop",
  solve_preflop_8max: "solve_preflop",
  solve_preflop_9max: "solve_preflop",
  solve_preflop_10max: "solve_preflop",
  solve_grid: "solve_grid",
  train_student: "train_student",
  train_multiway: "train_multiway_student",
  train_cql: "train_cql",
  train_hhformer_finetune: "train_hhformer_finetune",
  train_style: "train_style",
  league: "league_run",
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

type ActiveSummary = { active: { job_id: string; type: string; status: string }[]; count: number };

function stepTitle(step: SetupStep, stepsById: Map<string, SetupStep>): string {
  const waiting = step.requires.find((r) => !stepsById.get(r)?.ready);
  if (waiting) {
    const other = stepsById.get(waiting);
    return `Waiting for: ${other?.title ?? waiting}`;
  }
  return step.ready ? "Done" : "Run";
}

export default function SetupPage() {
  const { data: setup, error: setupError, refresh: refreshSteps } = useSetupSteps(6000);
  const { data: sys } = useSystemStatus({ pollMs: 10_000 });
  const { submit, submitting, error: submitError, setError: setSubmitError } = useJobSubmit();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [workers, setWorkers] = useState(0);
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);
  const [taskPresets, setTaskPresets] = useState<Record<string, TaskPresetId>>({});
  const [taskParams, setTaskParams] = useState<Record<string, Record<string, unknown>>>({});
  const [busyAction, setBusyAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [texasPath, setTexasPath] = useState("");
  const [texasBusy, setTexasBusy] = useState(false);
  const progressRef = useRef<HTMLElement>(null);
  const { progress, connected } = useJobProgress(activeJobId);

  const stepsById = useMemo(
    () => new Map((setup?.steps ?? []).map((s) => [s.id, s])),
    [setup?.steps],
  );

  const refreshActive = useCallback(async () => {
    try {
      const active = await apiGet<ActiveSummary>("/jobs/active/summary");
      if (active.active[0]) {
        setActiveJobId((prev) => prev ?? active.active[0].job_id);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshActive();
    const id = window.setInterval(() => void refreshActive(), 4000);
    return () => clearInterval(id);
  }, [refreshActive]);

  useEffect(() => {
    if (!activeJobId) {
      setJobDetail(null);
      return;
    }
    const load = async () => {
      try {
        const d = await apiGet<JobDetail>(`/jobs/${activeJobId}`);
        setJobDetail(d);
        if (d.status === "done" || d.status === "error" || d.status === "cancelled") {
          invalidateSystemStatus();
          void refreshSteps();
        }
      } catch {
        /* ignore */
      }
    };
    void load();
    const id = window.setInterval(() => void load(), 1500);
    return () => clearInterval(id);
  }, [activeJobId, progress?.pct, progress?.status, refreshSteps]);

  useEffect(() => {
    if (activeJobId && progressRef.current) {
      progressRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeJobId]);

  const hasActive = (sys?.jobs_running ?? 0) + (sys?.jobs_queued ?? 0) > 0;
  const displayProgress = mergeJobProgress(progress, jobDetail);
  const activeStatus = displayProgress?.status ?? jobDetail?.status;
  const isLive = activeStatus === "running" || activeStatus === "queued";

  async function runStep(stepId: string, params?: Record<string, unknown>) {
    setError(null);
    setSubmitError(null);
    const taskId = STEP_TO_TASK[stepId];
    if (taskId && params) {
      const jobId = await submit(taskId, params, workers);
      if (jobId) {
        setActiveJobId(jobId);
        setExpandedStepId(null);
        invalidateSystemStatus();
        void refreshSteps();
      }
      return;
    }
    try {
      const { job_id } = await apiPost<{ job_id: string }>(`/setup/run/${stepId}`, {
        params: params ?? {},
      });
      setActiveJobId(job_id);
      setExpandedStepId(null);
      invalidateSystemStatus();
      void refreshSteps();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function registerTexas() {
    const p = texasPath.trim();
    if (!p) {
      setError("Enter the path to TexasSolver (console_solver).");
      return;
    }
    setTexasBusy(true);
    setError(null);
    try {
      await apiPost("/setup/texas/register", { exe_path: p });
      invalidateSystemStatus();
      void refreshSteps();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTexasBusy(false);
    }
  }

  async function stopJob() {
    if (!activeJobId) return;
    setBusyAction(true);
    try {
      await apiPost(`/jobs/${activeJobId}/cancel`, {});
      invalidateSystemStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyAction(false);
    }
  }

  const friendly = displayProgress?.friendly ?? jobDetail?.friendly ?? null;
  const technical = displayProgress?.result ?? jobDetail?.result ?? null;

  return (
    <div className="space-y-6 max-w-3xl">
      <ApiOfflineBanner suppressWhenBusy={hasActive} />

      <PageIntro
        title="Setup wizard"
        description="Run the full AI pipeline in order — same jobs as the CLI and Tasks page. One task at a time; use Advanced to match CLI flags."
      />

      {setup && (
        <p className="text-sm text-slate-400">
          <strong className="text-emerald-300">{setup.ready_count}</strong> step
          {setup.ready_count === 1 ? "" : "s"} ready ·{" "}
          <strong className="text-amber-300">{setup.pending_count}</strong> required step
          {setup.pending_count === 1 ? "" : "s"} still to do
        </p>
      )}

      {(error || submitError || setupError) && (
        <p className="text-sm text-red-400 border border-red-900/50 rounded-md px-3 py-2">
          {error ?? submitError ?? setupError}
        </p>
      )}

      <ol className="space-y-3">
        {(setup?.steps ?? []).map((step, idx) => {
          const taskId = STEP_TO_TASK[step.id];
          const task = taskId ? getTaskById(taskId) : undefined;
          const expanded = expandedStepId === step.id;
          const waitingLabel = step.requires.find((r) => !stepsById.get(r)?.ready);
          const presetId = taskPresets[step.id] ?? defaultPresetForStep(step.id);

          return (
            <li
              key={step.id}
              className={`rounded-xl border overflow-hidden ${
                step.ready
                  ? "border-emerald-800/50 bg-emerald-950/15"
                  : "border-slate-700 bg-slate-900/50"
              }`}
            >
              <div className="px-4 py-3 flex flex-wrap items-start gap-3">
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                    step.ready
                      ? "bg-emerald-700 text-white"
                      : "bg-slate-700 text-slate-300"
                  }`}
                  aria-hidden
                >
                  {step.ready ? "✓" : idx + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-medium text-slate-100">{step.title}</h3>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
                  <p className="text-sm text-slate-300 mt-1">{step.detail}</p>
                </div>
                <div className="flex flex-wrap gap-2 shrink-0">
                  {step.id === "ingest" ? (
                    <Link
                      to="/import"
                      className="px-4 py-2 rounded-md bg-emerald-700 text-white text-sm font-medium hover:bg-emerald-600"
                    >
                      Open import
                    </Link>
                  ) : waitingLabel ? (
                    <span className="px-3 py-2 text-sm text-slate-500">
                      {stepTitle(step, stepsById)}
                    </span>
                  ) : (
                    <>
                      <button
                        type="button"
                        disabled={submitting || hasActive || !step.can_run}
                        onClick={() => void runStep(step.id)}
                        className="px-4 py-2 rounded-md bg-emerald-700 text-white text-sm font-medium hover:bg-emerald-600 disabled:opacity-50"
                      >
                        {hasActive ? "Busy…" : stepTitle(step, stepsById)}
                      </button>
                      {task && (
                        <button
                          type="button"
                          disabled={submitting || hasActive || !step.can_run}
                          onClick={() =>
                            setExpandedStepId(expanded ? null : step.id)
                          }
                          className="px-3 py-2 rounded-md border border-slate-600 text-slate-300 text-sm hover:bg-slate-800 disabled:opacity-50"
                        >
                          Advanced
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>

              {step.id === "solve_grid" && step.texas_solver_found === false && (
                <div className="mx-4 mb-3 rounded-lg border border-amber-800/40 bg-amber-950/20 p-3 space-y-2 text-sm">
                  <p className="text-amber-100/90 font-medium">TexasSolver setup</p>
                  <p className="text-xs text-slate-400">
                    Register an existing binary, or use{" "}
                    <Link to="/health" className="text-emerald-400 hover:underline">
                      System health
                    </Link>{" "}
                    to build from source. You can also run with mock labels (lower quality).
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <input
                      type="text"
                      value={texasPath}
                      onChange={(e) => setTexasPath(e.target.value)}
                      placeholder="C:\Tools\TexasSolver\console_solver.exe"
                      className="flex-1 min-w-[12rem] px-2 py-1.5 rounded bg-slate-900 border border-slate-600 text-xs font-mono"
                    />
                    <button
                      type="button"
                      disabled={texasBusy}
                      onClick={() => void registerTexas()}
                      className="px-3 py-1.5 rounded bg-slate-700 text-white text-xs hover:bg-slate-600 disabled:opacity-50"
                    >
                      {texasBusy ? "Checking…" : "Register"}
                    </button>
                  </div>
                </div>
              )}

              {expanded && task && sys && (
                <div className="border-t border-slate-700 px-2 pb-2">
                  <TaskPipelineCard
                    task={task}
                    sys={sys}
                    expanded
                    onExpand={() => {}}
                    onCollapse={() => setExpandedStepId(null)}
                    hasActiveJob={hasActive}
                    submitting={submitting}
                    submitError={submitError}
                    workers={workers}
                    onWorkers={setWorkers}
                    onQuickStart={(p) => void runStep(step.id, p)}
                    onStart={(p) => void runStep(step.id, p)}
                    presetId={presetId}
                    onPresetId={(id) => setTaskPresets((prev) => ({ ...prev, [step.id]: id }))}
                    params={taskParams[step.id] ?? {}}
                    onParams={(p) => setTaskParams((prev) => ({ ...prev, [step.id]: p }))}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {activeJobId && (
        <section
          ref={progressRef}
          className="space-y-3 rounded-xl border-2 border-emerald-600/50 bg-emerald-950/20 p-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-emerald-100">Current task</h3>
            {connected && isLive && (
              <span className="text-xs text-emerald-400 bg-emerald-900/50 px-2 py-0.5 rounded">
                Live
              </span>
            )}
            {isLive && (
              <button
                type="button"
                disabled={busyAction}
                onClick={() => void stopJob()}
                className="ml-auto text-sm px-3 py-1 rounded-md border border-amber-600 text-amber-300 hover:bg-amber-950/50 disabled:opacity-50"
              >
                {busyAction ? "Stopping…" : "Stop"}
              </button>
            )}
            <Link to="/jobs" className="text-xs text-emerald-400 hover:underline">
              Tasks history →
            </Link>
          </div>
          <JobProgressBar progress={displayProgress} startedAt={jobDetail?.started_at} />
          {(progress?.status === "done" ||
            progress?.status === "error" ||
            jobDetail?.status === "done" ||
            jobDetail?.status === "error") && (
            <JobResultCard
              friendly={friendly}
              jobType={jobDetail?.type ?? ""}
              technicalResult={technical}
              hasActiveJob={hasActive}
            />
          )}
        </section>
      )}

      <DatasetSnapshotsPanel />

      <ScheduledRetrainPanel />

      <p className="text-sm text-slate-500">
        <Link to="/status" className="text-emerald-400 hover:underline">
          System status
        </Link>{" "}
        ·{" "}
        <Link to="/jobs" className="text-emerald-400 hover:underline">
          All tasks
        </Link>
      </p>
    </div>
  );
}
