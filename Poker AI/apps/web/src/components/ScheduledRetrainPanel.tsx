import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { Card } from "./Card";

type ScheduleEntry = {
  job_type: string;
  label: string;
  enabled: boolean;
  time_local: string;
  frequency: string;
  day_of_week: string | null;
  os_installed: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
};

type ScheduleList = {
  platform: string;
  scheduler_available: boolean;
  nightly_enabled: boolean;
  nightly_start_time: string;
  entries: ScheduleEntry[];
  last_nightly_run_at: string | null;
  message: string | null;
};

function formatWhen(e: ScheduleEntry): string {
  const freq = e.frequency === "weekly" ? `weekly ${e.day_of_week ?? "SUN"}` : "nightly";
  return `${freq} ${e.time_local}`;
}

function formatLastRun(at: string | null, status: string | null): string {
  if (!at) return "Never";
  const d = new Date(at.includes("T") ? at : `${at.replace(" ", "T")}Z`);
  const when = Number.isNaN(d.getTime()) ? at : d.toLocaleString();
  if (status === "error") return `${when} (failed)`;
  return when;
}

export default function ScheduledRetrainPanel() {
  const qc = useQueryClient();
  const [startTime, setStartTime] = useState("00:00");

  const { data, error, isLoading } = useQuery({
    queryKey: ["job-schedule"],
    queryFn: () => apiGet<ScheduleList>("/jobs/schedule"),
    retry: false,
  });

  const nightly = useMutation({
    mutationFn: (enabled: boolean) =>
      apiPost<{ entries: ScheduleEntry[]; message: string | null }>("/jobs/schedule/nightly", {
        enabled,
        start_time: startTime,
      }),
    onSuccess: (res) => {
      void qc.invalidateQueries({ queryKey: ["job-schedule"] });
      if (res.message) {
        /* surfaced below via refetch */
      }
    },
  });

  const toggleEntry = useMutation({
    mutationFn: (entry: ScheduleEntry) =>
      apiPost<{ entries: ScheduleEntry[] }>("/jobs/schedule", {
        job_type: entry.job_type,
        enabled: !entry.enabled,
        time_local: entry.time_local,
        frequency: entry.frequency,
        day_of_week: entry.day_of_week,
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["job-schedule"] }),
  });

  const nightlyOn = data?.nightly_enabled ?? false;
  const busy = nightly.isPending || toggleEntry.isPending;

  useEffect(() => {
    if (data?.nightly_start_time) {
      setStartTime(data.nightly_start_time);
    }
  }, [data?.nightly_start_time]);

  return (
    <Card title="Scheduled retraining">
      <p className="text-slate-400 text-sm mb-4 leading-relaxed">
        Automatically refresh models overnight using Windows Task Scheduler (or cron on
        Linux/macOS). Tasks run the same CLI commands as the Setup wizard — your PC must be on at
        the scheduled time. GPU jobs (HHFormer, league) can take hours.
      </p>

      {isLoading && <p className="text-slate-500 text-sm">Loading schedule…</p>}
      {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}

      {data && (
        <>
          {data.message && (
            <p className="text-amber-200/90 text-sm mb-3 rounded border border-amber-800/50 bg-amber-950/30 px-3 py-2">
              {data.message}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-4 mb-4">
            <label className="flex items-center gap-2 text-sm text-slate-200">
              <span>Nightly retrain</span>
              <button
                type="button"
                disabled={busy}
                role="switch"
                aria-checked={nightlyOn}
                onClick={() => nightly.mutate(!nightlyOn)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  nightlyOn ? "bg-emerald-600" : "bg-slate-600"
                } disabled:opacity-50`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    nightlyOn ? "translate-x-5" : ""
                  }`}
                />
              </button>
              <span className="text-slate-400">{nightlyOn ? "On" : "Off"}</span>
            </label>

            <label className="flex items-center gap-2 text-sm text-slate-300">
              First job at
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="px-2 py-1 rounded bg-slate-900 border border-slate-600 text-sm"
              />
              <span className="text-slate-500 text-xs">local time</span>
            </label>

            {startTime !== data.nightly_start_time && (
              <button
                type="button"
                disabled={busy || !nightlyOn}
                onClick={() => nightly.mutate(true)}
                className="text-xs px-2 py-1 rounded border border-slate-600 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
              >
                Apply new start time
              </button>
            )}
          </div>

          {data.last_nightly_run_at && (
            <p className="text-xs text-slate-500 mb-3">
              Last pipeline job finished:{" "}
              {formatLastRun(data.last_nightly_run_at, "done")}
            </p>
          )}

          <ul className="divide-y divide-slate-800 border border-slate-700 rounded-md text-sm">
            {data.entries.map((e) => (
              <li key={e.job_type} className="px-4 py-2 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => toggleEntry.mutate(e)}
                  className={`text-left flex-1 min-w-[12rem] hover:text-emerald-300 ${
                    e.enabled ? "text-slate-100" : "text-slate-500"
                  }`}
                >
                  {e.enabled ? "✓" : "○"} {e.label}
                </button>
                <span className="text-slate-500 text-xs">{formatWhen(e)}</span>
                {e.enabled && (
                  <span
                    className={`text-xs ${e.os_installed ? "text-emerald-500" : "text-amber-500"}`}
                    title={e.os_installed ? "OS task installed" : "Saved but OS task missing"}
                  >
                    {e.os_installed ? "scheduled" : "pending install"}
                  </span>
                )}
                <span className="text-xs text-slate-600 w-full sm:w-auto">
                  Last: {formatLastRun(e.last_run_at, e.last_run_status)}
                </span>
              </li>
            ))}
          </ul>

          {nightly.isSuccess && nightly.data?.message && (
            <p className="text-emerald-400/90 text-xs mt-3">{nightly.data.message}</p>
          )}

          <p className="text-xs text-slate-600 mt-3">
            Platform: {data.platform}
            {data.scheduler_available ? " · scheduler ready" : " · manual install may be needed"}
            {" · "}
            Logs: <code className="text-slate-500">poker_ai/data/schedule/logs/</code>
          </p>
        </>
      )}
    </Card>
  );
}
