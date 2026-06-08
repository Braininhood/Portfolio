import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { apiGet } from "../api/client";
import { Card } from "../components/Card";

type BlueprintResponse = {
  title: string;
  version: string;
  sections: { id: string; title: string; body: string }[];
};

export default function BlueprintPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["blueprint"],
    queryFn: () => apiGet<BlueprintResponse>("/blueprint"),
  });

  return (
    <div className="space-y-4">
      <Card title="Architecture blueprint">
        {isLoading && <p className="text-slate-400">Loading from doc/blueprint.yaml…</p>}
        {error && <p className="text-red-400">{(error as Error).message}</p>}
        {data && (
          <>
            <p className="text-sm text-slate-400 mb-4">
              {data.title} v{data.version} — single source of truth
            </p>
            {data.sections.map((s) => (
              <article key={s.id} className="mb-6 prose prose-invert prose-sm max-w-none">
                <h3 className="text-emerald-400 text-lg">{s.title}</h3>
                <ReactMarkdown>{s.body}</ReactMarkdown>
              </article>
            ))}
          </>
        )}
      </Card>
    </div>
  );
}
