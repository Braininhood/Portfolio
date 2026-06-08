import { touchApiOnline } from "../lib/apiReachability";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

function friendlyFetchError(err: unknown): Error {
  const msg = err instanceof Error ? err.message : String(err);
  if (
    msg === "Failed to fetch" ||
    msg.includes("NetworkError") ||
    msg.includes("ECONNREFUSED") ||
    msg.includes("502") ||
    msg.includes("proxy error")
  ) {
    return new Error(
      "The analysis server is not running. In your terminal: cd to the poker_ai folder, " +
        "activate your environment, then run: python -m poker_ai serve — leave that window open and reload this page.",
    );
  }
  return err instanceof Error ? err : new Error(msg);
}

async function apiError(res: Response): Promise<Error> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as {
      detail?: string | { message?: string; active_job_type?: string };
    };
    if (typeof j.detail === "string") return new Error(j.detail);
    if (j.detail && typeof j.detail === "object" && typeof j.detail.message === "string") {
      return new Error(j.detail.message);
    }
  } catch {
    /* plain text */
  }
  return new Error(text || res.statusText);
}

export async function apiGet<T>(path: string): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw await apiError(res);
    touchApiOnline();
    return res.json() as Promise<T>;
  } catch (e) {
    throw friendlyFetchError(e);
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await apiError(res);
    touchApiOnline();
    return res.json() as Promise<T>;
  } catch (e) {
    throw friendlyFetchError(e);
  }
}

/** Multipart upload (Import page). */
export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
    if (!res.ok) throw await apiError(res);
    touchApiOnline();
    return res.json() as Promise<T>;
  } catch (e) {
    throw friendlyFetchError(e);
  }
}

/** WebSocket URL for job progress (`/ws/jobs/{id}`). */
export function jobWebSocketUrl(jobId: string): string {
  const wsBase = import.meta.env.VITE_WS_BASE_URL;
  if (wsBase) {
    return `${wsBase.replace(/\/$/, "")}/ws/jobs/${jobId}`;
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL;
  if (apiBase) {
    const url = new URL(apiBase);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `/ws/jobs/${jobId}`;
    url.search = "";
    return url.toString();
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/jobs/${jobId}`;
}

/** WebSocket URL for live sim — prefer direct API (avoids Vite ws proxy ECONNABORTED). */
export function simWebSocketUrl(): string {
  const wsBase = import.meta.env.VITE_WS_BASE_URL;
  if (wsBase) {
    return `${wsBase.replace(/\/$/, "")}/ws/sim`;
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL;
  if (apiBase) {
    const url = new URL(apiBase);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/ws/sim";
    url.search = "";
    return url.toString().replace(/\/$/, "");
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/sim`;
}

/** WebSocket URL for interactive play vs AI. */
export function playWebSocketUrl(sessionId: string): string {
  const wsBase = import.meta.env.VITE_WS_BASE_URL;
  if (wsBase) {
    return `${wsBase.replace(/\/$/, "")}/ws/play/${sessionId}`;
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL;
  if (apiBase) {
    const url = new URL(apiBase);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `/ws/play/${sessionId}`;
    url.search = "";
    return url.toString().replace(/\/$/, "");
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/play/${sessionId}`;
}
