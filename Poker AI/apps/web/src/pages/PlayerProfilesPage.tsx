import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import ChangepointBanner from "../components/ChangepointBanner";
import CausalEvalPanel from "../components/CausalEvalPanel";
import RangeInferencePanel from "../components/RangeInferencePanel";
import { Card } from "../components/Card";

type PlayerRow = {
  player_uid: string;
  display_name: string;
  hands: number;
  source?: string;
};

type PlayerList = {
  total: number;
  players: PlayerRow[];
  hint?: string | null;
};

type Profile = {
  player_uid: string;
  display_name: string;
  hands_in_sample: number;
  summary: string;
  player_type: string;
  stats: {
    vpip_pct: number;
    pfr_pct: number;
    aggression_factor: number;
  };
  similar_players: {
    display_name: string;
    similarity_pct: number;
  }[];
  changepoint?: {
    detected_at: string;
    description: string;
    confidence: number;
  } | null;
};

export default function PlayerProfilesPage() {
  const [selectedUid, setSelectedUid] = useState<string | null>(null);

  const { data: list, isLoading, error } = useQuery({
    queryKey: ["players"],
    queryFn: () => apiGet<PlayerList>("/players?limit=50"),
  });

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["player-profile", selectedUid],
    queryFn: () => apiGet<Profile>(`/players/${encodeURIComponent(selectedUid!)}/profile`),
    enabled: selectedUid !== null,
  });

  return (
    <div className="space-y-4">
      <Card title="Players">
        <p className="text-slate-400 text-sm mb-4">
          Opponents from imported hand histories and Play vs AI bots (after sessions on{" "}
          <a href="/play" className="text-emerald-400 underline">
            Play
          </a>
          ). Both feed style training and drift monitoring.
        </p>
        {list?.hint && (
          <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2 mb-4">
            {list.hint}
          </p>
        )}
        <details className="text-xs text-slate-500 mb-4">
          <summary className="cursor-pointer text-slate-400">What do the numbers mean?</summary>
          <ul className="mt-2 space-y-1 list-disc list-inside">
            <li>
              <strong>VPIP</strong> — how often they put money in the pot voluntarily (higher =
              plays more hands).
            </li>
            <li>
              <strong>PFR</strong> — how often they raise before the flop (higher = more aggressive
              preflop).
            </li>
            <li>
              <strong>Aggression</strong> — bets and raises vs calls after the flop (higher =
              pushes harder).
            </li>
            <li>
              <strong>Similar players</strong> — others who act alike (from the style model).
            </li>
          </ul>
        </details>

        {isLoading && <p className="text-slate-500">Loading players…</p>}
        {error && <p className="text-red-400">{(error as Error).message}</p>}
        {list && list.players.length === 0 && (
          <p className="text-amber-200/90 text-sm rounded-md bg-amber-900/30 border border-amber-800 px-3 py-2">
            No players yet. Import hands first:{" "}
            <code className="text-emerald-300">poker_ai ingest your_hand_folder</code>
          </p>
        )}
        {list && list.players.length > 0 && (
          <ul className="divide-y divide-slate-800 border border-slate-700 rounded-md max-h-48 overflow-y-auto mb-4">
            {list.players.map((p) => (
              <li key={p.player_uid}>
                <button
                  type="button"
                  onClick={() => setSelectedUid(p.player_uid)}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-800 ${
                    selectedUid === p.player_uid ? "bg-emerald-900/40 text-emerald-100" : "text-slate-200"
                  }`}
                >
                  <span className="font-medium">{p.display_name}</span>
                  <span className="text-slate-500 ml-2">
                    {p.source === "play" ? `${p.hands} decisions (Play)` : `seen in ${p.hands} hands`}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {selectedUid && (
        <Card title={profile?.display_name ?? "Player style"}>
          {profileLoading && <p className="text-slate-500">Analyzing hands…</p>}
          {profile && (
            <div className="space-y-4 text-sm">
              <ChangepointBanner playerUid={selectedUid} changepoint={profile.changepoint} />
              <p className="text-xl text-emerald-300 font-medium">{profile.player_type}</p>
              <p className="text-slate-300 leading-relaxed">{profile.summary.replace(/\*\*/g, "")}</p>
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="VPIP" value={`${profile.stats.vpip_pct}%`} sub="plays hands" />
                <StatBox label="PFR" value={`${profile.stats.pfr_pct}%`} sub="preflop raises" />
                <StatBox label="Aggression" value={String(profile.stats.aggression_factor)} sub="postflop" />
              </div>
              <p className="text-xs text-slate-500">
                Estimated from {profile.hands_in_sample} hands in your database.
              </p>
              {profile.similar_players.length > 0 && (
                <div>
                  <h3 className="text-slate-400 font-medium mb-2">Reminds us of</h3>
                  <ul className="space-y-1 text-slate-300">
                    {profile.similar_players.map((n, i) => (
                      <li key={i}>
                        {n.display_name} ({n.similarity_pct}% similar style)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="pt-2 border-t border-slate-800">
                <Link
                  to="/jobs?task=opponents_eval_exploit&preset=recommended"
                  className="inline-flex items-center rounded-md bg-emerald-800/40 border border-emerald-700 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-800/60"
                >
                  Run exploit test vs GTO baseline
                </Link>
                <p className="text-xs text-slate-500 mt-2">
                  Same as CLI <code className="text-slate-400">opponents eval-exploit</code> — measures
                  exploit policy edge vs scripted opponents.
                </p>
              </div>
            </div>
          )}
        </Card>
      )}

      {selectedUid && !selectedUid.startsWith("play_bot:") && (
        <div className="grid lg:grid-cols-2 gap-4">
          <RangeInferencePanel playerUid={selectedUid} />
          <CausalEvalPanel playerUid={selectedUid} />
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-md bg-slate-800/80 p-3 text-center">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-xl font-semibold text-slate-100">{value}</div>
      <div className="text-xs text-slate-600">{sub}</div>
    </div>
  );
}
