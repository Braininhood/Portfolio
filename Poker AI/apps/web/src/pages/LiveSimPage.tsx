import { useCallback, useEffect, useRef, useState } from "react";
import { simWebSocketUrl } from "../api/client";
import { Card } from "../components/Card";

type SimAction = {
  street: string;
  player: string;
  action: string;
};

type SimPlayer = {
  seat: number;
  name: string;
  cards: string | null;
  delta_bb: number;
};

type SimDetail = {
  board: string;
  why_won: string;
  players: SimPlayer[];
  actions: SimAction[];
  streets: { name: string; board: string }[];
};

type SimPayload = {
  hand_no: number;
  summary: string;
  winner_label: string | null;
  result_bb: number;
  table_label: string;
  went_showdown: boolean;
  mixed_table?: boolean;
  detail?: SimDetail;
};

function HandDetail({ detail }: { detail: SimDetail }) {
  return (
    <div className="mt-3 pt-3 border-t border-slate-600 space-y-3 text-sm">
      <p className="text-slate-300">{detail.why_won}</p>
      <div>
        <h4 className="text-xs text-slate-500 uppercase tracking-wide mb-1">Final board</h4>
        <p className="font-mono text-lg text-slate-100">{detail.board}</p>
      </div>
      <div>
        <h4 className="text-xs text-slate-500 uppercase tracking-wide mb-1">Players & cards</h4>
        <ul className="space-y-1">
          {detail.players.map((p) => (
            <li key={p.seat} className="text-slate-300">
              Seat {p.seat} · {p.name}:{" "}
              <span className="font-mono text-slate-100">{p.cards ?? "—"}</span>
              <span
                className={
                  p.delta_bb > 0 ? "text-emerald-400 ml-2" : p.delta_bb < 0 ? "text-red-400 ml-2" : "ml-2"
                }
              >
                ({p.delta_bb > 0 ? "+" : ""}
                {p.delta_bb} BB)
              </span>
            </li>
          ))}
        </ul>
      </div>
      {detail.streets.length > 0 && (
        <div>
          <h4 className="text-xs text-slate-500 uppercase tracking-wide mb-1">Streets</h4>
          <ul className="text-slate-400 text-xs space-y-0.5">
            {detail.streets.map((s) => (
              <li key={s.name}>
                {s.name}: <span className="font-mono text-slate-300">{s.board}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {detail.actions.length > 0 && (
        <div>
          <h4 className="text-xs text-slate-500 uppercase tracking-wide mb-1">Action timeline</h4>
          <ol className="space-y-1 max-h-48 overflow-y-auto">
            {detail.actions.map((a, i) => (
              <li key={i} className="text-slate-300">
                <span className="text-slate-500">{a.street}</span> — {a.player}:{" "}
                <span className="text-slate-100">{a.action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function HandRow({
  hand,
  expanded,
  onToggle,
}: {
  hand: SimPayload;
  expanded: boolean;
  onToggle: () => void;
}) {
  const badge = hand.went_showdown ? "Showdown" : "Everyone folded";
  const hasDetail = Boolean(hand.detail);
  return (
    <li className="rounded-md border border-slate-700/80 bg-slate-800/50 px-4 py-3">
      <button
        type="button"
        onClick={onToggle}
        disabled={!hasDetail}
        className={`w-full text-left ${hasDetail ? "cursor-pointer hover:opacity-90" : "cursor-default"}`}
      >
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="text-xs font-medium text-slate-500">Hand {hand.hand_no}</span>
          <span className="text-xs rounded-full bg-slate-700 px-2 py-0.5 text-slate-300">
            {hand.table_label}
          </span>
          <span className="text-xs rounded-full bg-slate-700 px-2 py-0.5 text-slate-400">{badge}</span>
          {hasDetail && (
            <span className="text-xs text-emerald-500 ml-auto">
              {expanded ? "Hide hand ▲" : "View full hand ▼"}
            </span>
          )}
        </div>
        <p className="text-slate-100 leading-relaxed">{hand.summary}</p>
        {hand.winner_label && hand.result_bb > 0 && (
          <p className="mt-1 text-sm text-emerald-400">
            Winner: {hand.winner_label} · +{hand.result_bb} BB
          </p>
        )}
      </button>
      {expanded && hand.detail && <HandDetail detail={hand.detail} />}
    </li>
  );
}

type TableMode = "2" | "6" | "9" | "mix";

export default function LiveSimPage() {
  const [events, setEvents] = useState<SimPayload[]>([]);
  const [connected, setConnected] = useState(false);
  const [watching, setWatching] = useState(false);
  const [tableMode, setTableMode] = useState<TableMode>("6");
  const [expandedHand, setExpandedHand] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    if (ws) {
      ws.onopen = null;
      ws.onclose = null;
      ws.onmessage = null;
      ws.onerror = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      wsRef.current = null;
    }
    setConnected(false);
    setWatching(false);
  }, []);

  useEffect(() => {
    if (!watching) return;

    let alive = true;
    const seatsQs = tableMode === "mix" ? "mix" : tableMode;
    const qs = `?seats=${seatsQs}&agent_a=main_agent&agent_b=distilled_gto`;
    const ws = new WebSocket(simWebSocketUrl() + qs);
    wsRef.current = ws;
    ws.onopen = () => {
      if (alive) setConnected(true);
    };
    ws.onclose = () => {
      if (alive) {
        setConnected(false);
        setWatching(false);
      }
    };
    ws.onerror = () => {
      if (alive) setConnected(false);
    };
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data as string) as { event: string; payload: SimPayload };
        if (alive && msg.event === "hand_complete" && msg.payload.summary) {
          setEvents((prev) => [msg.payload, ...prev].slice(0, 30));
          setExpandedHand(msg.payload.hand_no);
        }
      } catch {
        /* ignore */
      }
    };
    return () => {
      alive = false;
      disconnect();
    };
  }, [watching, tableMode, disconnect]);

  const tableHelp =
    tableMode === "mix"
      ? "Mixed tables: rotates 2 → 6 → 9 → 2 … players each hand (like the real league)."
      : tableMode === "2"
        ? "Heads-up: Main AI seat 1 vs GTO baseline seat 2."
        : `Fixed ${tableMode}-max: Main AI on seats 1 & 3+, GTO baseline on seat 2.`;

  return (
    <div className="space-y-4">
      <Card title="Live table watch">
        <p className="text-slate-300 text-sm mb-4">
          Watch AI vs AI play hands in real time. Amounts are in <strong>BB</strong> (big blinds).
          <strong> Click any hand</strong> to see cards, board, and every bet/call/fold.
        </p>

        <div className="flex flex-wrap gap-3 items-center mb-4">
          <label className="text-sm text-slate-400">
            Table
            <select
              className="block mt-1 rounded bg-slate-800 border border-slate-600 px-2 py-1"
              value={tableMode}
              onChange={(e) => {
                disconnect();
                setTableMode(e.target.value as TableMode);
              }}
              disabled={watching}
            >
              <option value="2">2 (heads-up)</option>
              <option value="6">6-max</option>
              <option value="9">9-max</option>
              <option value="mix">Mixed (2 / 6 / 9)</option>
            </select>
          </label>
          {!watching ? (
            <button
              type="button"
              onClick={() => setWatching(true)}
              className="rounded bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium mt-5"
            >
              Start watching
            </button>
          ) : (
            <button
              type="button"
              onClick={disconnect}
              className="rounded bg-slate-600 hover:bg-slate-500 px-4 py-2 text-sm font-medium mt-5"
            >
              Stop watching
            </button>
          )}
        </div>

        <p className="text-xs text-slate-500 mb-3">{tableHelp}</p>

        <div className="flex items-center gap-2 mb-4">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              connected ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
            }`}
          />
          <span className="text-sm text-slate-300">
            {watching
              ? connected
                ? "Live — about one hand per second"
                : "Connecting…"
              : "Stopped"}
          </span>
        </div>
        <p className="text-xs text-slate-600 mb-3">
          Stop the whole app with Ctrl+C in the terminal running <code>poker_ai serve</code>.
        </p>

        {events.length > 0 && (
          <ul className="space-y-3 max-h-[32rem] overflow-y-auto">
            {events.map((e) => (
              <HandRow
                key={e.hand_no}
                hand={e}
                expanded={expandedHand === e.hand_no}
                onToggle={() =>
                  setExpandedHand((id) => (id === e.hand_no ? null : e.hand_no))
                }
              />
            ))}
          </ul>
        )}
        {watching && events.length === 0 && (
          <p className="text-slate-500 text-sm py-8 text-center">Waiting for the first hand…</p>
        )}
      </Card>
    </div>
  );
}
