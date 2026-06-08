import { useCallback, useRef, useState } from "react";
import { apiPost } from "../api/client";
import { Card } from "../components/Card";
import CardPicker, { SelectedCardsRow } from "../components/CardPicker";
import PageIntro from "../components/PageIntro";
import {
  CardCode,
  cardsToApiString,
  displayCard,
  parseCardCodes,
} from "../lib/cards";

type EquityResult = {
  hero_equity: number;
  villain_equity: number;
  tie_equity: number;
  hero_cards: string;
  board_cards: string | null;
  villain_range: string;
  mode_used: string;
  latency_ms: number;
  breakdown: Record<string, number>;
  insight: string | null;
};

type RangeMode = "random" | "custom";

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

function EquityBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const p = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-mono text-slate-100">{pct(value)}</span>
      </div>
      <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${color}`}
          style={{ width: `${p}%` }}
        />
      </div>
    </div>
  );
}

export default function EquityPage() {
  const [hero, setHero] = useState<CardCode[]>([]);
  const [board, setBoard] = useState<CardCode[]>([]);
  const [focus, setFocus] = useState<"hero" | "board">("hero");
  const [rangeMode, setRangeMode] = useState<RangeMode>("random");
  const [customRange, setCustomRange] = useState("TT+,AKs");
  const [result, setResult] = useState<EquityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const calculate = useCallback(async () => {
    if (hero.length !== 2) {
      setError("Pick exactly two cards for your hand.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await apiPost<EquityResult>("/equity", {
        hero_cards: cardsToApiString(hero),
        board_cards: cardsToApiString(board),
        villain_range: rangeMode === "random" ? "random" : customRange.trim() || "random",
        mode: "auto",
        num_samples: 8000,
      });
      setResult(res);
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    } catch (e) {
      setResult(null);
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [hero, board, rangeMode, customRange]);

  const villainLabel =
    rangeMode === "random" ? "random hands" : customRange.trim() || "custom range";

  return (
    <div className="space-y-6">
      <PageIntro
        title="Equity calculator"
        description="See how often your hand wins against a villain range — exact math on the flop and later streets, fast simulation preflop. Pick your cards, optionally add a board, then calculate."
      />

      <Card title="Your situation">
        <div className="space-y-4 mb-6">
          <SelectedCardsRow
            label="Your cards"
            cards={hero}
            maxSlots={2}
            onClear={() => {
              setHero([]);
              setFocus("hero");
            }}
          />
          <SelectedCardsRow
            label="Board"
            cards={board}
            maxSlots={5}
            onClear={() => setBoard([])}
          />
        </div>

        <CardPicker
          hero={hero}
          board={board}
          focus={focus}
          onFocusChange={setFocus}
          onHeroChange={setHero}
          onBoardChange={setBoard}
        />

        <div className="mt-6 pt-6 border-t border-slate-700 space-y-3">
          <p className="text-sm text-slate-400">Villain range</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="villain"
                checked={rangeMode === "random"}
                onChange={() => setRangeMode("random")}
                className="accent-emerald-500"
              />
              Random hand
            </label>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="villain"
                checked={rangeMode === "custom"}
                onChange={() => setRangeMode("custom")}
                className="accent-emerald-500"
              />
              Specific range
            </label>
          </div>
          {rangeMode === "custom" && (
            <div>
              <input
                type="text"
                value={customRange}
                onChange={(e) => setCustomRange(e.target.value)}
                placeholder="TT+, AKs, AQs or AhKd"
                className="w-full max-w-md rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:outline-none"
              />
              <p className="text-xs text-slate-500 mt-1">
                Examples: <span className="font-mono text-slate-400">TT+</span>,{" "}
                <span className="font-mono text-slate-400">AKs,AQs</span>,{" "}
                <span className="font-mono text-slate-400">A2s+</span>, or an exact hand{" "}
                <span className="font-mono text-slate-400">QsQh</span>
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => void calculate()}
            disabled={loading || hero.length !== 2}
            className="px-5 py-2.5 rounded-md bg-emerald-600 text-white font-medium text-sm hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Calculating…" : "Calculate equity"}
          </button>
          {hero.length === 2 && (
            <span className="text-xs text-slate-500">
              {hero.map(displayCard).join(" ")}
              {board.length > 0 ? ` · ${board.map(displayCard).join(" ")}` : ""}
            </span>
          )}
        </div>
        {error && (
          <p className="mt-3 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}
      </Card>

      {result && (
        <div ref={resultsRef}>
          <Card title="Results">
            <div className="space-y-4">
              <EquityBar
                label={`Your hand (${result.hero_cards})`}
                value={result.hero_equity}
                color="bg-emerald-500"
              />
              <EquityBar
                label={`Villain (${villainLabel})`}
                value={result.villain_equity}
                color="bg-rose-500/90"
              />
              <EquityBar
                label="Chops (tie)"
                value={result.tie_equity}
                color="bg-slate-500"
              />

              <p className="text-xs text-slate-500 pt-2">
                Computed in {result.latency_ms.toFixed(0)} ms ({result.mode_used}). Pot shares
                (top two bars) sum to 100%; chop rate is shown separately.
              </p>

              {Object.keys(result.breakdown).length > 0 && (
                <div className="rounded-md border border-slate-700 bg-slate-800/40 p-3 text-sm">
                  <p className="text-slate-400 text-xs mb-2">Equity by street (same ranges)</p>
                  <ul className="flex flex-wrap gap-4">
                    {(["flop", "turn", "river"] as const).map((st) =>
                      result.breakdown[st] != null ? (
                        <li key={st} className="text-slate-200">
                          <span className="capitalize text-slate-500">{st}: </span>
                          <span className="font-mono text-emerald-400">{pct(result.breakdown[st])}</span>
                        </li>
                      ) : null,
                    )}
                  </ul>
                </div>
              )}

              {result.insight && (
                <p className="text-sm text-slate-300 bg-slate-800/50 border border-slate-700 rounded-md px-3 py-2 leading-relaxed">
                  <span className="text-emerald-400/80 mr-1">ⓘ</span>
                  {result.insight}
                </p>
              )}
            </div>
          </Card>
        </div>
      )}

      <Card title="Quick presets">
        <p className="text-sm text-slate-400 mb-3">Try a classic spot:</p>
        <div className="flex flex-wrap gap-2">
          {[
            {
              label: "AK vs random (preflop)",
              hero: parseCardCodes("Ah Kd"),
              board: [] as CardCode[],
              range: "random" as RangeMode,
              custom: "",
            },
            {
              label: "AK on QJT (flop)",
              hero: parseCardCodes("Ah Kd"),
              board: parseCardCodes("Qh Jc Ts"),
              range: "random" as RangeMode,
              custom: "",
            },
            {
              label: "TT+ vs AK",
              hero: parseCardCodes("Qs Qh"),
              board: [] as CardCode[],
              range: "custom" as RangeMode,
              custom: "AK",
            },
          ].map((p) => (
            <button
              key={p.label}
              type="button"
              className="text-xs px-3 py-1.5 rounded-md border border-slate-600 text-slate-300 hover:border-emerald-600 hover:text-emerald-200"
              onClick={() => {
                setHero(p.hero);
                setBoard(p.board);
                setRangeMode(p.range);
                if (p.custom) setCustomRange(p.custom);
                setFocus(p.board.length ? "board" : "hero");
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}
