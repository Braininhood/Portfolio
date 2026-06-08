import { TaskConfigForm } from "./ModelTaskActions";
import type { SystemStatus } from "../hooks/useSystemStatus";
import type { PipelineTaskDef, TaskPresetId } from "../lib/pipelineTasks";
import { mergeTaskParams } from "../lib/pipelineTasks";

type Props = {
  task: PipelineTaskDef;
  sys: SystemStatus | null;
  expanded: boolean;
  onExpand: () => void;
  onCollapse: () => void;
  hasActiveJob: boolean;
  submitting: boolean;
  submitError: string | null;
  workers: number;
  onWorkers: (n: number) => void;
  onQuickStart: (params: Record<string, unknown>) => void;
  onStart: (params: Record<string, unknown>) => void;
  modelName?: string;
  presetId: TaskPresetId;
  onPresetId: (id: TaskPresetId) => void;
  params: Record<string, unknown>;
  onParams: (p: Record<string, unknown>) => void;
};

export default function TaskPipelineCard({
  task,
  sys,
  expanded,
  onExpand,
  onCollapse,
  hasActiveJob,
  submitting,
  submitError,
  workers,
  onWorkers,
  onQuickStart,
  onStart,
  modelName,
  presetId,
  onPresetId,
  params,
  onParams,
}: Props) {
  const quick = task.presets.find((p) => p.id === "quick") ?? task.presets[0];
  const quickParams =
    sys && quick ? mergeTaskParams(task, quick, sys, {}, modelName) : quick?.params ?? {};

  const preset = task.presets.find((p) => p.id === presetId) ?? task.presets[0];
  const merged =
    sys && preset ? mergeTaskParams(task, preset, sys, params, modelName) : {};
  const prereqs = sys ? (task.prerequisites?.(sys) ?? []) : [];

  return (
    <div
      id={`task-${task.id}`}
      className={`flex flex-col rounded-lg border overflow-hidden transition-shadow ${
        expanded
          ? "border-emerald-600 ring-2 ring-emerald-700/40 bg-slate-900/70"
          : "border-slate-700 bg-slate-900/50"
      }`}
    >
      <div className="px-4 py-3 flex-1">
        <span className="text-xs text-emerald-500 font-medium">
          {task.step != null ? `Step ${task.step}` : "Extra"}
        </span>
        <span className="block font-medium text-slate-200">{task.label}</span>
        <span className="block text-xs text-slate-500 mt-1">{task.description}</span>
        <p className="text-xs text-slate-600 mt-1 italic">{task.why}</p>
      </div>

      {!expanded && (
        <div className="flex border-t border-slate-700">
          <button
            type="button"
            disabled={submitting || hasActiveJob}
            onClick={() => onQuickStart(quickParams)}
            className="flex-1 px-3 py-2.5 text-sm font-medium bg-emerald-900/30 text-emerald-100 hover:bg-emerald-800/40 disabled:opacity-50"
          >
            {hasActiveJob ? "Busy" : "Quick start"}
          </button>
          <button
            type="button"
            disabled={submitting || hasActiveJob}
            onClick={onExpand}
            className="flex-1 px-3 py-2.5 text-sm border-l border-slate-700 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            Configure…
          </button>
        </div>
      )}

      {expanded && sys && (
        <div className="border-t border-emerald-800/50 px-3 pb-3 pt-2 bg-slate-950/40">
          <TaskConfigForm
            task={task}
            modelName={modelName}
            status={sys}
            presetId={presetId}
            onPresetId={onPresetId}
            params={params}
            onParams={onParams}
            mergedParams={merged}
            workers={workers}
            onWorkers={onWorkers}
            prereqs={prereqs}
            hasActiveJob={hasActiveJob}
            submitting={submitting}
            error={submitError}
            onStart={() => onStart(merged)}
            onClose={onCollapse}
          />
        </div>
      )}
    </div>
  );
}
