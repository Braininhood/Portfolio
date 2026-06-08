import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiGet } from "../api/client";
import { Card } from "../components/Card";

type HandListItem = {
  hand_id: number;
  label: string;
  hero_cards: string | null;
  board_preview: string | null;
  num_players: number;
};

type HandList = {
  total: number;
  hands: HandListItem[];
  hint: string | null;
};

type ReplayAction = {
  index: number;
  street: string;
  position: string;
  description: string;
  amount_bb: number | null;
  overlay: { kind: string; prob: number }[] | null;
  hero_equity?: number | null;
};

type ReplayResponse = {
  hand_id: number;
  summary: string | null;
  hero_position: string | null;
  hero_cards: string | null;
  board_cards: string | null;
  stakes: string | null;
  big_blind: number | null;
  num_players: number | null;
  num_actions: number;
  actions: ReplayAction[];
  overlay_enabled?: boolean;
  overlay_steps?: number;
};

const ACTION_LABELS: Record<string, string> = {
  Fold: "Fold",
  Check: "Check",
  Call: "Call",
  Bet: "Bet",
  Raise: "Raise",
};

export default function ReplayerPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [wantAiOverlay, setWantAiOverlay] = useState(false);

  const { isError: apiDown, isFetched: apiChecked } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<{ status: string }>("/health"),
    retry: 1,
    staleTime: 10_000,
  });

  const { data: catalog } = useQuery({
    queryKey: ["hands-list"],
    queryFn: () => apiGet<HandList>("/hands?limit=40"),
  });

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ["replay", selectedId, wantAiOverlay],
    queryFn: () =>
      apiGet<ReplayResponse>(
        `/replay/${selectedId}?overlay=${wantAiOverlay}&policy=heuristic&hero_only_overlay=true`,
      ),
    enabled: selectedId !== null,
    staleTime: 0,
  });

  const overlayCount =
    data?.actions.filter((a) => a.overlay && a.overlay.length > 0).length ?? 0;

  return (
    <div className="space-y-4">
      <Card title="Hand replayer">
        <p className="text-slate-400 text-sm mb-4">
          Pick a hand from your database to see cards, board, and every bet. Loads in seconds.
          Optional AI overlay is slower (runs the model on your decisions).
        </p>
        <p className="text-xs text-slate-500 mb-3">
          <strong>BB</strong> = big blind (the main bet size). Amounts are shown in BB so they work
          at any stakes.
        </p>

        {apiChecked && apiDown && (
          <p className="text-amber-200/90 text-sm mb-4 rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
            The app cannot reach the analysis server. Start Poker AI from your terminal (serve
            command) and keep that window open, then reload this page.
          </p>
        )}

        {catalog?.hint && (
          <p className="text-amber-200/90 text-sm mb-4 rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
            {catalog.hint}
          </p>
        )}

        {catalog && catalog.total > 0 && (
          <>
            <p className="text-sm text-slate-300 mb-2">
              {catalog.total} hands in database — pick one to replay:
            </p>
            <ul className="max-h-40 overflow-y-auto border border-slate-700 rounded-md divide-y divide-slate-800 mb-4">
              {catalog.hands.map((h) => (
                <li key={h.hand_id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(h.hand_id)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-800 ${
                      selectedId === h.hand_id ? "bg-emerald-900/40" : ""
                    }`}
                  >
                    {h.label}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        {selectedId !== null && (
          <label className="flex items-center gap-2 text-sm text-slate-400 mb-3">
            <input
              type="checkbox"
              checked={wantAiOverlay}
              onChange={(e) => setWantAiOverlay(e.target.checked)}
            />
            Show AI suggestions under your actions in the timeline (not in “At a glance”)
          </label>
        )}

        {(isLoading || isFetching) && (
          <p className="text-slate-400">
            {wantAiOverlay ? "Loading hand + running AI overlay…" : "Loading hand…"}
          </p>
        )}
        {error && (
          <p className="text-amber-200 text-sm rounded-md bg-amber-900/20 border border-amber-800 px-3 py-2">
            {(error as Error).message}
          </p>
        )}

        {data && !isLoading && (
          <div className="mt-2 space-y-4 text-sm">
            {wantAiOverlay && overlayCount === 0 && !isFetching && (
              <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
                AI overlay could not be computed for this hand (imported action order). The
                timeline below is still correct from your hand history.
              </p>
            )}
            {wantAiOverlay && overlayCount > 0 && (
              <p className="text-emerald-300/90 text-sm rounded-md bg-emerald-900/20 border border-emerald-800 px-3 py-2">
                AI suggestions on {overlayCount} of your decisions (green lines in the timeline).
              </p>
            )}

            <div className="rounded-md bg-slate-800/60 p-4 border border-slate-700">
              <h3 className="text-emerald-400 font-medium mb-2">At a glance</h3>
              <p className="text-slate-300">{data.summary}</p>
              <dl className="grid grid-cols-2 gap-2 mt-3 text-slate-400">
                <dt>Your cards</dt>
                <dd className="text-slate-100 font-mono">{data.hero_cards ?? "—"}</dd>
                <dt>Board</dt>
                <dd className="text-slate-100 font-mono">{data.board_cards ?? "—"}</dd>
                <dt>Position</dt>
                <dd className="text-slate-100">{data.hero_position ?? "—"}</dd>
                <dt>Table</dt>
                <dd className="text-slate-100">
                  {data.num_players} players · {data.stakes ?? "—"}
                </dd>
              </dl>
            </div>

            <h3 className="text-slate-300 font-medium">Action timeline</h3>
            <ol className="space-y-3">
              {data.actions.map((a) => (
                <li
                  key={a.index}
                  className="rounded-md border border-slate-700/80 bg-slate-900/40 px-3 py-2"
                >
                  <div className="text-slate-500 text-xs">
                    Step {a.index + 1} · {a.street}
                  </div>
                  <div className="text-slate-100 font-medium">{a.description}</div>
                  {a.hero_equity != null && (
                    <div className="mt-1 text-xs text-sky-300/90">
                      Hero equity: {(a.hero_equity * 100).toFixed(1)}%
                    </div>
                  )}
                  {wantAiOverlay && a.overlay && a.overlay.length > 0 && (
                    <div className="mt-2 rounded bg-emerald-950/50 border border-emerald-800/60 px-2 py-1.5 text-xs text-emerald-200">
                      <span className="font-medium text-emerald-400">AI would consider: </span>
                      {a.overlay
                        .filter((o) => o.prob > 0.05)
                        .map((o) => {
                          const label = ACTION_LABELS[o.kind] ?? o.kind;
                          return `${label} ${(o.prob * 100).toFixed(0)}%`;
                        })
                        .join(" · ")}
                    </div>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}
      </Card>
    </div>
  );
}
