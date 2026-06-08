import { CardCode, displayCard, RANKS, SUITS } from "../lib/cards";

type FocusTarget = "hero" | "board";

type Props = {
  hero: CardCode[];
  board: CardCode[];
  focus: FocusTarget;
  onFocusChange: (f: FocusTarget) => void;
  onHeroChange: (cards: CardCode[]) => void;
  onBoardChange: (cards: CardCode[]) => void;
};

const MAX_HERO = 2;
const MAX_BOARD = 5;

export default function CardPicker({
  hero,
  board,
  focus,
  onFocusChange,
  onHeroChange,
  onBoardChange,
}: Props) {
  const used = new Set([...hero, ...board]);

  function toggle(card: CardCode) {
    if (focus === "hero") {
      if (hero.includes(card)) {
        onHeroChange(hero.filter((c) => c !== card));
        return;
      }
      if (board.includes(card)) return;
      if (hero.length >= MAX_HERO) {
        onHeroChange([hero[1], card]);
      } else {
        onHeroChange([...hero, card]);
      }
      if (hero.length + 1 >= MAX_HERO && board.length < MAX_BOARD) {
        onFocusChange("board");
      }
    } else {
      if (board.includes(card)) {
        onBoardChange(board.filter((c) => c !== card));
        return;
      }
      if (hero.includes(card)) return;
      if (board.length >= MAX_BOARD) {
        onBoardChange([...board.slice(1), card]);
      } else {
        onBoardChange([...board, card]);
      }
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 text-sm">
        <button
          type="button"
          onClick={() => onFocusChange("hero")}
          className={`px-3 py-1.5 rounded-md border ${
            focus === "hero"
              ? "border-emerald-500 bg-emerald-900/40 text-emerald-100"
              : "border-slate-600 text-slate-400 hover:border-slate-500"
          }`}
        >
          Your hand {hero.length > 0 ? `(${hero.length}/2)` : ""}
        </button>
        <button
          type="button"
          onClick={() => onFocusChange("board")}
          className={`px-3 py-1.5 rounded-md border ${
            focus === "board"
              ? "border-emerald-500 bg-emerald-900/40 text-emerald-100"
              : "border-slate-600 text-slate-400 hover:border-slate-500"
          }`}
        >
          Board {board.length > 0 ? `(${board.length}/5)` : "(optional)"}
        </button>
      </div>

      <div className="overflow-x-auto">
        <div
          className="inline-grid gap-0.5 min-w-[28rem]"
          style={{ gridTemplateColumns: `repeat(${RANKS.length}, minmax(2rem, 1fr))` }}
        >
          {RANKS.map((r) => (
            <div
              key={`h-${r}`}
              className="text-center text-[10px] font-medium text-slate-500 pb-0.5"
            >
              {r}
            </div>
          ))}
          {SUITS.map((suit) => (
            <div key={suit.id} className="contents">
              {RANKS.map((r) => {
                const code = `${r}${suit.id}` as CardCode;
                const selected = hero.includes(code) || board.includes(code);
                const disabled = used.has(code) && !selected;
                const inHero = hero.includes(code);
                const inBoard = board.includes(code);
                return (
                  <button
                    key={code}
                    type="button"
                    disabled={disabled}
                    onClick={() => toggle(code)}
                    title={`${r} of ${suit.label}`}
                    className={`
                      h-9 rounded text-sm font-semibold transition-all
                      ${disabled ? "opacity-25 cursor-not-allowed bg-slate-800/30" : "hover:scale-105 hover:z-10"}
                      ${selected ? "ring-2 ring-offset-1 ring-offset-slate-900" : "bg-slate-800/80 hover:bg-slate-700"}
                      ${inHero ? "ring-emerald-400 bg-emerald-950/80" : ""}
                      ${inBoard ? "ring-amber-400 bg-amber-950/60" : ""}
                      ${suit.color}
                    `}
                  >
                    {r}
                    <span className="text-xs">{suit.symbol}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Click cards to fill{" "}
        <strong className="text-emerald-400/90">{focus === "hero" ? "your hand" : "the board"}</strong>.
        Selected cards are highlighted; unavailable cards are greyed out.
      </p>
    </div>
  );
}

export function SelectedCardsRow({
  label,
  cards,
  onClear,
  maxSlots,
}: {
  label: string;
  cards: CardCode[];
  onClear: () => void;
  maxSlots: number;
}) {
  const slots = Array.from({ length: maxSlots }, (_, i) => cards[i] ?? null);
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-slate-400 w-28 shrink-0">{label}</span>
      <div className="flex gap-1.5">
        {slots.map((c, i) => (
          <div
            key={i}
            className={`w-12 h-16 rounded-md border flex items-center justify-center text-lg font-bold ${
              c
                ? "border-slate-500 bg-slate-800"
                : "border-dashed border-slate-700 bg-slate-900/40 text-slate-600"
            }`}
          >
            {c ? displayCard(c) : "·"}
          </div>
        ))}
      </div>
      {cards.length > 0 && (
        <button
          type="button"
          onClick={onClear}
          className="text-xs text-slate-500 hover:text-slate-300 underline"
        >
          clear
        </button>
      )}
    </div>
  );
}
