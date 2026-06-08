import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiGet } from "../api/client";
import { Card } from "../components/Card";

type SpotSummary = {
  cache_key: string;
  board: string;
  top_action: string;
  top_frequency_pct: number;
};

type SpotsPage = {
  total: number;
  page: number;
  page_size: number;
  spots: SpotSummary[];
};

type SpotDetail = {
  board: string;
  summary: string;
  board_note: string | null;
  actions: { action: string; frequency_pct: number }[];
};

export default function SolverSpotsPage() {
  const [page, setPage] = useState(1);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const { data: stats } = useQuery({
    queryKey: ["solver-stats"],
    queryFn: () => apiGet<{ total_spots: number }>("/solver/stats"),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["solver-spots", page],
    queryFn: () => apiGet<SpotsPage>(`/solver/spots?page=${page}&page_size=15`),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["solver-spot", selectedKey],
    queryFn: () => apiGet<SpotDetail>(`/solver/spots/${selectedKey}`),
    enabled: selectedKey !== null,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div className="space-y-4">
      <Card title="Solver study spots">
        <p className="text-slate-400 text-sm mb-3">
          The computer coach studied many postflop situations ahead of time. Each entry is the{" "}
          <strong>shared board cards</strong> (flop/turn/river everyone sees) — not your private
          two cards in hand.
        </p>
        <p className="text-xs text-amber-200/80 bg-amber-900/20 border border-amber-900/50 rounded px-3 py-2 mb-4">
          Example board <span className="font-mono">Tc, Td, 4s</span> means ten of clubs, ten of
          diamonds, four of spades on the table. Your hidden hole cards are separate and are not
          stored in this list.
        </p>
        {stats && (
          <p className="text-sm text-slate-300 mb-4">
            <span className="text-emerald-400 font-medium">{stats.total_spots}</span> situations
            saved
          </p>
        )}
        {isLoading && <p className="text-slate-500">Loading…</p>}
        {error && <p className="text-red-400">{(error as Error).message}</p>}
        {data && data.total === 0 && (
          <p className="text-slate-500 text-sm">
            Nothing cached yet. Run{" "}
            <code className="text-emerald-300">poker_ai solve grid</code> to build the library.
          </p>
        )}
        {data && data.spots.length > 0 && (
          <>
            <ul className="space-y-2 max-h-64 overflow-y-auto mb-3">
              {data.spots.map((s) => (
                <li key={s.cache_key}>
                  <button
                    type="button"
                    onClick={() => setSelectedKey(s.cache_key)}
                    className={`w-full text-left rounded-md border px-3 py-2 text-sm hover:border-emerald-600 ${
                      selectedKey === s.cache_key
                        ? "border-emerald-500 bg-emerald-900/30"
                        : "border-slate-700 bg-slate-800/50"
                    }`}
                  >
                    <span className="text-slate-400 text-xs">Board cards</span>
                    <div className="font-mono text-slate-100">{s.board}</div>
                    <div className="text-slate-500 text-xs mt-1">
                      Usually: {s.top_action} ({s.top_frequency_pct}%)
                    </div>
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex items-center gap-2 text-sm">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 rounded bg-slate-700 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-slate-500">
                Page {page} / {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded bg-slate-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </>
        )}
      </Card>

      {selectedKey && detail && (
        <Card title="Recommended lines">
          {detailLoading && <p className="text-slate-500">Loading…</p>}
          {detail.board_note && (
            <p className="text-xs text-slate-500 mb-3">{detail.board_note}</p>
          )}
          <p className="font-mono text-lg text-slate-100 mb-2">{detail.board}</p>
          <p className="text-slate-300 leading-relaxed mb-4">{detail.summary}</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-700">
                <th className="py-2">Play</th>
                <th>How often</th>
              </tr>
            </thead>
            <tbody>
              {detail.actions.map((a) => (
                <tr key={a.action} className="border-b border-slate-800">
                  <td className="py-2 text-slate-200">{a.action}</td>
                  <td className="text-emerald-300">{a.frequency_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
