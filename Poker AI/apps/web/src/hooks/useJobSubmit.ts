import { useCallback, useState } from "react";
import { apiPost } from "../api/client";
import { taskUsesCpuWorkers } from "../lib/pipelineTasks";

export function useJobSubmit() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (
      type: string,
      params: Record<string, unknown>,
      workers: number,
    ): Promise<string | null> => {
      setSubmitting(true);
      setError(null);
      try {
        const body: Record<string, unknown> = { ...params };
        if (workers > 0 && taskUsesCpuWorkers(type)) {
          body.workers = workers;
        }
        const { job_id } = await apiPost<{ job_id: string }>("/jobs", { type, params: body });
        return job_id;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  return { submit, submitting, error, setError };
}
