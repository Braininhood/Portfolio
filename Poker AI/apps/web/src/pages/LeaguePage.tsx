import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { Card } from "../components/Card";

const AGENT_NAMES: Record<string, string> = {
  main_agent: "Main AI",
  main_exploiter: "Exploiter AI",
  distilled_gto: "GTO Baseline",
  league_exploiter: "League Exploiter",
  tag: "TAG · Tight-Aggressive",
  lag: "LAG · Loose-Aggressive",
  nit: "Nit · Rock",
  rock: "Rock",
  fish: "Fish · Loose-Passive",
  call_station: "Calling Station",
  maniac: "Maniac · Ultra-Aggressive",
  passive_reg: "Weak-Tight Reg",
  random: "Random",
  cfr_stacked: "CFR + Neural Stack",
  cql_agent: "CQL offline RL (Research)",
};

type LeaderboardResponse = {
  finished_at: string | null;
  hands_played: number | null;
  promoted: boolean | null;
  rows: {
    agent_id: string;
    elo: number | null;
    hands: number | null;
    bb_per_100: number | null;
    aivat_bb_per_100: number | null;
  }[];
};

type ReplayResponse = {
  finished_at: string | null;
  hands_scored: number | null;
  hero_decisions: number | null;
  aivat_mode: string | null;
  agents: {
    agent_id: string;
    hands: number | null;
    hero_decisions: number | null;
    bb_per_100: number | null;
    action_match_pct: number | null;
  }[];
  by_format: Record<string, { hands?: number; bb_per_100?: number }>;
};

type AivatResponse = {
  finished_at: string | null;
  aivat_mode: string | null;
  hands: number | null;
  naive_stderr: number | null;
  full_stderr: number | null;
  stderr_reduction_pct: number | null;
};

type CheckpointsResponse = {
  current: string | null;
  rows: {
    checkpoint_id: string;
    created_at: string | null;
    main_elo: number | null;
    hands: number | null;
    promoted: boolean | null;
    note: string | null;
    is_current: boolean;
  }[];
};

type TabId = "synthetic" | "real" | "aivat" | "checkpoints";

const TABS: { id: TabId; label: string }[] = [
  { id: "synthetic", label: "Synthetic league" },
  { id: "real", label: "Real hands" },
  { id: "aivat", label: "AIVAT details" },
  { id: "checkpoints", label: "Checkpoints" },
];

