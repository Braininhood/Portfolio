import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import { Card } from "./Card";

type RangeBucket = {
  tier: string;
  label: string;
  mass_pct: number;
};

type RangeResponse = {
  player_uid: string;
  observed_actions: number;
  buckets: RangeBucket[];
  confidence_label: string;
  confidence_pct: number;
  last_updated_at: string | null;
  last_hand_id: number | null;
  note: string | null;
};

function tierColor(tier: string): string {
  if (tier === "premium") return "bg-emerald-500/80";
  if (tier === "medium") return "bg-sky-500/70";
  return "bg-slate-500/60";
}

export default function RangeInferencePanel({ playerUid }: { playerUid: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["player-range", playerUid],
    queryFn: () =>
      apiGet<RangeResponse>(`/players/${encodeURIComponent(playerUid)}/range`),
    retry: false,
  });

  if (isLoading) {
    return (
      <Card title="Live range inference">
        <p className="text-slate-500 text-sm">Estimating preflop holding distribution…</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Live range inference">
        <p className="text-amber-200/90 text-sm">{(error as Error).message}</p>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card title="Live range inference">
      <p className="text-slate-400 text-sm mb-4">
        Based on {data.observed_actions.toLocaleString()} observed actions
      </p>
      <div className="space-y-3">
        <p className="text-xs text-slate-500 uppercase tracking-wide">Estimated preflop holding range</p>
        {data.buckets.map((b) => (
          <div key={b.tier}>
            <div className="flex justify-between text-sm mb-1 gap-2">
              <span className="text-slate-300 truncate">{b.label}</span>
              <span className="font-mono text-slate-100 shrink-0">{b.mass_pct.toFixed(0)}%</span>
            </div>
            <div className="h-2.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${tierColor(b.tier)}`}
                style={{ width: `${Math.min(100, b.mass_pct)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-2 text-sm">
        <div>
          <span className="text-slate-500">Confidence: </span>
          <span className="text-slate-200">
            {data.confidence_label} ({data.confidence_pct.toFixed(0)}%)
          </span>
          <div className="h-2 rounded-full bg-slate-800 mt-1 overflow-hidden">
            <div
              className="h-full bg-emerald-500/70 rounded-full"
              style={{ width: `${Math.min(100, data.confidence_pct)}%` }}
            />
          </div>
        </div>
        {data.last_updated_at && data.last_hand_id != null && (
          <p className="text-xs text-slate-500">
            Last updated: {data.last_updated_at} at hand #{data.last_hand_id.toLocaleString()}
          </p>
        )}
        {data.note && (
          <p className="text-xs text-amber-200/80 rounded-md bg-amber-900/20 border border-amber-800/60 px-2 py-1.5">
            {data.note}
          </p>
        )}
      </div>
    </Card>
  );
}
