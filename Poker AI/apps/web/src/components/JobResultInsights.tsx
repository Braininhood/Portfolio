import ArtifactPathLink from "./ArtifactPathLink";
import { explainJobResult, VERDICT_STYLE } from "../lib/explainJobResult";

type Props = {
  jobType: string;
  result: Record<string, unknown> | null | undefined;
  /** Extra advice from the API friendly summary (shown first). */
  apiAdvice?: string[];
};

export default function JobResultInsights({ jobType, result, apiAdvice = [] }: Props) {
  const insights = explainJobResult(jobType, result);
  const hasAdvice = apiAdvice.length > 0;
  if (insights.length === 0 && !hasAdvice) return null;

  return (
    <div className="mt-4 rounded-lg border border-slate-600 bg-slate-950/60 p-3 space-y-3">
      <h5 className="text-sm font-medium text-slate-200">Your results & advice</h5>

      {hasAdvice && (
        <ul className="space-y-1.5 text-sm text-amber-100/95 list-disc list-inside">
          {apiAdvice.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}

      {insights.length > 0 && (
        <ul className="space-y-3">
          {insights.map((row) => {
            const style = VERDICT_STYLE[row.verdict];
            return (
              <li key={row.label} className="text-sm border-b border-slate-800/80 pb-2 last:border-0 last:pb-0">
                <div className="flex items-start gap-2">
                  <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
                  <div className="min-w-0">
                    <span className="text-slate-400">{row.label}: </span>
                    {row.artifactPath ? (
                      <ArtifactPathLink path={row.artifactPath} label={row.value} />
                    ) : (
                      <span className={`font-medium ${style.text}`}>{row.value}</span>
                    )}
                    {row.verdict === "good" && (
                      <span className="ml-2 text-xs text-emerald-500">Looks good</span>
                    )}
                    {row.verdict === "warn" && (
                      <span className="ml-2 text-xs text-amber-500">Worth improving</span>
                    )}
                    {row.tip && (
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">{row.tip}</p>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
