import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../api/client";
import { Card } from "./Card";

type Snapshot = {
  version: string;
  num_hands: number;
  num_features: number;
  content_hash: string;
  features_path: string;
  created_at: string;
  is_active: boolean;
};

type SnapshotsResponse = {
  snapshots: Snapshot[];
  active_version: string | null;
};

export default function DatasetSnapshotsPanel() {
  const qc = useQueryClient();
  const { data, error, isLoading } = useQuery({
    queryKey: ["dataset-snapshots"],
    queryFn: () => apiGet<SnapshotsResponse>("/setup/snapshots"),
    retry: false,
  });

  const setActive = useMutation({
    mutationFn: (version: string) =>
      apiPost<Snapshot>("/setup/snapshots/active", { version }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["dataset-snapshots"] }),
  });

  return (
    <Card title="Dataset snapshots">
      <p className="text-slate-400 text-sm mb-3 leading-relaxed">
        Each time you run <strong className="font-normal text-slate-200">Prepare hands for AI</strong>,
        a dated snapshot is saved under{" "}
        <code className="text-slate-500 text-xs">data/processed/v&lt;date&gt;/</code>. Pick which
        snapshot training jobs should prefer (reproducible runs).
      </p>
      {isLoading && <p className="text-slate-500 text-sm">Loading snapshots…</p>}
      {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}
      {data && data.snapshots.length === 0 && (
        <p className="text-slate-500 text-sm">
          No snapshots yet. Run Prepare hands for AI in the steps above.
        </p>
      )}
      {data && data.snapshots.length > 0 && (
        <ul className="divide-y divide-slate-800 border border-slate-700 rounded-md text-sm">
          {data.snapshots.map((s) => (
            <li key={s.version} className="px-4 py-2 flex flex-wrap items-center gap-2">
              <span className="font-mono text-emerald-300/90">v{s.version}</span>
              <span className="text-slate-400">
                {s.num_hands.toLocaleString()} hands · hash {s.content_hash}
              </span>
              {s.is_active && (
                <span className="text-xs text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded">
                  Active for training
                </span>
              )}
              {!s.is_active && (
                <button
                  type="button"
                  disabled={setActive.isPending}
                  onClick={() => setActive.mutate(s.version)}
                  className="ml-auto text-xs px-2 py-1 rounded border border-slate-600 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                >
                  Use for training
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
