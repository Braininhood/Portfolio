import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiPost } from "../api/client";
import JobResultInsights from "./JobResultInsights";

export type JobNextStep = {
  label: string;
  path: string;
  hint?: string | null;
  action?: string | null;
  job_type?: string | null;
  job_params?: Record<string, unknown>;
};

export type JobFriendlySummary = {
  headline: string;
  explanation: string;
  advice: string[];
  next_steps: JobNextStep[];
  severity: string;
};

type Props = {
  friendly: JobFriendlySummary | null | undefined;
  jobType?: string;
  technicalResult?: Record<string, unknown> | null;
  /** When set, job-start buttons use this (e.g. Jobs page submit). */
  onStartJob?: (type: string, params: Record<string, unknown>) => Promise<void>;
  hasActiveJob?: boolean;
};

export default function JobResultCard({
  friendly,
  jobType,
  technicalResult,
  onStartJob,
  hasActiveJob = false,
}: Props) {
  const navigate = useNavigate();
  const [starting, setStarting] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  if (!friendly) return null;

  const border =
    friendly.severity === "error"
      ? "border-red-800/60 bg-red-950/20"
      : friendly.severity === "success"
        ? "border-emerald-800/50 bg-emerald-950/20"
        : "border-slate-700 bg-slate-900/60";

  async function runStep(step: JobNextStep) {
    if (step.action !== "start_job" || !step.job_type) {
      void navigate(step.path);
      return;
    }
    if (hasActiveJob) {
      setStartError("Another task is still running. Open Tasks → Release all, then try again.");
      void navigate("/jobs");
      return;
    }
    const key = `${step.job_type}:${step.label}`;
    setStarting(key);
    setStartError(null);
    try {
      const params = step.job_params ?? {};
      if (onStartJob) {
        await onStartJob(step.job_type, params);
      } else {
        const { job_id } = await apiPost<{ job_id: string }>("/jobs", {
          type: step.job_type,
          params,
        });
        void navigate(`/jobs?watch=${job_id}`);
      }
    } catch (e) {
      setStartError(e instanceof Error ? e.message : String(e));
    } finally {
      setStarting(null);
    }
  }

  return (
    <div className={`rounded-lg border p-4 mt-3 ${border}`}>
      <h4 className="text-base font-semibold text-slate-100">{friendly.headline}</h4>
      <p className="text-sm text-slate-300 mt-2 leading-relaxed">{friendly.explanation}</p>

      {startError && (
        <p className="mt-3 text-sm text-red-400 border border-red-900/50 rounded px-2 py-1">
          {startError}
        </p>
      )}

      {friendly.next_steps.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {friendly.next_steps.map((s) => {
            const isStart = s.action === "start_job" && s.job_type;
            const key = `${s.path}:${s.label}`;
            const busy = starting === `${s.job_type}:${s.label}`;

            if (isStart) {
              return (
                <button
                  key={key}
                  type="button"
                  disabled={!!starting || hasActiveJob}
                  title={s.hint ?? undefined}
                  onClick={() => void runStep(s)}
                  className="inline-flex items-center px-3 py-1.5 text-sm rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-500 disabled:opacity-50"
                >
                  {busy ? "Starting…" : s.label}
                </button>
              );
            }

            return (
              <Link
                key={key}
                to={s.path}
                className="inline-flex items-center px-3 py-1.5 text-sm rounded-md bg-emerald-800/50 text-emerald-100 hover:bg-emerald-700/60"
                title={s.hint ?? undefined}
              >
                {s.label}
              </Link>
            );
          })}
        </div>
      )}

      {jobType && (
        <JobResultInsights
          jobType={jobType}
          result={technicalResult ?? {}}
          apiAdvice={friendly.advice}
        />
      )}
    </div>
  );
}
