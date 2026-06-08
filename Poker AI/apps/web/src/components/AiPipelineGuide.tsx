import { Link } from "react-router-dom";

export type PipelineStep = {
  step: number;
  title: string;
  what: string;
  why: string;
  where: "import" | "jobs" | "setup";
  jobType?: string;
  setupStepId?: string;
};

/** Matches Setup wizard + Tasks page (10 pipeline steps + import). */
export const AI_PIPELINE: PipelineStep[] = [
  {
    step: 0,
    title: "Import hand histories",
    what: "Add .txt / .phh files from your PC (folder or cap on new hands).",
    why: "The AI only learns from hands in your library — nothing to train without this.",
    where: "import",
  },
  {
    step: 1,
    title: "Prepare hands for AI",
    what: "Turns library hands into features.jsonl.",
    why: "HHFormer and fine-tune jobs need this prepared format.",
    where: "setup",
    jobType: "features_build",
    setupStepId: "features",
  },
  {
    step: 2,
    title: "Train HHFormer",
    what: "Learns patterns from your hands (positions, actions, outcomes).",
    why: "Core encoder — used by student, style, and play-study training.",
    where: "setup",
    jobType: "train_hhformer",
    setupStepId: "train_hhformer",
  },
  {
    step: 3,
    title: "Preflop chart",
    what: "CFR preflop strategy for HU and/or 6-max.",
    why: "Required for solid play before the flop in bots and sim.",
    where: "setup",
    jobType: "solve_preflop",
    setupStepId: "solve_preflop",
  },
  {
    step: 4,
    title: "Solver cache",
    what: "Postflop teacher spots (TexasSolver or mock for tests).",
    why: "Student, CQL, and HHFormer v2 all learn from these labels.",
    where: "setup",
    jobType: "solve_grid",
    setupStepId: "solve_grid",
  },
  {
    step: 5,
    title: "Train decision AI (HU)",
    what: "Student model distills the solver teacher on postflop spots.",
    why: "Main playable HU brain for advice, Play vs AI, and league.",
    where: "setup",
    jobType: "train_student",
    setupStepId: "train_student",
  },
  {
    step: 6,
    title: "Train CQL policy",
    what: "Conservative offline RL on logged solver rows.",
    why: "Adds cql_agent to league — safer on rare actions than naive cloning.",
    where: "setup",
    jobType: "train_cql",
    setupStepId: "train_cql",
  },
  {
    step: 7,
    title: "Fine-tune HHFormer on solver",
    what: "Continual pretrain → v2 candidate (promote on Models).",
    why: "Aligns embeddings with solver-masked actions for better MAP/SOP.",
    where: "setup",
    jobType: "train_hhformer_finetune",
    setupStepId: "train_hhformer_finetune",
  },
  {
    step: 8,
    title: "Train player styles",
    what: "Style encoder clusters opponent tendencies.",
    why: "Powers Players page profiling and adaptive bots.",
    where: "setup",
    jobType: "train_style",
    setupStepId: "train_style",
  },
  {
    step: 9,
    title: "Bot league",
    what: "Bots play each other; rankings and promotion gates.",
    why: "Verify student + CQL beat baselines before trusting live play.",
    where: "setup",
    jobType: "league_run",
    setupStepId: "league",
  },
];

type Props = {
  completedJobTypes?: Set<string>;
};

export default function AiPipelineGuide({ completedJobTypes }: Props) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 space-y-3">
      <h3 className="text-base font-semibold text-slate-100">Full AI path (step by step)</h3>
      <p className="text-sm text-slate-400 leading-relaxed">
        Run <strong className="text-slate-300">one task at a time</strong> from{" "}
        <Link to="/setup" className="text-emerald-400 hover:underline">
          Setup
        </Link>{" "}
        or{" "}
        <Link to="/jobs" className="text-emerald-400 hover:underline">
          Tasks
        </Link>
        . Each step has Quick / Recommended / Full presets and per-field help under Configure.
      </p>
      <ol className="space-y-3">
        {AI_PIPELINE.map((s) => {
          const done = s.jobType && completedJobTypes?.has(s.jobType);
          return (
            <li
              key={s.step}
              className={`flex gap-3 rounded-lg border px-3 py-2.5 ${
                done ? "border-emerald-800/50 bg-emerald-950/20" : "border-slate-800 bg-slate-950/40"
              }`}
            >
              <span
                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                  done ? "bg-emerald-700 text-white" : "bg-slate-700 text-slate-200"
                }`}
              >
                {s.step}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-100">
                  {s.title}
                  {done && <span className="ml-2 text-xs text-emerald-400">✓ done recently</span>}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{s.what}</p>
                <p className="text-xs text-slate-500 mt-1 italic">{s.why}</p>
                {s.where === "import" ? (
                  <Link
                    to="/import"
                    className="inline-block mt-2 text-xs text-emerald-400 hover:underline"
                  >
                    Go to Import →
                  </Link>
                ) : s.setupStepId ? (
                  <Link
                    to="/setup"
                    className="inline-block mt-2 text-xs text-emerald-400 hover:underline"
                  >
                    Setup step {s.step} →
                  </Link>
                ) : (
                  <Link
                    to={s.jobType ? `/jobs?task=${s.jobType}&preset=recommended` : "/jobs"}
                    className="inline-block mt-2 text-xs text-emerald-400 hover:underline"
                  >
                    Open on Tasks →
                  </Link>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
