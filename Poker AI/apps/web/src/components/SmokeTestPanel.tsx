import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import { Card } from "./Card";

type SmokeCheck = {
  name: string;
  passed: boolean;
  latency_ms: number;
  detail: string | null;
};

type SmokeResponse = {
  all_passed: boolean;
  checks: SmokeCheck[];
};

const LABELS: Record<string, string> = {
  db_readable: "Database readable",
  health_endpoint: "Health endpoint",
  replay_one_hand: "Replay first hand",
  decide_one_hand: "Decide (heuristic)",
  equity_spot: "Equity AA vs random",
  no_outbound_dns: "No outbound DNS",
  artifacts_present: "Artifacts readable",
};

export default function SmokeTestPanel() {
  const qc = useQueryClient();
  const [visible, setVisible] = useState(0);
  const run = useMutation({
    mutationFn: () => apiGet<SmokeResponse>("/health/smoke"),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: ["compliance"] });
      setVisible(0);
      const steps = data.checks.length;
      let i = 0;
      const tick = () => {
        i += 1;
        setVisible(i);
        if (i < steps) window.setTimeout(tick, 120);
      };
      tick();
    },
  });

  const checks = run.data?.checks ?? [];
  const showCount = run.isPending ? 0 : visible || (run.data ? checks.length : 0);

  return (
    <Card title="Air-gapped smoke test">
      <p className="text-xs text-slate-500 mb-3 -mt-1">
        Internal checklist only — no external network. All green is required before calling the
        install production-ready.
      </p>
      <button
        type="button"
        disabled={run.isPending}
        onClick={() => run.mutate()}
        className="rounded-lg bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 px-4 py-2 text-sm font-semibold text-white"
      >
        {run.isPending ? "Running…" : "Run smoke test"}
      </button>
      {run.error && (
        <p className="text-red-400 text-sm mt-3">{(run.error as Error).message}</p>
      )}
      {checks.length > 0 && (
        <ul className="mt-4 space-y-2" aria-live="polite">
          {checks.slice(0, showCount).map((c) => (
            <li
              key={c.name}
              className="flex items-start gap-3 text-sm rounded-md border border-slate-700/60 px-3 py-2"
            >
              <span
                className={`font-medium tabular-nums ${c.passed ? "text-emerald-400" : "text-red-400"}`}
              >
                {c.passed ? "✓" : "✗"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-slate-200">{LABELS[c.name] ?? c.name}</div>
                <div className="text-xs text-slate-500">
                  {c.latency_ms.toFixed(1)} ms
                  {c.detail ? ` · ${c.detail}` : ""}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      {run.data && showCount >= checks.length && (
        <p
          className={`mt-3 text-sm font-medium ${
            run.data.all_passed ? "text-emerald-300" : "text-amber-300"
          }`}
        >
          {run.data.all_passed
            ? "All checks passed — suitable for air-gapped production install."
            : "Some checks failed — fix items above before shipping offline."}
        </p>
      )}
    </Card>
  );
}
