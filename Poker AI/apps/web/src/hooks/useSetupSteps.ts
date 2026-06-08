import { useCallback, useEffect, useState } from "react";
import { apiGet } from "../api/client";

export type SetupStep = {
  id: string;
  title: string;
  description: string;
  ready: boolean;
  detail: string;
  requires: string[];
  optional: boolean;
  optional_note?: string | null;
  job_type: string | null;
  texas_solver_found?: boolean | null;
  can_run: boolean;
};

export type SetupStepsResponse = {
  steps: SetupStep[];
  ready_count: number;
  pending_count: number;
};

export function useSetupSteps(pollMs = 8000) {
  const [data, setData] = useState<SetupStepsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await apiGet<SetupStepsResponse>("/setup/steps");
      setData(res);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { data, error, refresh };
}
