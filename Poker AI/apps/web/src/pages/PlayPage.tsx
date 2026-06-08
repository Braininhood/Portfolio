import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost, playWebSocketUrl } from "../api/client";
import PlayActionPanel from "../components/play/PlayActionPanel";
import PlayStudyPanel from "../components/play/PlayStudyPanel";
import PlayTableFelt from "../components/play/PlayTableFelt";
import { Card } from "../components/Card";
import PageIntro from "../components/PageIntro";
import { normalizeSeat, reducePlayWs } from "../lib/playState";
import type {
  HandRecord,
  LegalAction,
  PlayBot,
  SeatState,
  TableSnapshot,
  WsMessage,
} from "../lib/playTypes";
import { SEAT_OPTIONS } from "../lib/playTypes";

const QUICK_FILLS: { label: string; pick: (bots: PlayBot[]) => string[] }[] = [
  {
    label: "All easy",
    pick: (bots) => {
      const easy = bots.filter((b) => b.difficulty === "Easiest" || b.difficulty === "Easy");
      return easy.length ? easy.map((b) => b.id) : ["fish", "random"];
    },
  },
  {
    label: "All medium",
    pick: (bots) => {
      const med = bots.filter((b) => b.difficulty === "Medium");
      return med.length ? med.map((b) => b.id) : ["passive_reg", "nit"];
    },
  },
  {
    label: "All hard",
    pick: (bots) => {
      const hard = bots.filter((b) => b.difficulty === "Hard");
      return hard.length ? hard.map((b) => b.id) : ["tag", "lag"];
    },
  },
  { label: "Random mix", pick: (bots) => bots.map((b) => b.id) },
];

type PlayState = {
  table: TableSnapshot | null;
  heroCards: string[];
  heroHand: import("../lib/playTypes").HeroHandInfo;
  turn: Extract<WsMessage, { type: "your_turn" }> | null;
  actionLog: import("../lib/playTypes").ActionLogEntry[];
  handActionLog: import("../lib/playTypes").ActionLogEntry[];
  history: import("../lib/playTypes").HandHistoryRow[];
  studyHands: import("../lib/playTypes").HandRecord[];
  sessionStats: { hands: number; net_bb: number; vpip_pct: number; pfr_pct: number };
  showdown: Extract<WsMessage, { type: "showdown" }> | null;
  handResult: number | null;
  awaitNext: boolean;
  timeoutMsg: string | null;
  lastActionLabel: string | null;
  botReplaceMsg: string | null;
};

const initialPlayState: PlayState = {
  table: null,
  heroCards: [],
  heroHand: null,
  turn: null,
  actionLog: [],
  handActionLog: [],
  history: [],
  studyHands: [],
  sessionStats: { hands: 0, net_bb: 0, vpip_pct: 0, pfr_pct: 0 },
  showdown: null,
  handResult: null,
  awaitNext: false,
  timeoutMsg: null,
  lastActionLabel: null,
  botReplaceMsg: null,
};

function playReducer(state: PlayState, msg: WsMessage): PlayState {
  return reducePlayWs(state, msg);
}

function TimerRing({ remainingMs, totalMs }: { remainingMs: number; totalMs: number }) {
  const pct = Math.max(0, Math.min(1, remainingMs / totalMs));
  const color = pct > 0.5 ? "#34d399" : pct > 0.2 ? "#fbbf24" : "#f87171";
  const r = 18;
  const circ = 2 * Math.PI * r;
  return (
    <svg width="44" height="44" className="inline-block -rotate-90" aria-hidden>
      <circle cx="22" cy="22" r={r} fill="none" stroke="#334155" strokeWidth="4" />
      <circle
        cx="22"
        cy="22"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeDasharray={circ}
        strokeDashoffset={circ * (1 - pct)}
        strokeLinecap="round"
      />
    </svg>
  );
}

