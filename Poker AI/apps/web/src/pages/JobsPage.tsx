import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet, apiPost } from "../api/client";
import JobProgressBar from "../components/JobProgressBar";
import JobResultCard, { type JobFriendlySummary } from "../components/JobResultCard";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import AiPipelineGuide from "../components/AiPipelineGuide";
import PageIntro from "../components/PageIntro";
import TaskPipelineCard from "../components/TaskPipelineCard";
import { useJobProgress } from "../hooks/useJobProgress";
import { useJobSubmit } from "../hooks/useJobSubmit";
import { useSystemStatus } from "../hooks/useSystemStatus";
import { jobStatusLabel, jobTypeLabel } from "../lib/jobLabels";
import { getTaskById, pipelineTasksForJobs, type TaskPresetId } from "../lib/pipelineTasks";
import { mergeJobProgress } from "../lib/mergeJobProgress";
import { invalidateSystemStatus } from "../lib/statusEvents";

type JobSummary = {
  job_id: string;
  type: string;
  status: string;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  progress: { pct: number; msg: string } | null;
  error: string | null;
};

type JobDetail = JobSummary & {
  friendly: JobFriendlySummary | null;
  result: Record<string, unknown> | null;
};

type JobListResponse = { jobs: JobSummary[]; total: number };
type ActiveSummary = { active: JobSummary[]; count: number };

const { core: CORE_TASK_CARDS, extra: EXTRA_TASK_CARDS } = pipelineTasksForJobs();
const ALL_TASK_CARDS = [...CORE_TASK_CARDS, ...EXTRA_TASK_CARDS];

const STATUS_CLASS: Record<string, string> = {
  queued: "text-slate-400",
  running: "text-amber-300",
  done: "text-emerald-400",
  error: "text-red-400",
  cancelled: "text-slate-500",
};

