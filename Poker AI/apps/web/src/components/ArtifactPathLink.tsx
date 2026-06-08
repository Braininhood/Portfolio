import { useState } from "react";
import { openProjectPath } from "../lib/openArtifact";

type Props = {
  path: string;
  label?: string;
  className?: string;
};

/** Clickable path — opens in Windows Explorer / macOS Finder via local API. */
export default function ArtifactPathLink({ path, label, className }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const display = label ?? path.split(/[/\\]/).pop() ?? path;

  async function handleClick() {
    setBusy(true);
    setErr(null);
    try {
      await openProjectPath(path);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className={className}>
      <button
        type="button"
        onClick={() => void handleClick()}
        disabled={busy}
        title={path}
        className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2 disabled:opacity-50 font-mono text-xs"
      >
        {busy ? "Opening…" : display}
      </button>
      {err && <span className="text-red-400 text-xs ml-1">({err})</span>}
    </span>
  );
}
