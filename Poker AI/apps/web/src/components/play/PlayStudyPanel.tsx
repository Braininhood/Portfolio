import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../../api/client";
import { Card } from "../Card";

type StudyStatus = {
  database_path: string;
  database_exists: boolean;
  sessions: number;
  hands: number;
  hero_decisions: number;
  showdown_hands: number;
  ready_for_training: boolean;
  manifest_path: string | null;
  note: string | null;
};

type CatalogSession = {
  session_id: string;
  status: string | null;
  hands_played: number;
  persisted_hands: number;
  net_bb: number;
  table_config: Record<string, unknown>;
  updated_at: string | null;
};

type RouterStatus = {
  hu: { student_dir: string; source: string; play_study: boolean };
  multiway: { student_dir: string; source: string; play_study: boolean };
};

export default function PlayStudyPanel() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [preparing, setPreparing] = useState(false);
  const [training, setTraining] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [prepareError, setPrepareError] = useState<string | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);
  const [promoteError, setPromoteError] = useState<string | null>(null);

  const routerQuery = useQuery({
    queryKey: ["router-status"],
    queryFn: () => apiGet<RouterStatus>("/models/router/status"),
    retry: false,
  });

  const statusQuery = useQuery({
    queryKey: ["play-study-status"],
    queryFn: () => apiGet<StudyStatus>("/play/study/status"),
    refetchInterval: 30_000,
  });

  const catalogQuery = useQuery({
    queryKey: ["play-study-catalog"],
    queryFn: () =>
      apiGet<{ sessions: CatalogSession[]; total_persisted_hands: number; note: string | null }>(
        "/play/study/catalog",
      ),
  });

  const status = statusQuery.data;
  const catalog = catalogQuery.data;

  async function prepareForTraining() {
    setPreparing(true);
    setPrepareError(null);
    try {
      const res = await apiPost<{ job_id: string; message: string }>("/play/study/prepare", {});
      void navigate(`/jobs?watch=${res.job_id}`);
    } catch (e) {
      setPrepareError(e instanceof Error ? e.message : String(e));
    } finally {
      setPreparing(false);
    }
  }

  async function trainFromPlayHands() {
    setTraining(true);
    setTrainError(null);
    try {
      const res = await apiPost<{
        job_id: string;
        message: string;
        manifest_path: string;
        hero_decisions: number;
      }>("/play/study/train", {});
      void navigate(`/jobs?watch=${res.job_id}`);
    } catch (e) {
      setTrainError(e instanceof Error ? e.message : String(e));
    } finally {
      setTraining(false);
    }
  }

  async function promoteToRouter() {
    setPromoting(true);
    setPromoteError(null);
    try {
      await apiPost<RouterStatus>("/models/router/promote-play-study?confirm=true", {
        hu: true,
        multiway: true,
      });
      void qc.invalidateQueries({ queryKey: ["router-status"] });
    } catch (e) {
      setPromoteError(e instanceof Error ? e.message : String(e));
    } finally {
      setPromoting(false);
    }
  }

  const router = routerQuery.data;
  const playStudyActive = router?.hu.play_study || router?.multiway.play_study;

  return (
    <Card title="AI study pool (database)">
      <p className="text-sm text-slate-400 mb-4">
        Every completed hand is saved in <code className="text-slate-300">play_hands</code> with full action logs,
        showdowns, and bot lineups. Train a student policy directly from your hero decisions.
      </p>

      {status && (
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-4">
          <div>
            <dt className="text-slate-500">Sessions</dt>
            <dd className="text-lg font-semibold text-slate-100">{status.sessions}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Hands in DB</dt>
            <dd className="text-lg font-semibold text-slate-100">{status.hands}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Hero decisions</dt>
            <dd className="text-lg font-semibold text-emerald-300">{status.hero_decisions}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Showdowns</dt>
            <dd className="text-lg font-semibold text-slate-100">{status.showdown_hands}</dd>
          </div>
        </dl>
      )}

      {status?.manifest_path && (
        <p className="text-xs text-slate-500 mb-3">
          Training manifest: <span className="font-mono text-slate-400">{status.manifest_path}</span>
        </p>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          disabled={!status?.ready_for_training || preparing}
          onClick={() => void prepareForTraining()}
          className="px-4 py-2 rounded-md border border-slate-600 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
        >
          {preparing ? "Preparing…" : "Refresh training manifest"}
        </button>
        <button
          type="button"
          disabled={!status?.ready_for_training || training || (status?.hero_decisions ?? 0) < 5}
          onClick={() => void trainFromPlayHands()}
          className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 text-sm font-medium disabled:opacity-50"
          title={
            (status?.hero_decisions ?? 0) < 5
              ? "Play at least a few hands with hero decisions first"
              : "Behavioral clone from your play-vs-AI decisions"
          }
        >
          {training ? "Starting…" : "Train student from play hands"}
        </button>
        <Link
          to="/jobs"
          className="px-4 py-2 rounded-md border border-slate-600 text-sm text-slate-300 hover:bg-slate-800"
        >
          View Tasks
        </Link>
        <button
          type="button"
          disabled={promoting}
          onClick={() => void promoteToRouter()}
          className="px-4 py-2 rounded-md border border-emerald-700 text-sm text-emerald-200 hover:bg-emerald-950/50 disabled:opacity-50"
          title="Wire play-study HU/multi-way weights into RouterPolicy (decide, play bots, league)"
        >
          {promoting ? "Promoting…" : playStudyActive ? "Router uses play-study" : "Promote to router"}
        </button>
      </div>

      {router && (
        <p className="text-xs text-slate-500 mb-3 font-mono">
          Router HU → {router.hu.student_dir}
          {router.hu.play_study ? " (play-study)" : ""} · multiway → {router.multiway.student_dir}
          {router.multiway.play_study ? " (play-study)" : ""}
        </p>
      )}

      {prepareError && <p className="text-sm text-red-400 mb-2">{prepareError}</p>}
      {trainError && <p className="text-sm text-red-400 mb-2">{trainError}</p>}
      {promoteError && <p className="text-sm text-red-400 mb-3">{promoteError}</p>}

      {catalog && catalog.sessions.length > 0 && (
        <div className="border-t border-slate-700 pt-3">
          <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Saved sessions</h4>
          <ul className="space-y-1 max-h-40 overflow-y-auto text-xs">
            {catalog.sessions.map((s) => (
              <li key={s.session_id} className="flex justify-between gap-2 text-slate-400">
                <span className="truncate font-mono text-slate-300" title={s.session_id}>
                  {s.session_id.slice(0, 8)}…
                </span>
                <span>
                  {s.persisted_hands} hands · {s.net_bb >= 0 ? "+" : ""}
                  {s.net_bb} BB · {s.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {status && !status.ready_for_training && (
        <p className="text-xs text-slate-500 mt-2">Play a few hands — they will appear here automatically.</p>
      )}
    </Card>
  );
}
