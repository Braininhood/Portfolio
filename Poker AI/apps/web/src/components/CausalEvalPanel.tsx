import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { Card } from "./Card";

type LeakRow = {
  rank: number;
  title: string;
  bb_per_100: number;
  description: string;
};

type CausalResponse = {
  player_uid: string;
  hands_analyzed: number;
  counterfactual: {
    hand_id: number;
    street: string;
    narrative: string;
    ev_delta_bb: number;
  } | null;
  leaks: LeakRow[];
  total_leak_bb_per_100: number;
  note: string | null;
};

export default function CausalEvalPanel({ playerUid }: { playerUid: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["player-causal", playerUid],
    queryFn: () =>
      apiGet<CausalResponse>(`/players/${encodeURIComponent(playerUid)}/causal`),
    retry: false,
  });

  if (isLoading) {
    return (
      <Card title="Causal evaluation">
        <p className="text-slate-500 text-sm">Running AIVAT-style leak scan…</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Causal evaluation">
        <p className="text-amber-200/90 text-sm">{(error as Error).message}</p>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card title="Causal evaluation (AIVAT + propensity weighting)">
      <p className="text-xs text-slate-500 mb-3">
        Analyzed {data.hands_analyzed.toLocaleString()} hands with this player
      </p>
      {data.counterfactual && (
        <div className="rounded-md border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-300 mb-4">
          <p className="text-slate-400 text-xs uppercase tracking-wide mb-1">Counterfactual EV</p>
          <p>{data.counterfactual.narrative}</p>
        </div>
      )}
      {data.leaks.length > 0 ? (
        <ul className="space-y-2 text-sm">
          {data.leaks.map((leak) => (
            <li
              key={leak.rank}
              className="flex justify-between gap-3 border-b border-slate-800 pb-2 last:border-0"
            >
              <span className="text-slate-300">
                Leak #{leak.rank}: {leak.title}
                <span className="block text-xs text-slate-500 mt-0.5">{leak.description}</span>
              </span>
              <span className="font-mono text-amber-300 shrink-0">
                {leak.bb_per_100.toFixed(1)} BB/100
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-slate-400 text-sm">No major leaks detected in this sample.</p>
      )}
      {data.leaks.length > 0 && (
        <p className="mt-3 text-sm font-medium text-slate-200">
          Total correctable leaks:{" "}
          <span className="text-amber-300">{data.total_leak_bb_per_100.toFixed(1)} BB/100</span>
        </p>
      )}
      {data.counterfactual && (
        <Link
          to={`/replayer?hand=${data.counterfactual.hand_id}`}
          className="inline-block mt-3 text-sm text-emerald-400 hover:text-emerald-300 underline"
        >
          View counterfactual hand →
        </Link>
      )}
      {data.note && (
        <p className="text-xs text-slate-500 mt-3">{data.note}</p>
      )}
    </Card>
  );
}
