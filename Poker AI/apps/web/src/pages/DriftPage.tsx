import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { apiGet, apiPost } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import { Card } from "../components/Card";
import {
  CHANGEPOINT_ADVICE,
  CHANGEPOINT_INTRO,
  DRIFT_ACTION_STEPS,
  DRIFT_INTRO,
  DRIFT_STATUS_HELP,
} from "../lib/driftHelp";

type DriftReport = {
  date: string;
  filename: string;
  features_flagged: number;
  status: string;
  created_at: string;
};

type DriftList = {
  reports: DriftReport[];
  latest_status: string | null;
};

type DriftFeatureRow = {
  feature: string;
  label: string;
  meaning: string;
  shift?: number | null;
  ref_mean?: number | null;
  cur_mean?: number | null;
  flagged: boolean;
  counts_toward_status: boolean;
  advice?: string | null;
  note?: string | null;
};

type DriftDetail = {
  date: string;
  status: string;
  poker_features_flagged: number;
  hands_compared: number;
  summary_advice: string;
  method: string;
  features: DriftFeatureRow[];
};

type Changepoint = {
  player_uid: string;
  display_name: string;
  detected_at: string;
  description: string;
  confidence: number;
};

function statusDot(status: string | null) {
  if (status === "green") return "bg-emerald-500";
  if (status === "yellow") return "bg-amber-400";
  if (status === "red") return "bg-red-500";
  return "bg-slate-500";
}

