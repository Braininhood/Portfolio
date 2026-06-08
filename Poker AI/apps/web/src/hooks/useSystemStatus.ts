/**
 * useSystemStatus — fetches GET /status (hardware, models, DB, jobs).
 * Polls faster while jobs run; refreshes on tab focus and after job completion.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet } from "../api/client";
import { STATUS_INVALIDATE_EVENT } from "../lib/statusEvents";

export type CpuInfo = {
  name: string;
  physical_cores: number;
  logical_cores: number;
  arch: string;
};

export type GpuInfo = {
  name: string;
  vram_gb: number;
  driver_version: string;
  cuda_version: string | null;
  cuda_available: boolean;
};

export type RamInfo = {
  total_gb: number;
  available_gb: number;
};

export type DiskInfo = {
  free_gb: number;
  total_gb: number;
  path: string;
};

export type WorkerInfo = {
  recommended: number;
  max_safe: number;
  current_env: number;
  warning: string | null;
  explanation: string;
  by_task: Record<string, number>;
};

export type ModelStatus = {
  name: string;
  ready: boolean;
  path: string | null;
  trained_at: string | null;
  note: string | null;
  job_type: string | null;
  why: string | null;
};

export type TexasSolverStatus = {
  found: boolean;
  exe_path: string | null;
  version: string | null;
  note: string | null;
};

export type SystemStatus = {
  version: string;
  os_name: string;
  os_platform: string;
  cpu: CpuInfo;
  gpu: GpuInfo | null;
  ram: RamInfo;
  disk: DiskInfo;
  workers: WorkerInfo;
  db_hands: number | null;
  db_revision: string | null;
  models: ModelStatus[];
  texas_solver: TexasSolverStatus;
  jobs_running: number;
  jobs_queued: number;
};

export type LoadStatus = "idle" | "loading" | "done" | "error";

interface Options {
  /** Base poll interval when idle (ms). Default 8000. */
  pollMs?: number;
  skip?: boolean;
}

interface Return {
  status: LoadStatus;
  data: SystemStatus | null;
  error: string | null;
  lastUpdated: Date | null;
  recheck: () => void;
}

export function useSystemStatus(opts?: Options): Return {
  const basePollMs = opts?.pollMs ?? 8000;
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [data, setData] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [tick, setTick] = useState(0);
  const prevJobsActive = useRef(false);

  const recheck = useCallback(() => {
    setTick((n) => n + 1);
  }, []);

  useEffect(() => {
    if (opts?.skip) return;

    const onInvalidate = () => recheck();
    const onVisible = () => {
      if (document.visibilityState === "visible") recheck();
    };

    window.addEventListener(STATUS_INVALIDATE_EVENT, onInvalidate);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.removeEventListener(STATUS_INVALIDATE_EVENT, onInvalidate);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [opts?.skip, recheck]);

  useEffect(() => {
    if (opts?.skip) return;

    let cancelled = false;
    let followUpId: ReturnType<typeof setTimeout> | undefined;

    const load = async () => {
      setStatus((s) => (s === "done" ? "done" : "loading"));
      setError(null);
      try {
        const res = await apiGet<SystemStatus>("/status");
        if (!cancelled) {
          const jobsActive = (res.jobs_running ?? 0) + (res.jobs_queued ?? 0) > 0;
          if (prevJobsActive.current && !jobsActive) {
            // Job just finished — re-check after artifacts are flushed to disk
            followUpId = setTimeout(() => {
              if (!cancelled) void load();
            }, 1500);
          }
          prevJobsActive.current = jobsActive;

          setData(res);
          setLastUpdated(new Date());
          setStatus("done");
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setStatus("error");
        }
      }
    };

    void load();

    const jobsActive =
      (data?.jobs_running ?? 0) + (data?.jobs_queued ?? 0) > 0;
    const intervalMs = jobsActive ? 2000 : basePollMs;

    const id = window.setInterval(() => void load(), intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
      if (followUpId) clearTimeout(followUpId);
    };
  }, [opts?.skip, basePollMs, tick, data?.jobs_running, data?.jobs_queued]);

  return { status, data, error, lastUpdated, recheck };
}
