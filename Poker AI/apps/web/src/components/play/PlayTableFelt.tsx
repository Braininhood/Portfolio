import { playingCard } from "../../lib/playState";
import type { HeroHandInfo, SeatState } from "../../lib/playTypes";
import { seatPosition } from "../../lib/playTypes";

const CATEGORY_STYLE: Record<string, string> = {
  straight_flush: "text-fuchsia-300 border-fuchsia-500/50 bg-fuchsia-950/40",
  four_of_a_kind: "text-rose-300 border-rose-500/50 bg-rose-950/40",
  full_house: "text-orange-300 border-orange-500/50 bg-orange-950/40",
  flush: "text-sky-300 border-sky-500/50 bg-sky-950/40",
  straight: "text-amber-300 border-amber-500/50 bg-amber-950/40",
  three_of_a_kind: "text-yellow-300 border-yellow-500/50 bg-yellow-950/40",
  two_pair: "text-lime-300 border-lime-500/50 bg-lime-950/40",
  one_pair: "text-emerald-300 border-emerald-500/50 bg-emerald-950/40",
  preflop: "text-slate-300 border-slate-500/50 bg-slate-800/40",
  high_card: "text-slate-400 border-slate-600/50 bg-slate-800/40",
};

function PlayingCardFace({ code, hidden = false }: { code: string; hidden?: boolean }) {
  const c = playingCard(code, hidden);
  if (c.hidden) {
    return (
      <span className="inline-flex h-9 w-7 items-center justify-center rounded border border-slate-500 bg-slate-700 text-[10px] font-bold text-slate-400 shadow">
        ??
      </span>
    );
  }
  return (
    <span
      className={`inline-flex h-9 w-7 items-center justify-center rounded border border-slate-500 bg-white text-xs font-bold shadow ${c.red ? "text-rose-600" : "text-slate-900"}`}
    >
      {c.text}
    </span>
  );
}

function SeatBadge({ label, tone }: { label: string; tone: "btn" | "sb" | "bb" }) {
  const cls =
    tone === "btn"
      ? "bg-amber-500/90 text-slate-900"
      : tone === "sb"
        ? "bg-sky-500/90 text-white"
        : "bg-rose-500/90 text-white";
  return <span className={`text-[9px] font-bold px-1 py-0.5 rounded ${cls}`}>{label}</span>;
}

function SeatPod({
  seat,
  heroCards,
  holeCards,
  revealHoles,
}: {
  seat: SeatState;
  heroCards: string[];
  holeCards: string[] | null;
  revealHoles: boolean;
}) {
  const dim = seat.folded && !revealHoles ? "opacity-40" : seat.folded ? "opacity-70" : "";
  const acting = seat.is_hero ? "ring-2 ring-emerald-400/80" : revealHoles && !seat.folded ? "ring-2 ring-amber-400/50" : "";

  const cardsToShow =
    seat.is_hero && heroCards.length > 0
      ? heroCards
      : revealHoles && holeCards && holeCards.length >= 2
        ? holeCards
        : null;

  return (
    <div
      className={`absolute -translate-x-1/2 -translate-y-1/2 w-[7.5rem] text-center ${dim} ${acting}`}
    >
      <div className="flex justify-center gap-0.5 mb-1 min-h-[2.25rem]">
        {cardsToShow ? (
          cardsToShow.map((c) => <PlayingCardFace key={c} code={c} />)
        ) : !seat.folded ? (
          <>
            <PlayingCardFace code="??" hidden />
            <PlayingCardFace code="??" hidden />
          </>
        ) : null}
      </div>
      <div className="rounded-lg border border-slate-600/80 bg-slate-900/90 px-2 py-1.5 shadow-lg backdrop-blur-sm">
        <p className="text-xs font-medium text-slate-100 truncate">{seat.name}</p>
        <p className="text-[11px] text-emerald-300 font-mono">{seat.total_bb} BB</p>
        {seat.bet_bb > 0 && (
          <p className="text-[10px] text-amber-300 font-mono">bet {seat.bet_bb} BB</p>
        )}
        <div className="flex justify-center gap-1 mt-1 flex-wrap">
          {seat.is_button && <SeatBadge label="BTN" tone="btn" />}
          {seat.is_sb && <SeatBadge label="SB" tone="sb" />}
          {seat.is_bb && <SeatBadge label="BB" tone="bb" />}
          {seat.all_in && <span className="text-[9px] text-rose-300 font-bold">ALL-IN</span>}
          {seat.folded && <span className="text-[9px] text-slate-500">folded</span>}
        </div>
      </div>
    </div>
  );
}

