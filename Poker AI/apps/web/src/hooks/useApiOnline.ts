import { useEffect, useRef, useState } from "react";
import { API_BASE } from "../api/client";
import { isRecentlyOnline } from "../lib/apiReachability";

/**
 * True when the local API responds.
 * Uses consecutive failures before marking offline — a single slow /health during
 * folder scan or ingest must not show a false "server not running" banner.
 */
export function useApiOnline(pollMs = 10_000) {
  const [online, setOnline] = useState<boolean | null>(null);
  const failStreak = useRef(0);

  useEffect(() => {
    let cancelled = false;

    const probe = async (): Promise<boolean> => {
      const ctrl = new AbortController();
      const t = window.setTimeout(() => ctrl.abort(), 5_000);
      try {
        const res = await fetch(`${API_BASE}/health`, { signal: ctrl.signal });
        return res.ok;
      } catch {
        return false;
      } finally {
        clearTimeout(t);
      }
    };

    const check = async () => {
      const ok = await probe();
      if (cancelled) return;
      if (ok) {
        failStreak.current = 0;
        setOnline(true);
        return;
      }
      if (isRecentlyOnline()) {
        setOnline(true);
        return;
      }
      failStreak.current += 1;
      if (failStreak.current >= 3) {
        setOnline(false);
      }
    };

    void check();
    const id = window.setInterval(() => void check(), pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [pollMs]);

  return online;
}
