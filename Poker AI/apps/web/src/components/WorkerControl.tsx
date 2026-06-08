type WorkerInfo = {
  recommended: number;
  max_safe: number;
  current_env: number;
  explanation: string;
  by_task?: Record<string, number>;
};

type Props = {
  value: number;
  onChange: (n: number) => void;
  workers: WorkerInfo | null;
  taskHint?: string;
  disabled?: boolean;
  note?: string;
};

type WorkerPreset = { label: string; value: number };

const PRESETS: WorkerPreset[] = [
  { label: "Auto", value: 0 },
  { label: "1", value: 1 },
  { label: "2", value: 2 },
  { label: "4", value: 4 },
  { label: "8", value: 8 },
];

export default function WorkerControl({
  value,
  onChange,
  workers,
  taskHint,
  disabled,
  note,
}: Props) {
  const maxSafe = workers?.max_safe ?? 8;
  const recommended = taskHint && workers?.by_task?.[taskHint]
    ? workers.by_task[taskHint]
    : workers?.recommended ?? 4;

  const buttons = [...PRESETS];
  if (maxSafe > 8 && !buttons.some((b) => b.value === maxSafe)) {
    buttons.push({ label: String(maxSafe), value: maxSafe });
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-300">CPU workers</span>
        {buttons.map((p) => (
          <button
            key={p.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(p.value)}
            className={`px-3 py-1 text-sm rounded-md border disabled:opacity-50 ${
              value === p.value
                ? "border-emerald-500 bg-emerald-900/40 text-emerald-100"
                : "border-slate-600 text-slate-300 hover:border-slate-500"
            }`}
          >
            {p.label}
          </button>
        ))}
        <span className="text-xs text-slate-500">
          {value === 0 ? `Auto ≈ ${recommended} on this PC` : `Using ${value} worker(s)`}
        </span>
      </div>
      {workers?.explanation && (
        <p className="text-xs text-slate-500 leading-relaxed">{workers.explanation}</p>
      )}
      {note && <p className="text-xs text-amber-200/80">{note}</p>}
    </div>
  );
}
