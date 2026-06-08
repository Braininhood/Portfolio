import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import { Card } from "../components/Card";
import ModelCardPanel from "../components/ModelCardPanel";

type ModelVersion = {
  name: string;
  current_version: string | null;
  candidate_version: string | null;
  current_metrics: Record<string, number>;
  candidate_metrics: Record<string, number> | null;
  can_promote: boolean;
  can_rollback: boolean;
  current_path: string | null;
  note: string | null;
};

type GateCheck = {
  gate_id: string;
  label: string;
  passed: boolean;
  detail: string;
  required: boolean;
};

type PromotionGates = {
  model_name: string;
  can_promote: boolean;
  blocking: string[];
  checks: GateCheck[];
};

type RouterStatus = {
  hu: { student_dir: string; source: string; play_study: boolean };
  multiway: { student_dir: string; source: string; play_study: boolean };
};

function PromotionGatesPanel({ name }: { name: string }) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["promotion-gates", name],
    queryFn: () => apiGet<PromotionGates>(`/models/${name}/promotion-gates`),
    retry: false,
  });

  if (isLoading) return <p className="text-xs text-slate-500 mt-2">Checking gates…</p>;
  if (error) return <p className="text-xs text-red-400 mt-2">{(error as Error).message}</p>;
  if (!data) return null;

  return (
    <div className="mt-3 border border-slate-700 rounded p-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className={data.can_promote ? "text-emerald-400" : "text-amber-400"}>
          {data.can_promote ? "Gates passed" : `Blocked: ${data.blocking.join(", ") || "see checks"}`}
        </span>
        <button
          type="button"
          onClick={() => void refetch()}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          Refresh
        </button>
      </div>
      <ul className="mt-2 space-y-1 text-xs text-slate-400">
        {data.checks.map((c) => (
          <li key={c.gate_id}>
            <span className={c.passed ? "text-emerald-500" : "text-red-400"}>
              {c.passed ? "✓" : "✗"}
            </span>{" "}
            {c.label}
            {!c.required ? " (optional)" : null}: {c.detail}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ModelsPage() {
  const [cardModel, setCardModel] = useState<string | null>(null);
  const [gatesModel, setGatesModel] = useState<string | null>(null);
  const qc = useQueryClient();
  const { data, error, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => apiGet<{ models: ModelVersion[] }>("/models"),
    retry: false,
  });

  const routerQuery = useQuery({
    queryKey: ["router-status"],
    queryFn: () => apiGet<RouterStatus>("/models/router/status"),
    retry: false,
  });

  const promoteRouter = useMutation({
    mutationFn: () =>
      apiPost<RouterStatus>("/models/router/promote-play-study?confirm=true", {
        hu: true,
        multiway: true,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["router-status"] });
    },
  });

  const promote = useMutation({
    mutationFn: (name: string) => apiPost<ModelVersion>(`/models/${name}/promote?confirm=true`, {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["models"] });
      void qc.invalidateQueries({ queryKey: ["promotion-gates"] });
    },
  });

  const rollback = useMutation({
    mutationFn: (name: string) => apiPost<ModelVersion>(`/models/${name}/rollback`, {}),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["models"] }),
  });

  const label: Record<string, string> = {
    hhformer: "HHFormer",
    student_hu: "Student HU",
    student_multiway: "Student Multi-way",
    student_play_study_hu: "Play-study HU",
    student_play_study_multiway: "Play-study Multi-way",
    preflop_hu: "Preflop CFR (HU)",
    preflop_6max: "Preflop CFR (6-max)",
    preflop_8max: "Preflop CFR (8-max)",
    preflop_9max: "Preflop CFR (9-max)",
    preflop_10max: "Preflop CFR (10-max)",
    style_encoder: "Style encoder",
    solver_cache: "Solver cache",
  };

  return (
    <div className="space-y-4">
      <ApiOfflineBanner />
      <Card title="RouterPolicy bindings">
        <p className="text-slate-400 text-sm mb-3">
          Runtime decide/play/league uses these student dirs. Promote play-study weights after
          training on the Play page or via CLI{" "}
          <code className="text-emerald-300">poker-ai models router promote-play-study --confirm</code>.
        </p>
        {routerQuery.data && (
          <dl className="text-sm space-y-2 font-mono text-slate-400">
            <div>
              HU → {routerQuery.data.hu.student_dir}
              {routerQuery.data.hu.play_study ? " (play-study)" : ""}
            </div>
            <div>
              Multi-way → {routerQuery.data.multiway.student_dir}
              {routerQuery.data.multiway.play_study ? " (play-study)" : ""}
            </div>
          </dl>
        )}
        <button
          type="button"
          disabled={promoteRouter.isPending}
          onClick={() => promoteRouter.mutate()}
          className="mt-3 px-3 py-1 rounded bg-emerald-800 hover:bg-emerald-700 text-sm"
        >
          Promote play-study into router
        </button>
      </Card>
      <Card title="Model versions">
        <p className="text-slate-400 text-sm mb-4">
          Promote only after drift is green, league AIVAT gates pass, and canary artifacts exist.
          CLI: <code className="text-emerald-300">poker-ai models gates student_hu</code>
        </p>
        {isLoading && <p className="text-slate-500">Loading…</p>}
        {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}
        <div className="space-y-4">
          {(data?.models ?? []).map((m) => (
            <div key={m.name} className="border border-slate-700 rounded-lg p-4">
              <h3 className="font-medium text-emerald-300">{label[m.name] ?? m.name}</h3>
              <p className="text-sm text-slate-400 mt-1">
                Current: {m.current_version ?? "not trained"}
              </p>
              {m.candidate_version && (
                <p className="text-sm text-sky-300/90 mt-1">
                  Candidate {m.candidate_version}
                  {m.name === "hhformer" ? " — solver fine-tuned v2" : null}
                  {m.candidate_metrics?.map_accuracy != null
                    ? ` · MAP ${(m.candidate_metrics.map_accuracy * 100).toFixed(1)}%`
                    : null}
                  {m.candidate_metrics?.sop_auc != null
                    ? ` · SOP ${m.candidate_metrics.sop_auc.toFixed(2)}`
                    : null}
                </p>
              )}
              {m.note && <p className="text-xs text-slate-500 mt-1">{m.note}</p>}
              {m.current_path && (
                <p className="text-xs text-slate-600 mt-1 font-mono">{m.current_path}</p>
              )}
              {gatesModel === m.name && <PromotionGatesPanel name={m.name} />}
              <div className="flex flex-wrap gap-2 mt-3">
                <button
                  type="button"
                  onClick={() => setCardModel(m.name)}
                  className="px-3 py-1 rounded border border-slate-600 hover:border-emerald-600 text-sm text-slate-300"
                >
                  Model card
                </button>
                {m.candidate_version && (
                  <button
                    type="button"
                    onClick={() => setGatesModel(gatesModel === m.name ? null : m.name)}
                    className="px-3 py-1 rounded border border-slate-600 hover:border-sky-600 text-sm text-slate-300"
                  >
                    {gatesModel === m.name ? "Hide gates" : "Check gates"}
                  </button>
                )}
                {m.can_promote && (
                  <button
                    type="button"
                    disabled={promote.isPending}
                    onClick={() => promote.mutate(m.name)}
                    className="px-3 py-1 rounded bg-emerald-800 hover:bg-emerald-700 text-sm"
                  >
                    Promote candidate
                  </button>
                )}
                {m.can_rollback && (
                  <button
                    type="button"
                    disabled={rollback.isPending}
                    onClick={() => rollback.mutate(m.name)}
                    className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-sm"
                  >
                    Rollback
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
      {cardModel && (
        <ModelCardPanel modelName={cardModel} onClose={() => setCardModel(null)} />
      )}
    </div>
  );
}