function isLiveStatus(status: string) {
  return status === "running" || status === "queued";
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [activeList, setActiveList] = useState<JobSummary[]>([]);
  const { data: sys } = useSystemStatus({ pollMs: 10_000 });
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [workers, setWorkers] = useState(0);
  const [busyAction, setBusyAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const { progress, connected } = useJobProgress(activeJobId);
  const { submit, submitting, error: submitError, setError: setSubmitError } = useJobSubmit();

  const urlTask = searchParams.get("task");
  const urlModel = searchParams.get("model");
  const urlPreset = (searchParams.get("preset") as TaskPresetId) || "recommended";

  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(urlTask);
  const [taskPresets, setTaskPresets] = useState<Record<string, TaskPresetId>>({});
  const [taskParams, setTaskParams] = useState<Record<string, Record<string, unknown>>>({});
  const scrolledRef = useRef(false);

  const hasActive = activeList.length > 0;

  const refresh = useCallback(async () => {
    try {
      const [data, active] = await Promise.all([
        apiGet<JobListResponse>("/jobs"),
        apiGet<ActiveSummary>("/jobs/active/summary"),
      ]);
      setJobs(data.jobs);
      setActiveList(active.active);
      const running = active.active[0] ?? data.jobs.find((j) => isLiveStatus(j.status));
      if (running) {
        setActiveJobId((prev) => prev ?? running.job_id);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const ms = hasActive ? 2000 : 5000;
    const id = window.setInterval(() => void refresh(), ms);
    return () => clearInterval(id);
  }, [refresh, hasActive]);

  useEffect(() => {
    const watch = searchParams.get("watch");
    if (watch) {
      setActiveJobId(watch);
      const next = new URLSearchParams(searchParams);
      next.delete("watch");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (urlTask) {
      setExpandedTaskId(urlTask);
      setTaskPresets((p) => ({ ...p, [urlTask]: urlPreset }));
    }
  }, [urlTask, urlPreset]);

  useEffect(() => {
    if (!expandedTaskId || scrolledRef.current) return;
    const el = document.getElementById(`task-${expandedTaskId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      scrolledRef.current = true;
    }
  }, [expandedTaskId, sys]);

  useEffect(() => {
    if (!activeJobId) {
      setJobDetail(null);
      return;
    }
    const load = async () => {
      try {
        const d = await apiGet<JobDetail>(`/jobs/${activeJobId}`);
        setJobDetail(d);
      } catch {
        /* ignore */
      }
    };
    void load();
    const id = window.setInterval(() => void load(), 1500);
    return () => clearInterval(id);
  }, [activeJobId, progress?.status, progress?.pct]);

  const terminalStatus = progress?.status ?? jobDetail?.status;
  useEffect(() => {
    if (terminalStatus === "done") invalidateSystemStatus();
  }, [terminalStatus]);

  const activeJob = jobs.find((j) => j.job_id === activeJobId) ?? jobDetail;
  const activeStatus = progress?.status ?? activeJob?.status ?? jobDetail?.status;
  const isActive = isLiveStatus(activeStatus ?? "");
  const displayProgress = mergeJobProgress(progress, jobDetail);
  const friendly = displayProgress?.friendly ?? jobDetail?.friendly ?? null;
  const technical = displayProgress?.result ?? jobDetail?.result ?? null;

  const quickTaskByType = useMemo(() => {
    const m = new Map<string, (typeof ALL_TASK_CARDS)[number]>();
    for (const t of ALL_TASK_CARDS) m.set(t.id, t);
    return m;
  }, []);

  const completedJobTypes = useMemo(() => {
    const s = new Set<string>();
    for (const j of jobs) {
      if (j.status === "done") s.add(j.type);
    }
    return s;
  }, [jobs]);

  function openConfigure(taskId: string, preset: TaskPresetId = "recommended") {
    setExpandedTaskId(taskId);
    setTaskPresets((p) => ({ ...p, [taskId]: preset }));
    const next = new URLSearchParams(searchParams);
    next.set("task", taskId);
    next.set("preset", preset);
    if (urlModel) next.set("model", urlModel);
    setSearchParams(next, { replace: true });
  }

  function closeConfigure() {
    setExpandedTaskId(null);
    const next = new URLSearchParams(searchParams);
    next.delete("task");
    next.delete("preset");
    next.delete("model");
    setSearchParams(next, { replace: true });
  }

  async function startTask(type: string, params: Record<string, unknown>) {
    setError(null);
    setSubmitError(null);
    closeConfigure();
    const jobId = await submit(type, params, workers);
    if (jobId) {
      setActiveJobId(jobId);
      invalidateSystemStatus();
      await refresh();
    }
  }

  async function stopJob(jobId: string) {
    setBusyAction(true);
    setError(null);
    try {
      await apiPost(`/jobs/${jobId}/cancel`, {});
      setActiveJobId(jobId);
      invalidateSystemStatus();
      await refresh();
    } catch (e) {
      setError(
        (e instanceof Error ? e.message : String(e)) +
          " — try Release all tasks, or wait until the current training epoch finishes.",
      );
    } finally {
      setBusyAction(false);
    }
  }

  async function releaseAll() {
    setBusyAction(true);
    setError(null);
    try {
      await apiPost<{ count: number }>("/jobs/cancel-all", {});
      setActiveJobId(null);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyAction(false);
    }
  }

  return (
    <div className="space-y-6">
      <ApiOfflineBanner suppressWhenBusy={hasActive} />
      <PageIntro
        title="Background tasks"
        description="Click Configure on a task card to set workers, device, and epochs right on that card. Quick start uses the small test preset."
      />

      {hasActive && (
        <section className="rounded-xl border-2 border-amber-700/50 bg-amber-950/25 p-4 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-base font-semibold text-amber-100">
              Active now ({activeList.length})
            </h3>
            <button
              type="button"
              disabled={busyAction}
              onClick={() => void releaseAll()}
              className="ml-auto px-4 py-2 rounded-md bg-red-900/60 border border-red-600 text-red-100 text-sm font-medium hover:bg-red-900 disabled:opacity-50"
            >
              {busyAction ? "Releasing…" : "Release all tasks"}
            </button>
          </div>
          <ul className="space-y-2">
            {activeList.map((j) => (
              <li
                key={j.job_id}
                className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-900/40 bg-slate-950/40 px-3 py-2"
              >
                <span className="font-medium text-slate-100">{jobTypeLabel(j.type)}</span>
                <span className="text-xs text-amber-300">{jobStatusLabel(j.status)}</span>
                <span className="text-xs text-slate-500 truncate flex-1 min-w-[12rem]">
                  {j.progress?.msg ?? "—"}
                </span>
                <button
                  type="button"
                  disabled={busyAction}
                  onClick={() => void stopJob(j.job_id)}
                  className="text-sm px-3 py-1 rounded-md border border-amber-600 text-amber-200 hover:bg-amber-950/60 disabled:opacity-50"
                >
                  Stop
                </button>
                <button
                  type="button"
                  className="text-xs text-emerald-400 hover:underline"
                  onClick={() => setActiveJobId(j.job_id)}
                >
                  View progress
                </button>
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-500 leading-relaxed">
            <strong className="text-slate-400 font-normal">Stop</strong> cancels the task; GPU
            training exits after the current <em>epoch</em> (may take 1–3 min, RAM drops then).{" "}
            <strong className="text-slate-400 font-normal">Release all</strong> opens the queue
            immediately. If Task Manager still shows ~10 GB Python, wait or end that process on
            the Details tab.
          </p>
        </section>
      )}

      <p className="text-sm text-slate-400">
        <Link to="/import" className="text-emerald-400 hover:underline">
          Import hands
        </Link>{" "}
        ·{" "}
        <Link to="/status" className="text-emerald-400 hover:underline">
          System status
        </Link>
      </p>

      {(error || submitError) && (
        <p className="text-sm text-red-400 border border-red-900/50 rounded-md px-3 py-2">
          {error ?? submitError}
        </p>
      )}

      <AiPipelineGuide completedJobTypes={completedJobTypes} />

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-slate-300">Pipeline tasks (Setup order)</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {CORE_TASK_CARDS.map((j) => (
            <TaskPipelineCard
              key={j.id}
              task={j}
              sys={sys}
              expanded={expandedTaskId === j.id}
              onExpand={() => openConfigure(j.id, "recommended")}
              onCollapse={closeConfigure}
              hasActiveJob={hasActive}
              submitting={submitting}
              submitError={submitError}
              workers={workers}
              onWorkers={setWorkers}
              onQuickStart={(p) => void startTask(j.id, p)}
              onStart={(p) => void startTask(j.id, p)}
              modelName={
                urlModel && getTaskById(j.id)?.produces.includes(urlModel) ? urlModel : undefined
              }
              presetId={taskPresets[j.id] ?? "recommended"}
              onPresetId={(id) => setTaskPresets((p) => ({ ...p, [j.id]: id }))}
              params={taskParams[j.id] ?? {}}
              onParams={(p) => setTaskParams((prev) => ({ ...prev, [j.id]: p }))}
            />
          ))}
        </div>
      </section>

      {EXTRA_TASK_CARDS.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-sm font-medium text-slate-300">More training</h3>
          <p className="text-xs text-slate-500">
            Extra tasks not in the Setup wizard — run when you need multi-way or specialized models.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {EXTRA_TASK_CARDS.map((j) => (
              <TaskPipelineCard
                key={j.id}
                task={j}
                sys={sys}
                expanded={expandedTaskId === j.id}
                onExpand={() => openConfigure(j.id, "recommended")}
                onCollapse={closeConfigure}
                hasActiveJob={hasActive}
                submitting={submitting}
                submitError={submitError}
                workers={workers}
                onWorkers={setWorkers}
                onQuickStart={(p) => void startTask(j.id, p)}
                onStart={(p) => void startTask(j.id, p)}
                modelName={
                  urlModel && getTaskById(j.id)?.produces.includes(urlModel) ? urlModel : undefined
                }
                presetId={taskPresets[j.id] ?? "recommended"}
                onPresetId={(id) => setTaskPresets((p) => ({ ...p, [j.id]: id }))}
                params={taskParams[j.id] ?? {}}
                onParams={(p) => setTaskParams((prev) => ({ ...prev, [j.id]: p }))}
              />
            ))}
          </div>
        </section>
      )}

      {activeJobId && (
        <section className="space-y-2 rounded-xl border-2 border-emerald-700/40 bg-slate-900/50 p-4">
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-sm font-medium text-slate-200">
              {jobTypeLabel(activeJob?.type ?? jobDetail?.type ?? "")}
            </h3>
            {connected && isActive && (
              <span className="text-xs text-emerald-500">Updating live</span>
            )}
            {isActive && (
              <button
                type="button"
                disabled={busyAction}
                onClick={() => void stopJob(activeJobId)}
                className="text-sm px-3 py-1 rounded-md border border-amber-600 text-amber-300 hover:bg-amber-950/50 ml-auto disabled:opacity-50"
              >
                {busyAction ? "Stopping…" : "Stop"}
              </button>
            )}
          </div>
          <JobProgressBar progress={displayProgress} startedAt={activeJob?.started_at} />
          {(progress?.status === "done" ||
            progress?.status === "error" ||
            progress?.status === "cancelled" ||
            jobDetail?.status === "done" ||
            jobDetail?.status === "error" ||
            jobDetail?.status === "cancelled") && (
            <JobResultCard
              friendly={friendly}
              jobType={activeJob?.type ?? jobDetail?.type ?? ""}
              technicalResult={technical}
              hasActiveJob={hasActive}
              onStartJob={startTask}
            />
          )}
        </section>
      )}

      <section>
        <h3 className="text-sm font-medium text-slate-300 mb-3">Recent tasks</h3>
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-900/80 text-slate-400">
              <tr>
                <th className="px-3 py-2">Task</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Latest message</th>
                <th className="px-3 py-2">When</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-slate-500 text-center">
                    No tasks yet.
                  </td>
                </tr>
              )}
              {jobs.map((j) => {
                const quick = quickTaskByType.get(j.type);
                const live = isLiveStatus(j.status);
                return (
                  <tr key={j.job_id} className="border-t border-slate-800 hover:bg-slate-900/40">
                    <td className="px-3 py-2 text-slate-200">{jobTypeLabel(j.type)}</td>
                    <td className={`px-3 py-2 ${STATUS_CLASS[j.status] ?? ""}`}>
                      {jobStatusLabel(j.status)}
                    </td>
                    <td className="px-3 py-2 text-slate-400 truncate max-w-xs">
                      {j.progress?.msg ?? j.error ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-xs">
                      {j.created_at ? new Date(j.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-2 space-x-2 whitespace-nowrap">
                      <button
                        type="button"
                        className="text-xs text-emerald-400 hover:underline"
                        onClick={() => setActiveJobId(j.job_id)}
                      >
                        View
                      </button>
                      {live ? (
                        <button
                          type="button"
                          disabled={busyAction}
                          className="text-xs text-amber-400 hover:underline disabled:opacity-50"
                          onClick={() => void stopJob(j.job_id)}
                        >
                          Stop
                        </button>
                      ) : quick ? (
                        <button
                          type="button"
                          disabled={submitting || hasActive}
                          className="text-xs text-emerald-400 hover:underline disabled:opacity-50"
                          onClick={() => openConfigure(j.type, "recommended")}
                        >
                          Configure
                        </button>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