function HeroHandBanner({ heroHand, street }: { heroHand: HeroHandInfo; street: string }) {
  if (!heroHand) return null;
  const style = CATEGORY_STYLE[heroHand.category] ?? CATEGORY_STYLE.high_card;
  const streetLabel = street === "preflop" ? "Preflop" : street.toUpperCase();
  return (
    <div className={`mx-auto max-w-md rounded-lg border px-3 py-2 text-center mb-2 ${style}`}>
      <p className="text-[10px] uppercase tracking-wider opacity-80">{streetLabel} · your best hand</p>
      <p className="text-sm font-semibold">{heroHand.name}</p>
    </div>
  );
}

export default function PlayTableFelt({
  seats,
  heroSeat,
  heroCards,
  heroHand,
  board,
  potBb,
  street,
  showdownBySeat,
}: {
  seats: SeatState[];
  heroSeat: number;
  heroCards: string[];
  heroHand: HeroHandInfo;
  board: string;
  potBb: number;
  street: string;
  /** When set, flip villain hole cards on the felt (showdown). */
  showdownBySeat?: Record<number, string[]>;
}) {
  const totalSeats = seats.length || 2;
  const boardCards = board ? board.split(/\s+/).filter(Boolean) : [];
  const atShowdown = Boolean(showdownBySeat && Object.keys(showdownBySeat).length > 0);

  return (
    <div>
      {atShowdown && (
        <p className="text-center text-xs uppercase tracking-widest text-amber-400/90 mb-2 font-semibold">
          Showdown
        </p>
      )}
      <HeroHandBanner heroHand={heroHand} street={street} />
      <div className="relative mx-auto w-full max-w-3xl aspect-[4/3] min-h-[320px]">
        <div className="absolute inset-0 rounded-[999px] border-4 border-emerald-900/60 bg-gradient-to-b from-emerald-900/40 via-emerald-950/60 to-emerald-950/80 shadow-inner" />
        <div className="absolute inset-[8%] rounded-[999px] border border-emerald-700/30" />

        <div className="absolute left-1/2 top-[42%] -translate-x-1/2 -translate-y-1/2 text-center z-10">
          <div className="flex justify-center gap-1.5 mb-2 min-h-[2.5rem]">
            {boardCards.length > 0 ? (
              boardCards.map((c) => <PlayingCardFace key={c} code={c} />)
            ) : (
              <span className="text-xs text-emerald-600/80 uppercase tracking-widest">{street}</span>
            )}
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-black/40 px-4 py-1.5 border border-emerald-700/40">
            <span className="text-xs text-slate-400">Pot</span>
            <span className="text-lg font-bold text-amber-300 font-mono">{potBb} BB</span>
          </div>
        </div>

        {seats.map((seat) => {
          const pos = seatPosition(seat.seat, totalSeats, heroSeat);
          const holeCards = showdownBySeat?.[seat.seat] ?? null;
          return (
            <div key={seat.seat} className="absolute z-20" style={{ left: pos.left, top: pos.top }}>
              <SeatPod
                seat={seat}
                heroCards={heroCards}
                holeCards={holeCards}
                revealHoles={atShowdown}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
