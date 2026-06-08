import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { invalidateSystemStatus } from "../lib/statusEvents";
import type { ModelStatus, SystemStatus } from "../hooks/useSystemStatus";
import { useJobSubmit } from "../hooks/useJobSubmit";
import {
  getTaskForModel,
  mergeTaskParams,
  type PipelineTaskDef,
  type TaskPresetId,
} from "../lib/pipelineTasks";
import { getParamGuide } from "../lib/paramGuides";
import { buildTaskJobsUrl, getPrerequisiteRedirect } from "../lib/taskNavigation";
import WorkerControl from "./WorkerControl";

type Props = {
  model: ModelStatus;
  status: SystemStatus;
  hasActiveJob: boolean;
  onStarted?: (jobId: string) => void;
  defaultOpen?: boolean;
};

export default function ModelTaskActions({
  model,
  status,
  hasActiveJob,
  onStarted,
  defaultOpen = false,
}: Props) {
  const navigate = useNavigate();
  const task = getTaskForModel(model.name, model.job_type);
  const [open, setOpen] = useState(defaultOpen);
  const [presetId, setPresetId] = useState<TaskPresetId>("recommended");
  const [params, setParams] = useState<Record<string, unknown>>({});
  const [workers, setWorkers] = useState(0);
  const { submit, submitting, error } = useJobSubmit();

  const preset = task?.presets.find((p) => p.id === presetId) ?? task?.presets[0];

  const mergedParams = useMemo(() => {
    if (!task || !preset) return {};
    return mergeTaskParams(task, preset, status, params, model.name);
  }, [task, preset, status, params, model.name]);

  const prereqs = task?.prerequisites?.(status) ?? [];

  if (!task) {
    return (
      <p className="text-xs text-slate-500 mt-1">
        {model.why ?? model.note ?? "No automated task linked."}
      </p>
    );
  }

  async function handleStart() {
    if (!preset || hasActiveJob) return;
    const jobId = await submit(task!.id, mergedParams, workers);
    if (jobId) {
      invalidateSystemStatus();
      onStarted?.(jobId);
      void navigate(`/jobs?watch=${jobId}`);
    }
  }

  return (
    <div className="mt-2 space-y-2">
      <p className="text-xs text-slate-500 leading-relaxed">{model.why ?? task.why}</p>

      {!open ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setOpen(true);
              setPresetId("quick");
            }}
            className="text-xs px-3 py-1.5 rounded-md border border-slate-600 text-emerald-300 hover:bg-slate-800"
          >
            Quick test…
          </button>
          <button
            type="button"
            onClick={() => {
              setOpen(true);
              setPresetId("recommended");
            }}
            className="text-xs px-3 py-1.5 rounded-md bg-emerald-800/50 border border-emerald-700 text-emerald-100 hover:bg-emerald-800"
          >
            Configure & run
          </button>
          <Link
            to={buildTaskJobsUrl(task.id, {
              status,
              model: model.name,
              preset: "recommended",
            })}
            className="text-xs px-3 py-1.5 rounded-md text-slate-400 hover:text-slate-200"
          >
            Open on Tasks →
          </Link>
        </div>
      ) : (
        <TaskConfigForm
          task={task}
          modelName={model.name}
          status={status}
          presetId={presetId}
          onPresetId={setPresetId}
          params={params}
          onParams={setParams}
          mergedParams={mergedParams}
          workers={workers}
          onWorkers={setWorkers}
          prereqs={prereqs}
          hasActiveJob={hasActiveJob}
          submitting={submitting}
          error={error}
          onStart={() => void handleStart()}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

/** Shared configure form — used on Status and Jobs pages. */
export function TaskConfigForm({
  task,
  modelName,
  status,
  presetId,
  onPresetId,
  params,
  onParams,
  mergedParams,
  workers,
  onWorkers,
  prereqs,
  hasActiveJob,
  submitting,
  error,
  onStart,
  onClose,
}: {
  task: PipelineTaskDef;
  modelName?: string;
  status: SystemStatus;
  presetId: TaskPresetId;
  onPresetId: (id: TaskPresetId) => void;
  params: Record<string, unknown>;
  onParams: (p: Record<string, unknown>) => void;
  mergedParams: Record<string, unknown>;
  workers: number;
  onWorkers: (n: number) => void;
  prereqs: string[];
  hasActiveJob: boolean;
  submitting: boolean;
  error: string | null;
  onStart: () => void;
  onClose?: () => void;
}) {
  const preset = task.presets.find((p) => p.id === presetId) ?? task.presets[0];
  const taskHint = task.usesCpuWorkers ? task.id : undefined;
  const prereqRedirect = status ? getPrerequisiteRedirect(task.id, status) : null;

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-950/60 p-3 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-300">{task.label}</span>
        {onClose && (
          <button type="button" onClick={onClose} className="text-xs text-slate-500 hover:text-slate-300">
            Close
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {task.presets.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => {
              onPresetId(p.id);
              onParams({});
            }}
            className={`text-xs px-2.5 py-1 rounded-md border ${
              presetId === p.id
                ? "border-emerald-600 bg-emerald-900/40 text-emerald-100"
                : "border-slate-600 text-slate-400 hover:border-slate-500"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {preset && <p className="text-xs text-slate-500 italic">{preset.hint}</p>}

      {prereqs.length > 0 && (
        <ul className="text-xs text-amber-200/90 list-disc list-inside space-y-0.5">
          {prereqs.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      )}

      {prereqs.length > 0 && prereqRedirect && (
        <Link
          to={
            prereqRedirect.kind === "task"
              ? buildTaskJobsUrl(prereqRedirect.taskId, {
                  preset: prereqRedirect.preset,
                  status,
                  forceTask: true,
                })
              : prereqRedirect.path
          }
          className="inline-flex text-xs px-3 py-1.5 rounded-md bg-amber-900/40 border border-amber-700 text-amber-100 hover:bg-amber-900/60"
        >
          {prereqRedirect.label} →
        </Link>
      )}

      {task.fields.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {task.fields.map((f) => {
            const guide = getParamGuide(task.id, f.key);
            return (
            <div key={f.key} className="block text-xs space-y-1">
              <label className="block">
              <span className="text-slate-400">{f.label}</span>
              {f.type === "select" ? (
                <select
                  className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-slate-200 text-sm"
                  value={String(params[f.key] ?? mergedParams[f.key] ?? "")}
                  onChange={(e) => onParams({ ...params, [f.key]: e.target.value })}
                >
                  {f.options?.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="number"
                  className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-slate-200 text-sm"
                  min={f.min}
                  step={f.step}
                  placeholder={
                    mergedParams[f.key] != null ? String(mergedParams[f.key]) : undefined
                  }
                  value={params[f.key] != null ? String(params[f.key]) : ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    onParams({
                      ...params,
                      [f.key]: v === "" ? undefined : Number(v),
                    });
                  }}
                />
              )}
            </label>
              {guide && (
                <div className="rounded border border-slate-700/80 bg-slate-900/50 px-2 py-1.5 space-y-0.5 text-[11px] leading-relaxed">
                  <p className="text-slate-500">{guide.what}</p>
                  <p>
                    <span className="text-emerald-500/90">Good: </span>
                    <span className="text-slate-400">{guide.good}</span>
                  </p>
                  <p>
                    <span className="text-amber-500/90">If you need better: </span>
                    <span className="text-slate-400">{guide.improve}</span>
                  </p>
                </div>
              )}
            </div>
          );
          })}
        </div>
      )}

      {task.usesCpuWorkers && (
        <WorkerControl
          value={workers}
          onChange={onWorkers}
          workers={status.workers}
          taskHint={taskHint}
          disabled={hasActiveJob || submitting}
          note={
            task.id === "solve_preflop"
              ? "Windows: parallel runs in a separate process (same as CLI). Pick 8–10 CPU workers. Progress updates every ~1s."
              : status.workers.by_task[task.id] != null
                ? `This PC: ≈ ${status.workers.by_task[task.id]} workers recommended for ${task.id}.`
                : undefined
          }
        />
      )}

      {!task.usesCpuWorkers && status.gpu?.cuda_available && (
        <p className="text-xs text-slate-500">
          GPU training uses PyTorch DataLoader — device is set above; parallel CPU workers do not
          apply to this task.
        </p>
      )}

      {task.id === "solve_grid" &&
        String(mergedParams.backend) === "texas" &&
        !status.texas_solver.found && (
          <p className="text-xs text-amber-200/90">
            TexasSolver is not installed — switch backend to Mock for a quick test, or install via
            System health.
          </p>
        )}

      {modelName && (
        <p className="text-xs text-slate-600 font-mono truncate" title={JSON.stringify(mergedParams)}>
          Target: {modelName}
        </p>
      )}

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        type="button"
        disabled={hasActiveJob || submitting || prereqs.length > 0}
        onClick={onStart}
        className="w-full sm:w-auto text-sm px-4 py-2 rounded-md bg-emerald-700 hover:bg-emerald-600 text-white font-medium disabled:opacity-50"
      >
        {hasActiveJob
          ? "Release active task on Tasks page first"
          : submitting
            ? "Starting…"
            : `Start ${task.label}`}
      </button>
    </div>
  );
}
