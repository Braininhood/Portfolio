/**
 * HealthCheckPage — full-screen first-load system check.
 *
 * Behaviour:
 *  - If cache is fresh and all_passed → shows "All good" for 1 s then redirects to /
 *  - If no cache or has warnings/fails → shows animated check results
 *  - "Continue to app" button is always visible after checks complete
 *  - Each warn/fail item has an expandable advice panel with OS-specific fix command
 */

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  HealthCheckItem,
  useHealthCheck,
} from "../hooks/useHealthCheck";
import { API_BASE } from "../api/client";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function SpinnerIcon() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-slate-400"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  );
}

function PassIcon() {
  return (
    <svg className="h-5 w-5 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function WarnIcon() {
  return (
    <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function FailIcon() {
  return (
    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function PendingIcon() {
  return <span className="h-5 w-5 rounded-full border-2 border-slate-600 inline-block" />;
}

// ---------------------------------------------------------------------------
// Single check row
// ---------------------------------------------------------------------------

function fixForPlatform(item: HealthCheckItem, platform: string): string | null {
  if (platform === "win32") return item.fix_windows;
  if (platform === "darwin") return item.fix_macos;
  return item.fix_linux;
}

type InstallPhase = "idle" | "running" | "done" | "error";

function CheckRow({
  item,
  visible,
  platform,
  onInstallDone,
}: {
  item: HealthCheckItem;
  visible: boolean;
  platform: string;
  onInstallDone?: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [installPhase, setInstallPhase] = useState<InstallPhase>("idle");
  const [installLog, setInstallLog] = useState<string[]>([]);
  const logRef = useRef<HTMLPreElement>(null);
  const fix = fixForPlatform(item, platform);

  const statusIcon =
    installPhase === "done" ? (
      <PassIcon />
    ) : item.status === "pass" ? (
      <PassIcon />
    ) : item.status === "warn" ? (
      <WarnIcon />
    ) : (
      <FailIcon />
    );

  const rowBg =
    installPhase === "done"
      ? ""
      : item.status === "pass"
        ? ""
        : item.status === "warn"
          ? "border-amber-800/30 bg-amber-900/10"
          : "border-red-800/30 bg-red-900/10";

  async function copyFix() {
    if (!fix) return;
    try {
      await navigator.clipboard.writeText(fix);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  async function startInstall() {
    setInstallPhase("running");
    setInstallLog([]);
    if (!expanded) setExpanded(true);

    try {
      const res = await fetch(`${API_BASE}/texas/install`, { method: "POST" });
      if (!res.ok || !res.body) {
        setInstallLog((l) => [...l, `✗ Server returned ${res.status}`]);
        setInstallPhase("error");
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        // Parse SSE lines: "data: ...\n\n"
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          for (const rawLine of part.split("\n")) {
            const line = rawLine.trim();
            if (line.startsWith("event: done")) {
              setInstallPhase("done");
              onInstallDone?.();
            } else if (line.startsWith("event: error")) {
              setInstallPhase("error");
            } else if (line.startsWith("data: ")) {
              const text = line.slice(6);
              if (text) setInstallLog((l) => [...l, text]);
            }
          }
        }
      }
    } catch (e) {
      setInstallLog((l) => [...l, `✗ ${e instanceof Error ? e.message : String(e)}`]);
      setInstallPhase("error");
    }
  }

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [installLog]);

  if (!visible) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-slate-700/50">
        <PendingIcon />
        <span className="text-slate-500 text-sm">{item.name}</span>
      </div>
    );
  }

  const showInstallButton =
    item.can_auto_install && item.status !== "pass" && installPhase === "idle";

  return (
    <div
      className={`rounded-lg border border-slate-700/50 ${rowBg} transition-all duration-300`}
    >
      <button
        type="button"
        onClick={() => item.advice && setExpanded((e) => !e)}
        className={`w-full flex items-center gap-3 px-4 py-3 text-left ${item.advice ? "cursor-pointer hover:bg-white/5" : "cursor-default"}`}
      >
        <span className="shrink-0">{statusIcon}</span>
        <span className="flex-1 text-sm font-medium text-slate-200">{item.name}</span>
        <span className="text-sm text-slate-400 font-mono">
          {installPhase === "done" ? "Installed ✓" : item.value}
        </span>
        {item.advice && (
          <span className="text-xs text-slate-500 ml-2">{expanded ? "▲" : "▼"}</span>
        )}
      </button>

      {expanded && item.advice && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-700/50 pt-3">
          <p className="text-sm text-slate-300">{item.advice}</p>

          {/* Auto-install button */}
          {showInstallButton && (
            <button
              type="button"
              onClick={() => void startInstall()}
              className="flex items-center gap-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors"
            >
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 3a.75.75 0 01.75.75v8.69l2.22-2.22a.75.75 0 111.06 1.06l-3.5 3.5a.75.75 0 01-1.06 0l-3.5-3.5a.75.75 0 111.06-1.06l2.22 2.22V3.75A.75.75 0 0110 3zM3.75 15a.75.75 0 000 1.5h12.5a.75.75 0 000-1.5H3.75z"
                  clipRule="evenodd"
                />
              </svg>
              Install TexasSolver automatically
            </button>
          )}

          {/* Live install log */}
          {installPhase !== "idle" && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                {installPhase === "running" && <SpinnerIcon />}
                {installPhase === "done" && <PassIcon />}
                {installPhase === "error" && <FailIcon />}
                <span className="text-xs text-slate-400 font-mono">
                  {installPhase === "running"
                    ? "Installing…"
                    : installPhase === "done"
                      ? "Installation complete"
                      : "Installation failed"}
                </span>
              </div>
              <pre
                ref={logRef}
                className="text-xs font-mono bg-slate-950 border border-slate-700 rounded-md p-3 overflow-x-auto overflow-y-auto max-h-48 text-slate-300 whitespace-pre-wrap"
              >
                {installLog.join("\n") || " "}
              </pre>
            </div>
          )}

          {/* Manual fix commands (shown when not installing) */}
          {fix && installPhase === "idle" && (
            <div className="relative">
              <pre className="text-xs font-mono bg-slate-950 border border-slate-700 rounded-md p-3 overflow-x-auto text-slate-300 whitespace-pre-wrap">
                {fix}
              </pre>
              <button
                type="button"
                onClick={() => void copyFix()}
                className="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          )}

          {item.can_skip && item.status !== "fail" && installPhase !== "done" && (
            <p className="text-xs text-slate-500 italic">
              This item is optional — you can continue to the app without fixing it.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type RevealPhase = "loading" | "revealing" | "done" | "countdown" | "fast";

export default function HealthCheckPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Only auto-redirect when the first-load guard sent the user here (?auto=1).
  // Manual visits (clicking "System") should always stay on the page.
  const autoMode = searchParams.get("auto") === "1";
  const { status, result, cachedAt, fromCache, error, recheck } = useHealthCheck();
  const [revealCount, setRevealCount] = useState(0);
  const [phase, setPhase] = useState<RevealPhase>("loading");
  const [countdown, setCountdown] = useState(3);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Once data arrives, reveal items one by one
  useEffect(() => {
    if (status !== "done" || !result) return;

    if (fromCache && result.all_passed && autoMode) {
      // Cache hit + all good + sent here automatically → fast mode: show briefly then go
      setPhase("fast");
      setRevealCount(result.checks.length);
      timerRef.current = setTimeout(() => void navigate("/"), 1200);
      return;
    }

    setPhase("revealing");
    let i = 0;
    const total = result.checks.length;
    const tick = () => {
      i += 1;
      setRevealCount(i);
      if (i < total) {
        timerRef.current = setTimeout(tick, 250);
      } else {
        setPhase("done");
        if (result.all_passed && autoMode) {
          setPhase("countdown");
        }
      }
    };
    timerRef.current = setTimeout(tick, 300);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [status, result, fromCache, navigate]);

  // Countdown timer — only runs in auto mode
  useEffect(() => {
    if (phase !== "countdown" || !autoMode) return;
    if (countdown <= 0) {
      void navigate("/");
      return;
    }
    timerRef.current = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [phase, countdown, navigate]);

  const platform = result?.os_platform ?? "win32";

  const overallIcon =
    !result ? null : result.all_passed ? (
      <PassIcon />
    ) : result.has_warnings ? (
      <WarnIcon />
    ) : (
      <FailIcon />
    );

  const overallLabel = !result
    ? "Checking your system…"
    : result.all_passed
      ? phase === "fast"
        ? "All good — resuming…"
        : phase === "countdown"
          ? `All checks passed — continuing in ${countdown}s`
          : "All checks passed"
      : result.checks.some((c) => c.status === "fail")
        ? "Action required — see items below"
        : "Ready with warnings — see items below";

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-emerald-400">Poker AI</h1>
          <p className="text-slate-400 text-sm">System health check</p>
        </div>

        {/* Status summary */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl border border-slate-700 bg-slate-900">
          {status === "loading" || phase === "revealing" ? (
            <SpinnerIcon />
          ) : (
            overallIcon
          )}
          <span
            className={`text-sm font-medium ${
              !result
                ? "text-slate-400"
                : result.all_passed
                  ? "text-emerald-300"
                  : result.checks.some((c) => c.status === "fail")
                    ? "text-red-300"
                    : "text-amber-300"
            }`}
          >
            {status === "error" ? `Error: ${error ?? "unknown"}` : overallLabel}
          </span>
          {fromCache && cachedAt && (
            <span className="ml-auto text-xs text-slate-600">
              cached {Math.round((Date.now() - cachedAt.getTime()) / 60000)} min ago
            </span>
          )}
        </div>

        {/* Check items */}
        {result && (
          <div className="space-y-2">
            {result.checks.map((item, idx) => (
              <CheckRow
                key={item.id}
                item={item}
                visible={idx < revealCount}
                platform={platform}
                onInstallDone={() => {
                  setRevealCount(0);
                  setPhase("loading");
                  setCountdown(3);
                  recheck();
                }}
              />
            ))}
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div className="rounded-lg border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">Could not reach the API server.</p>
            <p className="mt-1 text-red-400 text-xs">
              Make sure <code className="font-mono">poker_ai serve</code> is running
              in a terminal, then click Re-run checks.
            </p>
          </div>
        )}

        {/* Diagnostics (v2) */}
        {(phase === "done" || phase === "countdown") && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/40 px-4 py-3 text-sm">
            <p className="text-slate-300 font-medium">Optional: policy speed test</p>
            <p className="mt-1 text-slate-400 text-xs">
              Measures how fast the AI decides (p99 latency). Target under 30 ms for smooth play.
            </p>
            <Link
              to="/jobs?task=policy_bench&preset=recommended"
              className="inline-block mt-2 text-emerald-400 hover:text-emerald-300 text-xs font-medium"
            >
              Run policy speed test in Tasks →
            </Link>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          {/* Always show "Go to app" once checks are done */}
          {(phase === "done" || phase === "countdown") && (
            <button
              type="button"
              onClick={() => void navigate("/")}
              className="flex-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white transition-colors"
            >
              {phase === "countdown"
                ? `Continue to app (${countdown})`
                : "Continue to app →"}
            </button>
          )}

          {/* Re-run */}
          {(status === "done" || status === "error") && (
            <button
              type="button"
              onClick={() => {
                setRevealCount(0);
                setPhase("loading");
                setCountdown(3);
                recheck();
              }}
              className="rounded-lg border border-slate-600 hover:border-slate-500 px-4 py-2.5 text-sm text-slate-300 transition-colors"
            >
              Re-run checks
            </button>
          )}
        </div>

        {/* OS note */}
        {result && (
          <p className="text-center text-xs text-slate-600">
            {result.os_name} · Fix commands shown for your OS
          </p>
        )}
      </div>
    </div>
  );
}