function StatusAdvice({ status }: { status: string }) {
  const help = DRIFT_STATUS_HELP[status] ?? DRIFT_STATUS_HELP.yellow;
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm mb-4 ${
        status === "green"
          ? "border-emerald-800/50 bg-emerald-950/30 text-emerald-100"
          : status === "red"
            ? "border-red-800/50 bg-red-950/30 text-red-100"
            : "border-amber-800/50 bg-amber-950/30 text-amber-100"
      }`}
    >
      <p className="font-medium">{help.title}</p>
      <p className="mt-1 opacity-90 leading-relaxed">{help.body}</p>
    </div>
  );
}

export default function DriftPage() {
  const qc = useQueryClient();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const { data, error, isLoading } = useQuery({
    queryKey: ["drift-reports"],
    queryFn: () => apiGet<DriftList>("/drift/reports"),
    retry: false,
  });

  const { data: detail } = useQuery({
    queryKey: ["drift-detail", selectedDate],
    queryFn: () => apiGet<DriftDetail>(`/drift/reports/${selectedDate}/detail`),
    enabled: selectedDate !== null,
    retry: false,
  });

  const { data: changepoints } = useQuery({
    queryKey: ["drift-changepoints"],
    queryFn: () => apiGet<{ alerts: Changepoint[] }>("/drift/changepoints?refresh=false"),
    retry: false,
  });

  const runDrift = useMutation({
    mutationFn: () => apiPost<DriftReport>("/drift/run", {}),
    onSuccess: (r) => {
      setSelectedDate(r.date);
      void qc.invalidateQueries({ queryKey: ["drift-reports"] });
      void qc.invalidateQueries({ queryKey: ["drift-detail", r.date] });
    },
  });

  const refreshChangepoints = useMutation({
    mutationFn: () => apiGet<{ alerts: Changepoint[] }>("/drift/changepoints?refresh=true"),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["drift-changepoints"] }),
  });

  const latestStatus = data?.latest_status ?? detail?.status ?? null;

  return (
    <div className="space-y-4">
      <ApiOfflineBanner />

      <Card title="What this page does">
        <p className="text-slate-300 text-sm leading-relaxed">{DRIFT_INTRO.body}</p>
        <ul className="mt-3 text-xs text-slate-500 space-y-1 list-disc list-inside">
          <li>
            <strong className="text-slate-400">Drift</strong> = training data mix (features.jsonl)
          </li>
          <li>
            <strong className="text-slate-400">Changepoints</strong> = Play vs AI bot style changes
          </li>
          <li>Hand ID is never used for green / yellow / red</li>
        </ul>
      </Card>

      <Card title="Drift monitor">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span
            className={`inline-block h-3 w-3 rounded-full ${statusDot(latestStatus)}`}
            title={latestStatus ?? "unknown"}
          />
          <span className="text-slate-300 text-sm">
            {latestStatus
              ? `Overall: ${latestStatus.toUpperCase()}`
              : "No reports yet — run a drift check"}
          </span>
          <button
            type="button"
            disabled={runDrift.isPending}
            onClick={() => runDrift.mutate()}
            className="ml-auto px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 text-sm text-white disabled:opacity-50"
          >
            {runDrift.isPending ? "Running…" : "Run drift check now"}
          </button>
        </div>
        {isLoading && <p className="text-slate-500 text-sm">Loading…</p>}
        {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}
        {data && (
          <ul className="divide-y divide-slate-800 border border-slate-700 rounded-md text-sm">
            {data.reports.length === 0 && (
              <li className="px-4 py-3 text-slate-500">
                No reports yet. Run Prepare hands on Setup, then click Run drift check.
              </li>
            )}
            {data.reports.map((r) => (
              <li key={r.filename} className="px-4 py-2 flex justify-between items-center">
                <button
                  type="button"
                  className="text-left hover:text-emerald-300"
                  onClick={() => setSelectedDate(r.date)}
                >
                  {r.date} — {r.features_flagged} poker feature(s) flagged
                </button>
                <span className={r.status === "green" ? "text-emerald-400" : "text-amber-400"}>
                  {r.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {selectedDate && detail && (
        <Card title={`Report ${selectedDate}`}>
          <StatusAdvice status={detail.status} />
          {detail.summary_advice && (
            <p className="text-slate-300 text-sm mb-4 leading-relaxed">{detail.summary_advice}</p>
          )}
          {detail.hands_compared > 0 && (
            <p className="text-xs text-slate-500 mb-4">
              Compared older vs newer halves of {detail.hands_compared.toLocaleString()} prepared
              hands. {detail.method}
            </p>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border border-slate-700 rounded-md">
              <thead className="bg-slate-800/80 text-slate-400 text-left">
                <tr>
                  <th className="px-3 py-2">Feature</th>
                  <th className="px-3 py-2">Older avg</th>
                  <th className="px-3 py-2">Newer avg</th>
                  <th className="px-3 py-2">Shift</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {detail.features.map((f) => (
                  <tr
                    key={f.feature}
                    className={f.flagged ? "bg-amber-950/20" : ""}
                  >
                    <td className="px-3 py-2 align-top">
                      <div className="font-medium text-slate-200">{f.label}</div>
                      <div className="text-xs text-slate-500 mt-1 max-w-md">{f.meaning}</div>
                      {f.advice && (
                        <div className="text-xs text-amber-200/90 mt-2">{f.advice}</div>
                      )}
                      {f.note && (
                        <div className="text-xs text-slate-600 mt-1 italic">{f.note}</div>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-400">{f.ref_mean ?? "—"}</td>
                    <td className="px-3 py-2 text-slate-400">{f.cur_mean ?? "—"}</td>
                    <td className="px-3 py-2 text-slate-300">{f.shift ?? "—"}</td>
                    <td className="px-3 py-2 text-xs">
                      {f.flagged ? (
                        <span className="text-amber-400">Flagged</span>
                      ) : f.counts_toward_status ? (
                        <span className="text-emerald-500">OK</span>
                      ) : (
                        <span className="text-slate-500">Info only</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(detail.status === "yellow" || detail.status === "red") && (
            <div className="mt-4 border-t border-slate-700 pt-4">
              <p className="text-slate-400 text-sm font-medium mb-2">What to do next</p>
              <ol className="text-sm text-slate-300 space-y-2 list-decimal list-inside">
                {DRIFT_ACTION_STEPS.map((s) => (
                  <li key={s.step}>
                    <Link to={s.path} className="text-emerald-400 hover:underline">
                      {s.step}
                    </Link>
                    {" — "}
                    {s.text}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </Card>
      )}

      <Card title="Opponent changepoints">
        <p className="text-slate-300 text-sm mb-1 font-medium">{CHANGEPOINT_INTRO.title}</p>
        <p className="text-slate-400 text-sm mb-3 leading-relaxed">{CHANGEPOINT_INTRO.body}</p>
        <button
          type="button"
          disabled={refreshChangepoints.isPending}
          onClick={() => refreshChangepoints.mutate()}
          className="mb-3 text-xs px-2 py-1 rounded border border-slate-600 text-slate-300 hover:bg-slate-800"
        >
          {refreshChangepoints.isPending ? "Scanning Play data…" : "Refresh from Play sessions"}
        </button>
        <ul className="text-xs text-slate-500 mb-3 space-y-1 list-disc list-inside">
          {CHANGEPOINT_ADVICE.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <ul className="space-y-2 text-sm">
          {(changepoints?.alerts ?? []).length === 0 && (
            <li className="text-slate-500">
              No changepoints yet. Play a session at{" "}
              <Link to="/play" className="text-emerald-400 underline">
                Play vs AI
              </Link>{" "}
              (20+ bot decisions), then refresh.
            </li>
          )}
          {(changepoints?.alerts ?? []).map((a) => (
            <li
              key={`${a.player_uid}-${a.detected_at}`}
              className="border border-amber-800/50 bg-amber-950/30 rounded px-3 py-2"
            >
              <strong>{a.display_name}</strong> — {a.description}
              <span className="text-slate-500 ml-2">({Math.round(a.confidence * 100)}%)</span>
              <div className="mt-1">
                <Link
                  to="/profiles"
                  className="text-xs text-emerald-400 hover:underline"
                >
                  View on Profiles →
                </Link>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