function PlaySetup({
  bots,
  onStart,
  loading,
}: {
  bots: PlayBot[];
  onStart: (config: {
    seats: number;
    user_seat: number;
    bots: string[];
    buy_in_bb: number;
    ante_bb: number;
    timeout_ms: number;
  }) => void;
  loading: boolean;
}) {
  const [seats, setSeats] = useState<number>(6);
  const [buyIn, setBuyIn] = useState(100);
  const [anteBb, setAnteBb] = useState(0);
  const [timeoutSec, setTimeoutSec] = useState(10);
  const [botIds, setBotIds] = useState<string[]>(() =>
    Array.from({ length: 5 }, (_, i) => ["fish", "tag", "random", "lag", "distilled_gto"][i] ?? "random"),
  );

  useEffect(() => {
    const needed = seats - 1;
    setBotIds((prev) => {
      if (prev.length === needed) return prev;
      if (prev.length > needed) return prev.slice(0, needed);
      return [...prev, ...Array.from({ length: needed - prev.length }, () => "random")];
    });
  }, [seats]);

  const botById = useMemo(() => Object.fromEntries(bots.map((b) => [b.id, b])), [bots]);

  return (
    <Card title="Set up your table">
      <div className="space-y-5">
        <div>
          <p className="text-sm text-slate-400 mb-2">Seats at table</p>
          <div className="flex gap-4">
            {SEAT_OPTIONS.map((n) => (
              <label key={n} className="flex items-center gap-2 text-slate-200 cursor-pointer">
                <input type="radio" name="seats" checked={seats === n} onChange={() => setSeats(n)} />
                {n}-max
              </label>
            ))}
          </div>
        </div>

        <label className="block text-sm text-slate-300">
          Buy-in (BB)
          <input
            type="number"
            min={20}
            max={500}
            value={buyIn}
            onChange={(e) => setBuyIn(Number(e.target.value))}
            className="mt-1 block w-32 rounded border border-slate-600 bg-slate-800 px-2 py-1"
          />
        </label>

        <div>
          <p className="text-sm text-slate-400 mb-2">Opponents ({seats - 1})</p>
          <ul className="space-y-2">
            {botIds.map((id, idx) => {
              const meta = botById[id];
              return (
                <li key={idx} className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-slate-500 w-16">Seat {idx + 1}</span>
                  <select
                    value={id}
                    onChange={(e) =>
                      setBotIds((prev) => prev.map((b, i) => (i === idx ? e.target.value : b)))
                    }
                    className="rounded border border-slate-600 bg-slate-800 px-2 py-1 min-w-[11rem]"
                  >
                    {bots.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} ({b.difficulty})
                      </option>
                    ))}
                  </select>
                  <span className="text-xs text-slate-500">{meta?.difficulty}</span>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="flex flex-wrap gap-2">
          {QUICK_FILLS.map((q) => (
            <button
              key={q.label}
              type="button"
              className="text-xs px-2 py-1 rounded border border-slate-600 text-slate-300 hover:bg-slate-800"
              onClick={() => {
                const pool = q.pick(bots);
                setBotIds((prev) => prev.map((_, i) => pool[i % pool.length] ?? "random"));
              }}
            >
              {q.label}
            </button>
          ))}
        </div>

        <label className="block text-sm text-slate-300">
          Ante (BB per player, 0 = none)
          <input
            type="number"
            min={0}
            max={5}
            step={0.1}
            value={anteBb}
            onChange={(e) => setAnteBb(Number(e.target.value))}
            className="mt-1 block w-32 rounded border border-slate-600 bg-slate-800 px-2 py-1"
          />
        </label>

        <label className="block text-sm text-slate-300">
          Action timer (seconds)
          <input
            type="number"
            min={3}
            max={60}
            value={timeoutSec}
            onChange={(e) => setTimeoutSec(Number(e.target.value))}
            className="mt-1 block w-32 rounded border border-slate-600 bg-slate-800 px-2 py-1"
          />
        </label>

        <button
          type="button"
          disabled={loading || bots.length === 0}
          onClick={() =>
            onStart({
              seats,
              user_seat: 0,
              bots: botIds,
              buy_in_bb: buyIn,
              ante_bb: anteBb,
              timeout_ms: timeoutSec * 1000,
            })
          }
          className="px-5 py-2.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium disabled:opacity-50"
        >
          {loading ? "Starting…" : "Start playing"}
        </button>
      </div>
    </Card>
  );
}

function BettingControls({
  turn,
  onAction,
}: {
  turn: Extract<WsMessage, { type: "your_turn" }>;
  onAction: (action: string, amount?: number) => void;
}) {
  const [betSize, setBetSize] = useState(3);
  const [remainingMs, setRemainingMs] = useState(turn.timeout_ms);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    setRemainingMs(turn.timeout_ms);
    const raise = turn.legal_actions.find((a) => a.kind === "raise");
    const bet = turn.legal_actions.find((a) => a.kind === "bet");
    const pick = raise ?? bet;
    if (pick && "suggested_bb" in pick && pick.suggested_bb.length) {
      setBetSize(pick.suggested_bb[0]);
    } else if (pick && "min_bb" in pick) {
      setBetSize(pick.min_bb);
    }
  }, [turn]);

  useEffect(() => {
    const started = Date.now();
    timerRef.current = window.setInterval(() => {
      setRemainingMs(Math.max(0, turn.timeout_ms - (Date.now() - started)));
    }, 100);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [turn]);

  const legal = turn.legal_actions;
  const canFold = legal.some((a) => a.kind === "fold");
  const canCheck = legal.some((a) => a.kind === "check");
  const canCall = legal.find((a): a is Extract<LegalAction, { kind: "call" }> => a.kind === "call");
  const canBet = legal.find((a): a is Extract<LegalAction, { kind: "bet" }> => a.kind === "bet");
  const canRaise = legal.find((a): a is Extract<LegalAction, { kind: "raise" }> => a.kind === "raise");
  const canAllIn = legal.find((a): a is Extract<LegalAction, { kind: "all_in" }> => a.kind === "all_in");

  const sizing = canBet ?? canRaise;
  const minBb = sizing && "min_bb" in sizing ? sizing.min_bb : 1;
  const maxBb =
    canAllIn?.amount_bb ??
    (canRaise ? canRaise.max_bb : canBet ? canBet.max_bb : turn.seats.find((s) => s.is_hero)?.stack_bb ?? 100);

  const potBb = turn.pot_bb;
  const shortcuts = useMemo(
    () =>
      [
        { label: "⅓ pot", v: Math.round((potBb / 3) * 10) / 10 },
        { label: "½ pot", v: Math.round((potBb / 2) * 10) / 10 },
        { label: "⅔ pot", v: Math.round(((potBb * 2) / 3) * 10) / 10 },
        { label: "Pot", v: Math.round(potBb * 10) / 10 },
        { label: "All-in", v: maxBb },
      ].filter((x) => x.v >= minBb && x.v <= maxBb),
    [potBb, minBb, maxBb],
  );

  return (
    <div className="border-t border-slate-700 pt-4 mt-4">
      <div className="flex items-center gap-3 mb-3">
        <TimerRing remainingMs={remainingMs} totalMs={turn.timeout_ms} />
        <div>
          <p className="text-emerald-300 font-semibold">Your turn</p>
          <p className="text-xs text-slate-400">{(remainingMs / 1000).toFixed(1)}s remaining</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {canFold && (
          <button type="button" className="px-4 py-2 rounded-md bg-red-900/70 hover:bg-red-800 text-red-50 font-medium" onClick={() => onAction("fold")}>
            Fold
          </button>
        )}
        {canCheck && (
          <button type="button" className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 font-medium" onClick={() => onAction("check")}>
            Check
          </button>
        )}
        {canCall && (
          <button type="button" className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 font-medium" onClick={() => onAction("call")}>
            Call {canCall.amount_bb} BB
          </button>
        )}
        {canAllIn && (
          <button type="button" className="px-4 py-2 rounded-md bg-rose-700 hover:bg-rose-600 font-medium" onClick={() => onAction("all_in")}>
            All-in {canAllIn.amount_bb} BB
          </button>
        )}
        {(canBet || canRaise) && (
          <button
            type="button"
            className="px-4 py-2 rounded-md bg-emerald-700 hover:bg-emerald-600 font-medium"
            onClick={() => onAction(canBet ? "bet" : "raise", betSize)}
          >
            {canBet ? "Bet" : "Raise to"} {betSize} BB
          </button>
        )}
      </div>

      {(canBet || canRaise) && (
        <div className="rounded-lg border border-slate-600 bg-slate-800/40 p-3 space-y-2">
          <div className="flex flex-wrap gap-2">
            {shortcuts.map((s) => (
              <button
                key={s.label}
                type="button"
                className={`text-xs px-2.5 py-1 rounded border ${s.label === "All-in" ? "border-rose-600 text-rose-300 hover:bg-rose-950" : "border-slate-600 text-slate-300 hover:bg-slate-800"}`}
                onClick={() => setBetSize(s.v)}
              >
                {s.label}
              </button>
            ))}
          </div>
          <input
            type="range"
            min={minBb}
            max={maxBb}
            step={0.1}
            value={Math.min(betSize, maxBb)}
            onChange={(e) => setBetSize(Number(e.target.value))}
            className="w-full"
          />
          <input
            type="number"
            min={minBb}
            max={maxBb}
            step={0.1}
            value={betSize}
            onChange={(e) => setBetSize(Number(e.target.value))}
            className="w-28 rounded border border-slate-600 bg-slate-900 px-2 py-1 text-sm font-mono"
          />
        </div>
      )}
    </div>
  );
}

