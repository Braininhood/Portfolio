/**
 * useHealthCheck — fetches /health/check and caches result in localStorage.
 *
 * Cache rules:
 *   - If last check was < CACHE_DURATION_MS ago AND all_passed → use cache (skip network call)
 *   - If last check had warnings/failures → always re-run on next mount
 *   - Manual re-run: call `recheck()`
 */

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "../api/client";

const CACHE_KEY = "pokerAI_healthCheck_v1";
const CACHE_DURATION_MS = 30 * 60 * 1000; // 30 minutes

export type CheckStatus = "pass" | "warn" | "fail";
export type LoadStatus = "idle" | "loading" | "done" | "error";

export interface HealthCheckItem {
  id: string;
  name: string;
  status: CheckStatus;
  value: string;
  advice: string | null;
  fix_windows: string | null;
  fix_linux: string | null;
  fix_macos: string | null;
  can_skip: boolean;
  can_auto_install: boolean;
  docs_section: string | null;
}

export interface HealthCheckResult {
  os_name: string;
  os_platform: string; // "win32" | "linux" | "darwin"
  all_passed: boolean;
  has_warnings: boolean;
  checks: HealthCheckItem[];
}

interface CachedResult {
  timestamp: number;
  result: HealthCheckResult;
}

function readCache(): CachedResult | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CachedResult;
  } catch {
    return null;
  }
}

function writeCache(result: HealthCheckResult): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ timestamp: Date.now(), result }));
  } catch {
    /* storage full or unavailable — ignore */
  }
}

function isCacheValid(cached: CachedResult): boolean {
  const age = Date.now() - cached.timestamp;
  return age < CACHE_DURATION_MS && cached.result.all_passed;
}

export function clearHealthCache(): void {
  try {
    localStorage.removeItem(CACHE_KEY);
  } catch {
    /* ignore */
  }
}

export function getCachedHealthResult(): HealthCheckResult | null {
  const cached = readCache();
  if (cached && isCacheValid(cached)) return cached.result;
  return null;
}

// ---------------------------------------------------------------------------

interface UseHealthCheckReturn {
  status: LoadStatus;
  result: HealthCheckResult | null;
  cachedAt: Date | null;       // when the cached result was saved
  fromCache: boolean;
  error: string | null;
  recheck: () => void;
}

export function useHealthCheck(opts?: { skip?: boolean }): UseHealthCheckReturn {
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [result, setResult] = useState<HealthCheckResult | null>(null);
  const [fromCache, setFromCache] = useState(false);
  const [cachedAt, setCachedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runCount, setRunCount] = useState(0);

  const run = useCallback(async (forceRefresh = false) => {
    if (opts?.skip) return;

    // Check cache first (unless forced)
    if (!forceRefresh) {
      const cached = readCache();
      if (cached && isCacheValid(cached)) {
        setResult(cached.result);
        setFromCache(true);
        setCachedAt(new Date(cached.timestamp));
        setStatus("done");
        return;
      }
    }

    setStatus("loading");
    setFromCache(false);
    setError(null);

    try {
      const data = await apiGet<HealthCheckResult>("/health/check");
      writeCache(data);
      setResult(data);
      setCachedAt(new Date());
      setStatus("done");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setStatus("error");
    }
  }, [opts?.skip]);

  useEffect(() => {
    void run(false);
  }, [run, runCount]);

  const recheck = useCallback(() => {
    clearHealthCache();
    setRunCount((n) => n + 1);
    void run(true);
  }, [run]);

  return { status, result, cachedAt, fromCache, error, recheck };
}
