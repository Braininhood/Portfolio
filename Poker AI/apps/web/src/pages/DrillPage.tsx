import { useMutation, useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { Card } from "../components/Card";
import PageIntro from "../components/PageIntro";
import ThinkingTimeControl from "../components/ThinkingTimeControl";
import { groupTimelineByStreet } from "../lib/drillTimeline";
import { displayCard, parseCardCodes } from "../lib/cards";

type DrillHand = {
  hand_id: number;
  label: string;
  hero_cards: string | null;
  board_preview: string | null;
  num_players: number;
  has_decision_point: boolean;
  hero_decision_count: number;
};

type DrillHandsResponse = {
  total: number;
  hands: DrillHand[];
  hint: string | null;
};

type ReplayAction = {
  index: number;
  street: string;
  position: string;
  description: string;
  action_type: string;
  amount_bb: number | null;
};

type ReplayResponse = {
  hand_id: number;
  hero_cards: string | null;
  board_cards: string | null;
  hero_position: string | null;
  actions: ReplayAction[];
};

type ActionProb = {
  kind: string;
  amount_chips: number;
  seat: number;
  prob: number;
  label?: string | null;
};

type DrillSpot = {
  policy_name: string;
  policy_version: string;
  latency_ms: number;
  actions: ActionProb[];
  explanation: string;
  street: string | null;
  step_index: number;
  actual_action: string;
  actual_amount: number | null;
  hero_cards: string | null;
  board: string | null;
  position: string | null;
  pot_bb: number | null;
  stack_bb: number | null;
  spr: number | null;
  action_comparison: string;
  policy_vs_human: string;
  ai_top_action: string | null;
  ai_top_prob: number | null;
  hero_equity?: number | null;
};

type CompareColumn = {
  policy_key: string;
  policy_label: string;
  policy_name: string;
  latency_ms: number;
  actions: { label: string; prob: number }[];
};

type CompareResponse = {
  policies: CompareColumn[];
  consensus: string;
  actual_action: string;
  actual_amount: number | null;
  hero_cards: string | null;
  board: string | null;
  street: string | null;
  position: string | null;
  pot_bb: number | null;
  stack_bb: number | null;
  spr: number | null;
};

type PolicyKey = "distilled" | "heuristic" | "best";

const POLICY_OPTIONS: { key: PolicyKey; label: string }[] = [
  { key: "best", label: "Main AI (recommended)" },
  { key: "distilled", label: "Distilled student" },
  { key: "heuristic", label: "Heuristic" },
];


function cardsDisplay(s: string | null): string {
  if (!s?.trim()) return "—";
  return parseCardCodes(s).map(displayCard).join(" ");
}

function formatActual(action: string, amount: number | null): string {
  const a = action.charAt(0).toUpperCase() + action.slice(1).toLowerCase();
  if (amount != null && amount > 0 && (action === "Call" || action === "Bet" || action === "Raise")) {
    return `${a} ${amount} BB`;
  }
  return a.toUpperCase();
}

function actionBarLabel(ap: ActionProb): string {
  if (ap.label) return ap.label;
  const k = ap.kind.charAt(0).toUpperCase() + ap.kind.slice(1).toLowerCase();
  return k;
}

function ProbBar({ label, prob }: { label: string; prob: number }) {
  const p = Math.max(0, Math.min(100, prob * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm gap-3">
        <span className="text-slate-300 truncate">{label}</span>
        <span className="font-mono text-slate-100 shrink-0">{(prob * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2.5 rounded-full bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full bg-emerald-500/80 transition-all duration-300"
          style={{ width: `${p}%` }}
        />
      </div>
    </div>
  );
}

export default function DrillPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [stepIndex, setStepIndex] = useState<number | null>(null);
  const [policy, setPolicy] = useState<PolicyKey>("best");
  const [thinkingMs, setThinkingMs] = useState(0);
  const [deepSearch, setDeepSearch] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [drillableOnly, setDrillableOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const limit = 40;

  const { data: catalog, isLoading: catalogLoading } = useQuery({
    queryKey: ["drill-hands", offset, drillableOnly],
    queryFn: () =>
      apiGet<DrillHandsResponse>(
        `/drill/hands?limit=${limit}&offset=${offset}&drillable_only=${drillableOnly}`,
      ),
  });

  const { data: steps } = useQuery({
    queryKey: ["drill-steps", selectedId],
    queryFn: () => apiGet<{ hand_id: number; step_indices: number[] }>(`/drill/${selectedId}/steps`),
    enabled: selectedId !== null,
  });

  const { data: replay, isLoading: replayLoading } = useQuery({
    queryKey: ["drill-replay", selectedId],
    queryFn: () => apiGet<ReplayResponse>(`/replay/${selectedId}`),
    enabled: selectedId !== null,
  });

  const decisionSteps = useMemo(
    () => steps?.step_indices ?? [],
    [steps],
  );

  const heroSteps = useMemo(() => new Set(decisionSteps), [decisionSteps]);

  const timelineGroups = useMemo(
    () => (replay ? groupTimelineByStreet(replay.actions, replay.board_cards) : []),
    [replay],
  );

  const spotMutation = useMutation({
    mutationFn: (args: { hand_id: number; step_index: number }) =>
      apiPost<DrillSpot>("/drill/spot", {
        hand_id: args.hand_id,
        step_index: args.step_index,
        policy,
        thinking_ms: thinkingMs,
        deep_search: deepSearch,
      }),
  });

  const compareMutation = useMutation({
    mutationFn: (args: { hand_id: number; step_index: number }) =>
      apiPost<CompareResponse>("/drill/compare", {
        hand_id: args.hand_id,
        step_index: args.step_index,
        thinking_ms: thinkingMs,
        deep_search: deepSearch,
      }),
  });

  const loadSpot = useCallback(
    (handId: number, step: number) => {
      setStepIndex(step);
      if (compareMode) {
        compareMutation.mutate({ hand_id: handId, step_index: step });
      } else {
        spotMutation.mutate({ hand_id: handId, step_index: step });
      }
    },
    [compareMode, compareMutation, spotMutation],
  );

  useEffect(() => {
    if (selectedId !== null && stepIndex !== null) {
      loadSpot(selectedId, stepIndex);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when policy/thinking/compare toggles
  }, [policy, thinkingMs, deepSearch, compareMode]);

  useEffect(() => {
    if (selectedId === null || !replay || stepIndex !== null) return;
    const first = decisionSteps[0];
    if (first !== undefined) {
      loadSpot(selectedId, first);
    }
  }, [selectedId, replay, decisionSteps, stepIndex, loadSpot]);

  const spot = spotMutation.data;
  const compare = compareMutation.data;
  const loading = spotMutation.isPending || compareMutation.isPending;
  const error = spotMutation.error ?? compareMutation.error;

  const currentStepPos = decisionSteps.indexOf(stepIndex ?? -1);

  const goPrev = () => {
    if (selectedId === null || currentStepPos <= 0) return;
    loadSpot(selectedId, decisionSteps[currentStepPos - 1]!);
  };

  const goNext = () => {
    if (selectedId === null || currentStepPos < 0 || currentStepPos >= decisionSteps.length - 1)
      return;
    loadSpot(selectedId, decisionSteps[currentStepPos + 1]!);
  };

  return (
    <div className="space-y-4">
      <PageIntro
        title="Decision drill"
        description="Pick a hand from your history, click any of your decision points, and see what the AI recommends — compared to what you actually did."
      />

      <div className="grid lg:grid-cols-[minmax(220px,280px)_1fr] gap-4 items-start">
        <Card title="Hand list">
          {catalog?.hint && (
            <p className="text-amber-200/90 text-sm mb-3 rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
              {catalog.hint}
            </p>
          )}
          {catalogLoading && (
            <p className="text-slate-400 text-sm">Checking which hands have drillable spots…</p>
          )}
          {catalog && catalog.total > 0 && (
            <>
              <label className="flex items-center gap-2 text-xs text-slate-400 mb-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={drillableOnly}
                  onChange={(e) => {
                    setDrillableOnly(e.target.checked);
                    setOffset(0);
                  }}
                />
                Show drillable hands only
              </label>
              <p className="text-xs text-slate-500 mb-2">
                {catalog.total} hands in library · green dot = validated hero decision points
              </p>
              <ul className="max-h-[420px] overflow-y-auto border border-slate-700 rounded-md divide-y divide-slate-800">
                {catalog.hands.map((h) => (
                  <li key={h.hand_id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedId(h.hand_id);
                        setStepIndex(null);
                        spotMutation.reset();
                        compareMutation.reset();
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-800 flex items-start gap-2 ${
                        selectedId === h.hand_id ? "bg-emerald-900/40" : ""
                      }`}
                    >
                      <span
                        className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${
                          h.has_decision_point ? "bg-emerald-400" : "bg-slate-600"
                        }`}
                        title={
                          h.has_decision_point
                            ? `${h.hero_decision_count} hero decision${h.hero_decision_count === 1 ? "" : "s"}`
                            : "No validated hero decisions"
                        }
                      />
                      <span className="min-w-0">{h.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {catalog.total > offset + limit && (
                <button
                  type="button"
                  className="mt-2 text-sm text-emerald-400 hover:text-emerald-300"
                  onClick={() => setOffset((o) => o + limit)}
                >
                  Load more
                </button>
              )}
            </>
          )}
        </Card>

        <Card title="Hand timeline">
          {!selectedId && (
            <p className="text-slate-400 text-sm">Select a hand from the list to begin.</p>
          )}
          {selectedId && replayLoading && (
            <p className="text-slate-400 text-sm">Loading timeline…</p>
          )}
          {replay && (
            <div className="space-y-4 max-h-[420px] overflow-y-auto">
              {timelineGroups.map((group) => (
                <section key={group.street}>
                  <div className="sticky top-0 z-10 bg-slate-900/95 border-b border-slate-700/80 px-2 py-1.5 mb-2">
                    <h3 className="text-xs font-semibold text-emerald-400/90 uppercase tracking-wide">
                      {group.street}
                      {group.boardLabel ? (
                        <span className="ml-2 font-mono normal-case text-slate-300">
                          {group.boardLabel}
                        </span>
                      ) : null}
                    </h3>
                  </div>
                  <ol className="space-y-2">
                    {group.actions.map((a) => {
                      const isHero = heroSteps.has(a.index);
                      const isActive = stepIndex === a.index;
                      return (
                        <li key={a.index}>
                          <button
                            type="button"
                            disabled={!isHero}
                            onClick={() => selectedId !== null && loadSpot(selectedId, a.index)}
                            className={`w-full text-left rounded-md border px-3 py-2 text-sm transition-colors ${
                              isActive
                                ? "border-emerald-500 bg-emerald-950/40"
                                : isHero
                                  ? "border-emerald-800/60 bg-slate-900/50 hover:bg-emerald-950/30 cursor-pointer"
                                  : "border-slate-800 bg-slate-900/20 opacity-70 cursor-default"
                            }`}
                          >
                            <div className="text-xs text-slate-500">
                              Step {a.index + 1}
                              {isHero && (
                                <span className="ml-2 text-emerald-400 font-medium">
                                  {isActive ? "▶ drilling" : "click to drill"}
                                </span>
                              )}
                            </div>
                            <div className="text-slate-100">{a.description}</div>
                          </button>
                        </li>
                      );
                    })}
                  </ol>
                </section>
              ))}
            </div>
          )}
        </Card>
      </div>

      {(spot || compare || loading || error) && (
        <Card
          title={
            stepIndex !== null && spot
              ? `AI recommendation · step ${stepIndex + 1} · ${spot.position ?? "?"} · ${spot.street ?? "?"}`
              : "AI recommendation"
          }
        >
          <div className="flex flex-wrap gap-4 mb-4 text-sm">
            <label className="flex items-center gap-2 text-slate-400">
              Policy
              <select
                value={policy}
                onChange={(e) => setPolicy(e.target.value as PolicyKey)}
                disabled={compareMode}
                className="rounded-md bg-slate-800 border border-slate-600 px-2 py-1 text-slate-100"
              >
                {POLICY_OPTIONS.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={compareMode}
                onChange={(e) => setCompareMode(e.target.checked)}
                className="rounded"
              />
              Compare policies
            </label>
            <ThinkingTimeControl
              thinkingMs={thinkingMs}
              onThinkingMsChange={setThinkingMs}
              deepSearch={deepSearch}
              onDeepSearchChange={setDeepSearch}
              compact
            />
            <div className="flex gap-2 ml-auto">
              <button
                type="button"
                onClick={goPrev}
                disabled={currentStepPos <= 0}
                className="px-3 py-1 rounded-md text-sm bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40"
              >
                ← Prev decision
              </button>
              <button
                type="button"
                onClick={goNext}
                disabled={currentStepPos < 0 || currentStepPos >= decisionSteps.length - 1}
                className="px-3 py-1 rounded-md text-sm bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40"
              >
                Next decision →
              </button>
            </div>
          </div>

          {loading && <p className="text-slate-400 text-sm">Running policy…</p>}
          {error && (
            <p className="text-amber-200 text-sm rounded-md bg-amber-900/20 border border-amber-800 px-3 py-2">
              {(error as Error).message}
            </p>
          )}

          {spot && !compareMode && (
            <div className="space-y-4">
              <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <dt className="text-slate-500">Your cards</dt>
                  <dd className="font-mono text-slate-100">{cardsDisplay(spot.hero_cards)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Board</dt>
                  <dd className="font-mono text-slate-100">{cardsDisplay(spot.board)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Pot</dt>
                  <dd className="text-slate-100">{spot.pot_bb != null ? `${spot.pot_bb} BB` : "—"}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Stack · SPR</dt>
                  <dd className="text-slate-100">
                    {spot.stack_bb != null ? `${spot.stack_bb} BB` : "—"}
                    {spot.spr != null ? ` · SPR ${spot.spr}` : ""}
                  </dd>
                </div>
              </dl>

              <div>
                <h3 className="text-sm font-medium text-slate-300 mb-2">
                  AI says ({spot.policy_name})
                </h3>
                <div className="space-y-2">
                  {[...spot.actions]
                    .sort((a, b) => b.prob - a.prob)
                    .filter((a) => a.prob > 0.02)
                    .map((a, i) => (
                      <ProbBar
                        key={`${a.kind}-${a.amount_chips}-${i}`}
                        label={actionBarLabel(a)}
                        prob={a.prob}
                      />
                    ))}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Computed in {spot.latency_ms.toFixed(0)} ms
                </p>
              </div>

              <div className="rounded-md bg-slate-800/60 border border-slate-700 px-3 py-2 text-sm text-slate-300">
                <span className="text-slate-500 font-medium">Why: </span>
                {spot.explanation}
              </div>

              {spot.hero_equity != null && (
                <p className="text-sm text-sky-300/90">
                  Hero equity at this node:{" "}
                  <span className="font-mono font-semibold text-sky-200">
                    {(spot.hero_equity * 100).toFixed(1)}%
                  </span>
                </p>
              )}

              <div
                className={`rounded-md border px-3 py-2 text-sm ${
                  spot.policy_vs_human === "Same"
                    ? "border-emerald-800 bg-emerald-950/30 text-emerald-200"
                    : "border-amber-800 bg-amber-950/30 text-amber-100"
                }`}
              >
                <div>
                  You actually:{" "}
                  <span className="font-semibold">
                    {formatActual(spot.actual_action, spot.actual_amount)}
                  </span>
                </div>
                {spot.policy_vs_human !== "Same" && spot.ai_top_action && (
                  <div className="mt-1">
                    ⚠ AI prefers: {spot.ai_top_action}
                    {spot.ai_top_prob != null ? ` (${(spot.ai_top_prob * 100).toFixed(0)}%)` : ""}
                  </div>
                )}
                {spot.policy_vs_human === "Same" && (
                  <div className="mt-1 text-emerald-300">✓ Matches AI top line</div>
                )}
              </div>
            </div>
          )}

          {compare && compareMode && (
            <div className="space-y-4">
              <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <dt className="text-slate-500">Your cards</dt>
                  <dd className="font-mono text-slate-100">{cardsDisplay(compare.hero_cards)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Board</dt>
                  <dd className="font-mono text-slate-100">{cardsDisplay(compare.board)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Pot</dt>
                  <dd className="text-slate-100">
                    {compare.pot_bb != null ? `${compare.pot_bb} BB` : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Stack · SPR</dt>
                  <dd className="text-slate-100">
                    {compare.stack_bb != null ? `${compare.stack_bb} BB` : "—"}
                    {compare.spr != null ? ` · SPR ${compare.spr}` : ""}
                  </dd>
                </div>
              </dl>

              <h3 className="text-sm font-medium text-slate-300">Compare policies</h3>
              <div className="grid sm:grid-cols-3 gap-3">
                {compare.policies.map((col) => (
                  <div
                    key={col.policy_key}
                    className="rounded-md border border-slate-700 bg-slate-900/50 p-3 space-y-2"
                  >
                    <div className="text-sm font-medium text-emerald-400">{col.policy_label}</div>
                    {col.actions.slice(0, 4).map((a) => (
                      <ProbBar key={`${col.policy_key}-${a.label}`} label={a.label} prob={a.prob} />
                    ))}
                    <p className="text-xs text-slate-500">{col.latency_ms.toFixed(0)} ms</p>
                  </div>
                ))}
              </div>
              <p className="text-sm text-slate-300 rounded-md bg-slate-800/60 border border-slate-700 px-3 py-2">
                {compare.consensus}
              </p>
              <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
                You actually:{" "}
                <span className="font-semibold">
                  {formatActual(compare.actual_action, compare.actual_amount)}
                </span>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