function PlaySessionSummary({
  summary,
  sessionHands,
  showHistory,
  onToggleHistory,
  onPlayAgain,
  onChangeBots,
}: {
  summary: {
    hands_played: number;
    net_bb: number;
    bb_per_100?: number;
    vpip_pct: number;
    pfr_pct: number;
    af?: number;
    coaching_tips: string[];
    opponent_results?: { bot_id: string; name: string; net_bb: number; beaten: boolean }[];
  };
  sessionHands: HandRecord[];
  showHistory: boolean;
  onToggleHistory: () => void;
  onPlayAgain: () => void;
  onChangeBots: () => void;
}) {
  return (
    <Card title="Session complete">
      <div className="space-y-4">
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-slate-500">Hands</dt>
            <dd className="text-lg font-semibold text-slate-100">{summary.hands_played}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Net result</dt>
            <dd className={`text-lg font-semibold ${summary.net_bb >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {summary.net_bb >= 0 ? "+" : ""}
              {summary.net_bb} BB
            </dd>
          </div>
          {summary.bb_per_100 != null && (
            <div>
              <dt className="text-slate-500">BB / 100</dt>
              <dd className="text-slate-200">{summary.bb_per_100}</dd>
            </div>
          )}
          <div>
            <dt className="text-slate-500">VPIP / PFR</dt>
            <dd className="text-slate-200">
              {summary.vpip_pct}% / {summary.pfr_pct}%
            </dd>
          </div>
          {summary.af != null && (
            <div>
              <dt className="text-slate-500">AF</dt>
              <dd className="text-slate-200">{summary.af}</dd>
            </div>
          )}
        </dl>
        {summary.opponent_results && summary.opponent_results.length > 0 && (
          <div>
            <p className="text-sm text-slate-400 mb-2">Opponents beaten</p>
            <ul className="flex flex-wrap gap-2 text-sm">
              {summary.opponent_results.map((o) => (
                <li
                  key={o.bot_id}
                  className={`px-2 py-1 rounded ${o.beaten ? "bg-emerald-900/40 text-emerald-300" : "bg-red-900/30 text-red-300"}`}
                >
                  {o.beaten ? "✓" : "✗"} {o.name} ({o.net_bb >= 0 ? "+" : ""}
                  {o.net_bb} BB)
                </li>
              ))}
            </ul>
          </div>
        )}
        <div>
          <p className="text-sm text-slate-400 mb-2">Coaching tips</p>
          <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
            {summary.coaching_tips.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="px-5 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 font-medium" onClick={onPlayAgain}>
            Play again
          </button>
          <button
            type="button"
            className="px-5 py-2 rounded-md border border-slate-600 text-slate-200 hover:bg-slate-800 font-medium"
            onClick={onChangeBots}
          >
            Change bots
          </button>
          {sessionHands.length > 0 && (
            <button
              type="button"
              className="px-5 py-2 rounded-md border border-sky-700/60 text-sky-300 hover:bg-sky-950/40 font-medium"
              onClick={onToggleHistory}
            >
              {showHistory ? "Hide hand history" : "View hand history"}
            </button>
          )}
        </div>
        {showHistory && sessionHands.length > 0 && (
          <div className="border border-slate-700 rounded-lg p-3 max-h-64 overflow-y-auto">
            <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Session history</p>
            <ul className="space-y-2 text-sm">
              {[...sessionHands].reverse().map((h) => (
                <li key={h.hand_no} className="flex justify-between gap-2 border-b border-slate-800 pb-2 last:border-0">
                  <span className="text-slate-300">
                    #{h.hand_no} {h.ending_street ?? "hand"}
                    {h.went_showdown ? " · SD" : ""}
                    {h.hero_hand?.name ? ` · ${h.hero_hand.name}` : ""}
                  </span>
                  <span className={h.result_bb >= 0 ? "text-emerald-400 font-mono" : "text-red-400 font-mono"}>
                    {h.result_bb >= 0 ? "+" : ""}
                    {h.result_bb} BB
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  );
}

function PlayTable({
  sessionId,
  onLeave,
  hintsEnabled,
  hintThinkingMs,
}: {
  sessionId: string;
  onLeave: () => void;
  hintsEnabled: boolean;
  hintThinkingMs: number;
}) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedStudyHand, setSelectedStudyHand] = useState<number | null>(null);
  const [hint, setHint] = useState<{ label: string; detail: string; prob_pct: number } | null>(null);
  const [state, dispatch] = useReducer(playReducer, initialPlayState);

  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  useEffect(() => {
    let closed = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let ws: WebSocket | null = null;

    const connect = () => {
      if (closed) return;
      ws = new WebSocket(playWebSocketUrl(sessionId));
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closed) {
          reconnectTimer = setTimeout(connect, 1500);
        }
      };
      ws.onerror = () => {
        ws?.close();
      };
      ws.onmessage = (ev) => {
        const raw = JSON.parse(ev.data) as Record<string, unknown>;
        if (raw.type === "hand_started" || raw.type === "your_turn" || raw.type === "table_update" || raw.type === "street_change" || raw.type === "opponent_action" || raw.type === "session_sync") {
          if (Array.isArray(raw.seats)) {
            raw.seats = (raw.seats as Record<string, unknown>[]).map(normalizeSeat);
          }
        }
        if (raw.type === "your_turn") setHint(null);
        dispatch(raw as WsMessage);
      };
    };

    connect();
    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [sessionId]);

  useEffect(() => {
    if (!hintsEnabled || !state.turn?.game_state || !connected) return;
    let cancelled = false;
    const t = window.setTimeout(() => {
      void (async () => {
        try {
          const res = await apiPost<{
            actions: { kind: string; prob: number; label?: string }[];
            explanation: string;
            hero_equity?: number | null;
          }>("/decide", {
            game_state: state.turn!.game_state,
            policy: "best",
            profile_id: "hero",
            thinking_ms: hintThinkingMs,
            include_equity: true,
          });
          if (cancelled) return;
          const top = [...res.actions].sort((a, b) => b.prob - a.prob)[0];
          if (!top) return;
          const prob_pct = Math.round(top.prob * 1000) / 10;
          const label = top.label ?? top.kind;
          const expl = res.explanation.split("\n")[0]?.trim();
          const eq =
            res.hero_equity != null
              ? ` · Equity ${(res.hero_equity * 100).toFixed(1)}%`
              : "";
          setHint({
            label,
            prob_pct,
            detail: expl
              ? `Recommended: ${label} (${prob_pct}%)${eq} — ${expl}`
              : `Recommended: ${label} (${prob_pct}%)${eq}`,
          });
        } catch {
          if (!cancelled) setHint(null);
        }
      })();
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [hintsEnabled, state.turn, connected, hintThinkingMs]);

  const table = state.table;
  const seats: SeatState[] = table?.seats ?? [];
  const heroSeat = seats.find((s) => s.is_hero)?.seat ?? 0;

  const showdownBySeat = useMemo(() => {
    if (!state.showdown?.seats?.length) return undefined;
    const map: Record<number, string[]> = {};
    for (const s of state.showdown.seats) {
      if (s.cards?.length >= 2) map[s.seat] = s.cards;
    }
    return Object.keys(map).length ? map : undefined;
  }, [state.showdown]);

  const feltBoard = state.showdown?.board ?? table?.board ?? "";

  return (
    <div className="grid xl:grid-cols-[1fr_17rem] gap-4">
      <div className="space-y-3">
        <Card
          title={
            table
              ? `Hand #${table.hand_no} · ${table.street.toUpperCase()} · ${seats.length}-max`
              : "Connecting…"
          }
        >
          {!connected && (
            <p className="text-amber-400 text-sm mb-2">
              {state.table ? "Reconnecting to table…" : "Connecting to table…"}
            </p>
          )}
          {state.lastActionLabel && (
            <p className="text-sm text-slate-400 mb-2 border-l-2 border-slate-600 pl-2">{state.lastActionLabel}</p>
          )}
          {state.botReplaceMsg && (
            <p className="text-sm text-sky-300 mb-2 border-l-2 border-sky-600 pl-2">{state.botReplaceMsg}</p>
          )}
          {state.timeoutMsg && <p className="text-amber-300 text-sm mb-2">{state.timeoutMsg}</p>}

          <PlayTableFelt
            seats={seats}
            heroSeat={heroSeat}
            heroCards={state.heroCards}
            heroHand={state.heroHand}
            board={feltBoard}
            potBb={state.showdown?.pot_bb ?? table?.pot_bb ?? 0}
            street={table?.street ?? "preflop"}
            showdownBySeat={showdownBySeat}
          />

          {state.showdown && (
            <div className="mt-4 p-3 rounded-lg border border-slate-600 bg-slate-800/50">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Showdown · pot {state.showdown.pot_bb ?? table?.pot_bb ?? 0} BB
              </h3>
              {(state.showdown.winners?.length ? state.showdown.winners : state.showdown.winner ? [state.showdown.winner] : []).map(
                (w) => (
                  <p key={w.seat} className="text-emerald-400 text-sm mb-2 font-medium">
                    {w.name} wins {w.chips_won_bb != null ? `${w.chips_won_bb} BB` : ""} with {w.hand_rank}
                    <span className="font-mono text-slate-300 ml-2">{w.cards.join(" ")}</span>
                  </p>
                ),
              )}
              <ul className="space-y-1 text-sm">
                {state.showdown.seats.map((s) => (
                  <li key={s.seat} className={s.won ? "text-emerald-400" : "text-slate-400"}>
                    {s.name}: <span className="font-mono">{s.cards.join(" ")}</span> — {s.hand_rank}
                    {s.chips_won_bb != null && s.chips_won_bb !== 0 ? ` (${s.chips_won_bb >= 0 ? "+" : ""}${s.chips_won_bb} BB)` : ""}
                    {s.won ? " ✓ Won" : ""}
                    {s.folded ? " (folded)" : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {state.handResult !== null && (
            <p className={`mt-3 text-sm font-medium ${state.handResult >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              Hand result: {state.handResult >= 0 ? "+" : ""}
              {state.handResult} BB
            </p>
          )}

          {state.turn && <BettingControls turn={state.turn} onAction={(action, amount) => send({ type: "action", action, amount })} />}

          {hint && hintsEnabled && state.turn && (
            <div className="mt-3 rounded-lg border border-sky-700/50 bg-sky-950/30 px-3 py-2 text-sm">
              <p className="text-sky-300 font-medium">AI hint: {hint.detail}</p>
            </div>
          )}

          {state.awaitNext && (
            <button
              type="button"
              className="mt-4 px-5 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 font-medium"
              onClick={() => send({ type: "next_hand" })}
            >
              Next hand →
            </button>
          )}

          <button type="button" className="mt-4 block text-sm text-slate-500 hover:text-slate-300" onClick={onLeave}>
            End session
          </button>
        </Card>
      </div>

      <PlayActionPanel
        handLog={state.handActionLog}
        sessionLog={state.actionLog}
        history={state.history}
        sessionStats={state.sessionStats}
        studyHands={state.studyHands}
        selectedStudyHand={selectedStudyHand}
        onSelectStudyHand={setSelectedStudyHand}
        heroHand={state.heroHand}
      />
    </div>
  );
}

export default function PlayPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hintsEnabled, setHintsEnabled] = useState(false);
  const [hintThinkingMs, setHintThinkingMs] = useState(0);
  const [endSummary, setEndSummary] = useState<{
    hands_played: number;
    net_bb: number;
    bb_per_100?: number;
    vpip_pct: number;
    pfr_pct: number;
    af?: number;
    coaching_tips: string[];
    opponent_results?: { bot_id: string; name: string; net_bb: number; beaten: boolean }[];
  } | null>(null);
  const [endedSessionHands, setEndedSessionHands] = useState<HandRecord[]>([]);
  const [showSessionHistory, setShowSessionHistory] = useState(false);

  const botsQuery = useQuery({
    queryKey: ["play-bots"],
    queryFn: () => apiGet<{ bots: PlayBot[] }>("/play/bots"),
  });

  const activeSessionsQuery = useQuery({
    queryKey: ["play-sessions-active"],
    queryFn: () =>
      apiGet<{
        sessions: { session_id: string; hands_played: number; net_bb: number; table_config: Record<string, unknown> }[];
      }>("/play/sessions"),
    enabled: !sessionId && !endSummary,
  });

  const resumeId = activeSessionsQuery.data?.sessions?.[0]?.session_id;
  const resumeInfoQuery = useQuery({
    queryKey: ["play-resume", resumeId],
    queryFn: () =>
      apiGet<{
        session: { hands_played: number; net_bb: number };
        persisted_hands: number;
        can_resume: boolean;
        resume: { phase?: string; hand_no?: number; street?: string; updated_at?: string } | null;
      }>(`/play/sessions/${resumeId}/resume`),
    enabled: Boolean(resumeId) && !sessionId && !endSummary,
  });

  const startMutation = useMutation({
    mutationFn: (body: {
      seats: number;
      user_seat: number;
      bots: string[];
      buy_in_bb: number;
      ante_bb: number;
      timeout_ms: number;
    }) => apiPost<{ session_id: string }>("/play/sessions", body),
    onSuccess: (data) => {
      setEndSummary(null);
      setEndedSessionHands([]);
      setShowSessionHistory(false);
      setSessionId(data.session_id);
    },
  });

  const leave = useCallback(async () => {
    const endingId = sessionId;
    if (endingId) {
      try {
        const res = await apiPost<{ status: string; summary: typeof endSummary }>(
          `/play/sessions/${endingId}/end`,
          {},
        );
        if (res.summary) setEndSummary(res.summary as NonNullable<typeof endSummary>);
        try {
          const study = await apiGet<{ hands: HandRecord[] }>(`/play/sessions/${endingId}/study`);
          setEndedSessionHands(study.hands ?? []);
        } catch {
          setEndedSessionHands([]);
        }
      } catch {
        /* session may already be gone */
      }
    }
    setSessionId(null);
  }, [sessionId]);

  const resumeSession = activeSessionsQuery.data?.sessions?.[0];
  const resumeDetail = resumeInfoQuery.data;

  return (
    <div className="space-y-4 max-w-6xl">
      <PageIntro
        title="Play vs AI"
        description="Full-ring NL Hold'em with optional antes, side-pot showdowns, and study logs for AI training."
      />
      {endSummary ? (
        <PlaySessionSummary
          summary={endSummary}
          sessionHands={endedSessionHands}
          showHistory={showSessionHistory}
          onToggleHistory={() => setShowSessionHistory((v) => !v)}
          onPlayAgain={() => {
            setEndSummary(null);
            setEndedSessionHands([]);
            setShowSessionHistory(false);
          }}
          onChangeBots={() => {
            setEndSummary(null);
            setEndedSessionHands([]);
            setShowSessionHistory(false);
          }}
        />
      ) : !sessionId ? (
        <>
          {resumeSession && resumeDetail?.can_resume && (
            <Card title="Resume session?">
              <p className="text-sm text-slate-300 mb-1">
                Hand #{resumeDetail.resume?.hand_no ?? resumeSession.hands_played} ·{" "}
                {(resumeDetail.resume?.street ?? resumeDetail.resume?.phase ?? "table").toUpperCase()} ·{" "}
                {resumeSession.net_bb >= 0 ? "+" : ""}
                {resumeSession.net_bb} BB
              </p>
              <p className="text-xs text-slate-500 mb-3">
                {resumeDetail.persisted_hands} hands saved for study
                {resumeDetail.resume?.updated_at ? ` · last active ${resumeDetail.resume.updated_at}` : ""}
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 text-sm font-medium"
                  onClick={() => setSessionId(resumeSession.session_id)}
                >
                  Resume
                </button>
                <button
                  type="button"
                  className="px-4 py-2 rounded-md border border-slate-600 text-sm text-slate-300 hover:bg-slate-800"
                  onClick={() => void apiPost(`/play/sessions/${resumeSession.session_id}/end`, {}).then(() => activeSessionsQuery.refetch())}
                >
                  End session
                </button>
              </div>
            </Card>
          )}
          <PlaySetup
            bots={botsQuery.data?.bots ?? []}
            loading={startMutation.isPending}
            onStart={(cfg) => startMutation.mutate(cfg)}
          />
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input type="checkbox" checked={hintsEnabled} onChange={(e) => setHintsEnabled(e.target.checked)} />
            Show AI hint on your turn (opt-in)
          </label>
          {hintsEnabled && (
            <label className="flex items-center gap-2 text-sm text-slate-400">
              Hint thinking time
              <select
                value={hintThinkingMs}
                onChange={(e) => setHintThinkingMs(Number(e.target.value))}
                className="rounded-md bg-slate-800 border border-slate-600 px-2 py-1 text-slate-100"
              >
                {[0, 50, 200, 500].map((ms) => (
                  <option key={ms} value={ms}>
                    {ms} ms
                  </option>
                ))}
              </select>
            </label>
          )}
          <p className="text-xs text-slate-500">
            Increase thinking time to make GTO hints stronger but slower (~200 ms delay before hint).
          </p>
        </>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
              <input type="checkbox" checked={hintsEnabled} onChange={(e) => setHintsEnabled(e.target.checked)} />
              AI hints
            </label>
            {hintsEnabled && (
              <label className="flex items-center gap-2 text-slate-400">
                Thinking
                <select
                  value={hintThinkingMs}
                  onChange={(e) => setHintThinkingMs(Number(e.target.value))}
                  className="rounded-md bg-slate-800 border border-slate-600 px-2 py-1 text-slate-100"
                >
                  {[0, 50, 200, 500].map((ms) => (
                    <option key={ms} value={ms}>
                      {ms} ms
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          <PlayTable
            sessionId={sessionId}
            onLeave={() => void leave()}
            hintsEnabled={hintsEnabled}
            hintThinkingMs={hintThinkingMs}
          />
        </>
      )}
      {startMutation.isError && (
        <p className="text-red-400 text-sm">{(startMutation.error as Error).message}</p>
      )}
      <PlayStudyPanel />
    </div>
  );
}
