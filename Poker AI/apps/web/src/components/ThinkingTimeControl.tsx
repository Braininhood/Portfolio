/** Thinking-time slider + deep-search toggle (W10 Research Item 3 / 1). */

type ThinkingTimeControlProps = {
  thinkingMs: number;
  onThinkingMsChange: (ms: number) => void;
  deepSearch: boolean;
  onDeepSearchChange: (on: boolean) => void;
  compact?: boolean;
};

const MARKS = [0, 50, 200, 500];

export default function ThinkingTimeControl({
  thinkingMs,
  onThinkingMsChange,
  deepSearch,
  onDeepSearchChange,
  compact = false,
}: ThinkingTimeControlProps) {
  const autoDeep = thinkingMs > 200;
  const effectiveDeep = deepSearch || autoDeep;

  return (
    <div className={`space-y-2 ${compact ? "text-sm" : ""}`}>
      <label className="flex flex-col gap-1 text-slate-400 min-w-[200px]">
        <span className="flex justify-between items-center gap-2">
          <span>Thinking time</span>
          <span className="font-mono text-slate-200 tabular-nums">{thinkingMs} ms</span>
        </span>
        <input
          type="range"
          min={0}
          max={500}
          step={10}
          value={thinkingMs}
          onChange={(e) => onThinkingMsChange(Number(e.target.value))}
          className="w-full accent-emerald-500"
          aria-valuemin={0}
          aria-valuemax={500}
          aria-valuenow={thinkingMs}
        />
        <div className="flex justify-between text-[10px] text-slate-600 font-mono px-0.5">
          {MARKS.map((m) => (
            <span key={m}>{m}</span>
          ))}
        </div>
      </label>
      <p className="text-xs text-slate-500 leading-snug">
        Higher values let the AI think longer for better decisions. Latency increases from ~8 ms
        to ~500 ms. Use 0 for instant.
      </p>
      <label className="flex items-center gap-2 text-slate-400 cursor-pointer text-sm">
        <input
          type="checkbox"
          checked={deepSearch}
          onChange={(e) => onDeepSearchChange(e.target.checked)}
          className="rounded"
        />
        Deep search
        {effectiveDeep && (
          <span className="text-sky-400 text-xs">
            {autoDeep && !deepSearch ? "(auto — thinking &gt; 200 ms)" : "(solver blend on)"}
          </span>
        )}
      </label>
      <p className="text-xs text-slate-600">
        Deep search re-runs the postflop solver cache for stronger lines when enabled or thinking
        time exceeds 200 ms.
      </p>
    </div>
  );
}