function fmtBb(v: number | null | undefined) {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}`;
}

export default function LeaguePage() {
  const [tab, setTab] = useState<TabId>("synthetic");

  const leaderboard = useQuery({
    queryKey: ["league"],
    queryFn: () => apiGet<LeaderboardResponse>("/league/leaderboard"),
    enabled: tab === "synthetic",
  });

  const replay = useQuery({
    queryKey: ["league-replay"],
    queryFn: () => apiGet<ReplayResponse>("/league/replay-report"),
    enabled: tab === "real",
  });

  const aivat = useQuery({
    queryKey: ["league-aivat"],
    queryFn: () => apiGet<AivatResponse>("/league/aivat-audit"),
    enabled: tab === "aivat",
  });

  const checkpoints = useQuery({
    queryKey: ["league-checkpoints"],
    queryFn: () => apiGet<CheckpointsResponse>("/league/checkpoints"),
    enabled: tab === "checkpoints",
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 border-b border-slate-700 pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-slate-700 text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "synthetic" && (
        <Card title="League leaderboard">
          <p className="text-slate-400 text-sm mb-4">
            AI personalities played thousands of synthetic hands against each other. Rankings show
            who won the most chips in simulation.
          </p>
          {leaderboard.isLoading && <p className="text-slate-400">Loading…</p>}
          {leaderboard.error && (
            <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
              No synthetic league report yet.{" "}
              <Link to="/jobs?task=league_run&preset=recommended" className="text-amber-100 underline">
                Run bot league
              </Link>{" "}
              from Tasks, then reload.
            </p>
          )}
          {leaderboard.data && (
            <>
              <p className="text-sm text-slate-400 mb-3">
                Last run:{" "}
                {leaderboard.data.finished_at
                  ? new Date(leaderboard.data.finished_at).toLocaleString()
                  : "—"}{" "}
                · {leaderboard.data.hands_played?.toLocaleString() ?? 0} hands simulated ·{" "}
                {leaderboard.data.promoted ? (
                  <span className="text-emerald-400">Main bot promoted</span>
                ) : (
                  <span>Not promoted yet</span>
                )}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-700">
                      <th className="py-2 pr-4">Bot</th>
                      <th className="pr-4">Elo</th>
                      <th className="pr-4">Hands</th>
                      <th className="pr-4">BB/100</th>
                      <th>AIVAT BB/100</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.data.rows.map((r, i) => (
                      <tr
                        key={r.agent_id}
                        className={`border-b border-slate-800 ${
                          i === 0 ? "text-emerald-200" : "text-slate-300"
                        }`}
                      >
                        <td className="py-2 pr-4 font-medium">
                          {AGENT_NAMES[r.agent_id] ?? r.agent_id}
                        </td>
                        <td className="pr-4">{r.elo?.toFixed(0)}</td>
                        <td className="pr-4">{r.hands?.toLocaleString()}</td>
                        <td className="pr-4">{fmtBb(r.bb_per_100)}</td>
                        <td>{fmtBb(r.aivat_bb_per_100)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </Card>
      )}

      {tab === "real" && (
        <Card title="Real hands — replay league">
          <p className="text-slate-400 text-sm mb-4">
            Scores your AI against decisions in imported hand histories — not synthetic simulation.
            Action match % shows how often the policy agrees with what the hero actually did.
          </p>
          {replay.isLoading && <p className="text-slate-400">Loading…</p>}
          {replay.error && (
            <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
              No replay report yet.{" "}
              <Link to="/jobs?task=league_replay_run&preset=quick" className="text-amber-100 underline">
                Run league on your library
              </Link>{" "}
              from Tasks.
            </p>
          )}
          {replay.data && (
            <>
              <p className="text-sm text-slate-400 mb-3">
                Last run:{" "}
                {replay.data.finished_at
                  ? new Date(replay.data.finished_at).toLocaleString()
                  : "—"}{" "}
                · {replay.data.hands_scored?.toLocaleString() ?? 0} hands ·{" "}
                {replay.data.hero_decisions?.toLocaleString() ?? 0} hero decisions · AIVAT mode:{" "}
                {replay.data.aivat_mode ?? "sketch"}
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-700">
                      <th className="py-2 pr-4">Policy</th>
                      <th className="pr-4">Hands</th>
                      <th className="pr-4">BB/100</th>
                      <th>Action match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {replay.data.agents.map((a) => (
                      <tr key={a.agent_id} className="border-b border-slate-800 text-slate-300">
                        <td className="py-2 pr-4 font-medium">
                          {AGENT_NAMES[a.agent_id] ?? a.agent_id}
                        </td>
                        <td className="pr-4">{a.hands?.toLocaleString()}</td>
                        <td className="pr-4">{fmtBb(a.bb_per_100)}</td>
                        <td>
                          {a.action_match_pct != null ? `${a.action_match_pct.toFixed(1)}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {Object.keys(replay.data.by_format).length > 0 && (
                <div className="text-sm text-slate-400">
                  <span className="text-slate-300 font-medium">By format: </span>
                  {Object.entries(replay.data.by_format).map(([fmt, v]) => (
                    <span key={fmt} className="mr-4">
                      {fmt.toUpperCase()}: {v.hands ?? 0} hands, {fmtBb(v.bb_per_100)} BB/100
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </Card>
      )}

      {tab === "aivat" && (
        <Card title="AIVAT statistical adjustment">
          <p className="text-slate-400 text-sm mb-4">
            AIVAT removes luck from win-rate estimates. Full mode (chance + strategy corrections)
            reduces variance vs the v1 showdown sketch — trust AIVAT BB/100 over raw BB/100.
          </p>
          {aivat.isLoading && <p className="text-slate-400">Loading…</p>}
          {aivat.error && (
            <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
              No audit yet.{" "}
              <Link to="/jobs?task=aivat_audit&preset=recommended" className="text-amber-100 underline">
                Run AIVAT audit
              </Link>{" "}
              from Tasks.
            </p>
          )}
          {aivat.data && (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">Last audit</dt>
                <dd className="text-slate-200">
                  {aivat.data.finished_at
                    ? new Date(aivat.data.finished_at).toLocaleString()
                    : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Mode</dt>
                <dd className="text-slate-200">{aivat.data.aivat_mode ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Sample hands</dt>
                <dd className="text-slate-200">{aivat.data.hands?.toLocaleString() ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Stderr reduction</dt>
                <dd
                  className={
                    (aivat.data.stderr_reduction_pct ?? 0) >= 15
                      ? "text-emerald-400"
                      : "text-amber-300"
                  }
                >
                  {aivat.data.stderr_reduction_pct?.toFixed(1) ?? "—"}% (target ≥15%)
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Naive stderr</dt>
                <dd className="text-slate-200">{aivat.data.naive_stderr?.toFixed(4) ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Full AIVAT stderr</dt>
                <dd className="text-slate-200">{aivat.data.full_stderr?.toFixed(4) ?? "—"}</dd>
              </div>
            </dl>
          )}
        </Card>
      )}

      {tab === "checkpoints" && (
        <Card title="Promotion checkpoints">
          <p className="text-slate-400 text-sm mb-4">
            Snapshots saved when the main bot promoted during league training. Exploiter calibration
            uses these checkpoints.
          </p>
          {checkpoints.isLoading && <p className="text-slate-400">Loading…</p>}
          {checkpoints.data && checkpoints.data.rows.length === 0 && (
            <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
              No checkpoints yet. Run bot league until promotion fires.
            </p>
          )}
          {checkpoints.data && checkpoints.data.rows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-700">
                    <th className="py-2 pr-4">Checkpoint</th>
                    <th className="pr-4">Elo</th>
                    <th className="pr-4">Hands</th>
                    <th className="pr-4">Promoted</th>
                    <th>Note</th>
                  </tr>
                </thead>
                <tbody>
                  {checkpoints.data.rows.map((cp) => (
                    <tr
                      key={cp.checkpoint_id}
                      className={`border-b border-slate-800 ${
                        cp.is_current ? "text-emerald-200" : "text-slate-300"
                      }`}
                    >
                      <td className="py-2 pr-4 font-mono text-xs">
                        {cp.is_current ? "* " : ""}
                        {cp.checkpoint_id}
                      </td>
                      <td className="pr-4">{cp.main_elo?.toFixed(0)}</td>
                      <td className="pr-4">{cp.hands?.toLocaleString()}</td>
                      <td className="pr-4">{cp.promoted ? "Yes" : "No"}</td>
                      <td className="text-slate-500">{cp.note || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
