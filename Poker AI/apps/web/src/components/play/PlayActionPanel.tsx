import type { ActionLogEntry, HandHistoryRow, HandRecord, HeroHandInfo } from "../../lib/playTypes";

function ActionLine({ e }: { e: ActionLogEntry }) {
  return (
    <li className={`text-xs leading-relaxed ${e.is_all_in ? "text-rose-300" : ""}`}>
      <span className="text-slate-500 uppercase w-14 inline-block">{e.street}</span>
      <span className={e.seat === 0 ? "text-emerald-300" : "text-slate-300"}>{e.label}</span>
      <span className="text-slate-600 ml-1">· pot {e.pot_bb} BB</span>
    </li>
  );
}

function HandStudyDetail({ hand }: { hand: HandRecord }) {
  return (
    <div className="space-y-3 text-xs">
      <div className="rounded border border-slate-600 bg-slate-800/50 p-2">
        <p className="text-slate-300">
          Hero: <span className="font-mono text-slate-100">{hand.hero_cards ?? "—"}</span>
          {hand.hero_hand?.name ? <span className="text-emerald-400 ml-2">→ {hand.hero_hand.name}</span> : null}
        </p>
        {hand.board ? <p className="text-slate-400 mt-1">Board: <span className="font-mono">{hand.board}</span></p> : null}
        {(hand.all_in_count ?? 0) > 0 && (
          <p className="text-rose-300 mt-1">{hand.all_in_count} all-in action(s) this hand</p>
        )}
      </div>
      {hand.winner && (
        <div className="rounded border border-emerald-700/50 bg-emerald-950/30 p-2">
          <p className="text-emerald-300 font-medium">Winner: {hand.winner.name}</p>
          <p className="text-slate-300 mt-1 font-mono">{hand.winner.cards?.join(" ")}</p>
          <p className="text-slate-400 mt-1">{hand.winner.hand_rank}</p>
        </div>
      )}
      {hand.showdown.length > 0 && (
        <ul className="space-y-1">
          {hand.showdown.map((s) => (
            <li key={s.seat} className={s.won ? "text-emerald-400" : "text-slate-400"}>
              {s.name}: {s.cards.join(" ")} — {s.hand_rank}
            </li>
          ))}
        </ul>
      )}
      <ol className="space-y-0.5 max-h-40 overflow-y-auto border-t border-slate-700 pt-2">
        {[...hand.action_log].reverse().map((e, i) => (
          <ActionLine key={`${hand.hand_no}-${i}`} e={e} />
        ))}
      </ol>
    </div>
  );
}

export default function PlayActionPanel({
  handLog,
  sessionLog,
  history,
  sessionStats,
  studyHands,
  selectedStudyHand,
  onSelectStudyHand,
  heroHand,
}: {
  handLog: ActionLogEntry[];
  sessionLog: ActionLogEntry[];
  history: HandHistoryRow[];
  sessionStats: { hands: number; net_bb: number; vpip_pct: number; pfr_pct: number };
  studyHands: HandRecord[];
  selectedStudyHand: number | null;
  onSelectStudyHand: (handNo: number | null) => void;
  heroHand: HeroHandInfo;
}) {
  const handLogSorted = [...handLog].reverse();
  const selected = studyHands.find((h) => h.hand_no === selectedStudyHand) ?? null;
  const tab = selectedStudyHand === null ? "live" : "study";

  return (
    <div className="space-y-3">
      <div className="flex gap-1 border-b border-slate-700 pb-2">
        <button
          type="button"
          className={`text-xs px-2 py-1 rounded ${tab === "live" ? "bg-emerald-700 text-white" : "text-slate-400 hover:bg-slate-800"}`}
          onClick={() => onSelectStudyHand(null)}
        >
          Live
        </button>
        {studyHands.map((h) => (
          <button
            key={h.hand_no}
            type="button"
            title={`${h.result_bb >= 0 ? "+" : ""}${h.result_bb} BB`}
            className={`text-xs px-2 py-1 rounded font-mono ${selectedStudyHand === h.hand_no ? "bg-sky-700 text-white" : "text-slate-400 hover:bg-slate-800"}`}
            onClick={() => onSelectStudyHand(h.hand_no)}
          >
            #{h.hand_no}
          </button>
        ))}
      </div>

      {heroHand && tab === "live" && (
        <div className="rounded-lg border border-emerald-700/40 bg-emerald-950/30 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-emerald-500/80">Your hand</p>
          <p className="text-sm font-medium text-emerald-200">{heroHand.name}</p>
        </div>
      )}

      <section className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
        <h3 className="text-sm font-medium text-slate-200 mb-2">Session</h3>
        <p className={`text-lg font-mono font-semibold ${sessionStats.net_bb >= 0 ? "text-emerald-400" : "text-red-400"}`}>
          {sessionStats.net_bb >= 0 ? "+" : ""}
          {sessionStats.net_bb} BB
        </p>
        <p className="text-xs text-slate-400 mt-1">
          {sessionStats.hands} hands · VPIP {sessionStats.vpip_pct}% · PFR {sessionStats.pfr_pct}%
        </p>
      </section>

      {tab === "study" && selected ? (
        <section className="rounded-lg border border-sky-700/40 bg-slate-900/60 p-3">
          <h3 className="text-sm font-medium text-sky-200 mb-2">
            Study hand #{selected.hand_no}{" "}
            <span className={selected.result_bb >= 0 ? "text-emerald-400" : "text-red-400"}>
              ({selected.result_bb >= 0 ? "+" : ""}
              {selected.result_bb} BB)
            </span>
          </h3>
          <HandStudyDetail hand={selected} />
        </section>
      ) : (
        <>
          <section className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
            <h3 className="text-sm font-medium text-slate-200 mb-2">This hand — action log</h3>
            {handLogSorted.length === 0 ? (
              <p className="text-xs text-slate-500">Waiting for action…</p>
            ) : (
              <ol className="space-y-1 max-h-52 overflow-y-auto">
                {handLogSorted.map((e, i) => (
                  <ActionLine key={`${e.hand_no}-${e.street}-${e.seat}-${i}`} e={e} />
                ))}
              </ol>
            )}
          </section>

          <section className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
            <h3 className="text-sm font-medium text-slate-200 mb-2">Completed hands</h3>
            {history.length === 0 ? (
              <p className="text-xs text-slate-500">No completed hands yet.</p>
            ) : (
              <ul className="space-y-1 max-h-48 overflow-y-auto text-xs">
                {history.map((h) => (
                  <li key={h.hand_no}>
                    <button
                      type="button"
                      className={`text-left w-full hover:underline ${h.result_bb >= 0 ? "text-emerald-400" : "text-red-400"}`}
                      onClick={() => onSelectStudyHand(h.hand_no)}
                    >
                      #{h.hand_no} {h.ending_street}
                      {h.went_showdown ? " · SD" : ""}
                      {h.hero_hand_name ? ` · ${h.hero_hand_name}` : ""}
                      {h.winner_name ? ` · won: ${h.winner_name}` : ""}
                      {(h.all_in_count ?? 0) > 0 ? ` · ${h.all_in_count} AI` : ""} — {h.result_bb >= 0 ? "+" : ""}
                      {h.result_bb} BB
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {tab === "live" && sessionLog.length > 0 && (
        <section className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
          <p className="text-[10px] text-slate-500">
            Saved to DB for AI study — hero decisions counted toward NN training pool.
          </p>
        </section>
      )}
    </div>
  );
}
