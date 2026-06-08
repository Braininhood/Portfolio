import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Changepoint = {
  detected_at: string;
  description: string;
  confidence: number;
};

const DISMISS_KEY = "poker-ai-dismissed-changepoints";

function dismissId(playerUid: string, detectedAt: string) {
  return `${playerUid}:${detectedAt}`;
}

function loadDismissed(): Set<string> {
  try {
    const raw = localStorage.getItem(DISMISS_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set();
  }
}

function saveDismissed(ids: Set<string>) {
  localStorage.setItem(DISMISS_KEY, JSON.stringify([...ids]));
}

type Props = {
  playerUid: string;
  changepoint: Changepoint | null | undefined;
};

export default function ChangepointBanner({ playerUid, changepoint }: Props) {
  const [hidden, setHidden] = useState(() => {
    if (!changepoint) return true;
    return loadDismissed().has(dismissId(playerUid, changepoint.detected_at));
  });

  useEffect(() => {
    if (!changepoint) {
      setHidden(true);
      return;
    }
    setHidden(loadDismissed().has(dismissId(playerUid, changepoint.detected_at)));
  }, [playerUid, changepoint?.detected_at, changepoint]);

  if (!changepoint || hidden) return null;

  const onDismiss = () => {
    const next = loadDismissed();
    next.add(dismissId(playerUid, changepoint.detected_at));
    saveDismissed(next);
    setHidden(true);
  };

  return (
    <div
      className="rounded-lg border border-amber-700/60 bg-amber-950/40 px-4 py-3 text-sm text-amber-100 mb-4"
      role="alert"
    >
      <p className="font-medium text-amber-200">
        Regime change detected ({changepoint.detected_at})
      </p>
      <p className="mt-1 text-amber-100/90 leading-relaxed">{changepoint.description}</p>
      <p className="mt-1 text-xs text-amber-300/80">
        Possible tilt, fatigue, or strategy shift — exploit policies may want a fresh opponent read.
      </p>
      <div className="flex flex-wrap gap-2 mt-3">
        <button
          type="button"
          onClick={onDismiss}
          className="px-3 py-1 rounded border border-amber-700 text-amber-200 text-xs hover:bg-amber-900/50"
        >
          Dismiss
        </button>
        <Link
          to="/drift"
          className="px-3 py-1 rounded bg-amber-800/60 text-amber-100 text-xs hover:bg-amber-700/60"
        >
          View drift monitor →
        </Link>
      </div>
    </div>
  );
}
