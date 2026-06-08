import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { apiGet } from "../api/client";

type ModelCardResponse = {
  name: string;
  version: string | null;
  markdown: string;
  path: string | null;
};

export default function ModelCardPanel({
  modelName,
  onClose,
}: {
  modelName: string;
  onClose: () => void;
}) {
  const { data, error, isLoading } = useQuery({
    queryKey: ["model-card", modelName],
    queryFn: () => apiGet<ModelCardResponse>(`/models/${encodeURIComponent(modelName)}/card`),
    retry: false,
  });

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/50"
      role="dialog"
      aria-modal
      aria-label="Model card"
    >
      <div className="w-full max-w-lg h-full bg-slate-900 border-l border-slate-700 shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-emerald-400">
            Model card — {modelName}
            {data?.version && (
              <span className="text-slate-500 text-sm font-normal ml-2">{data.version}</span>
            )}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-sm px-2 py-1"
          >
            Close
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 prose prose-invert prose-sm max-w-none">
          {isLoading && <p className="text-slate-500">Loading…</p>}
          {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}
          {data && <ReactMarkdown>{data.markdown}</ReactMarkdown>}
          {data?.path && (
            <p className="text-xs text-slate-600 font-mono mt-4 not-prose">{data.path}</p>
          )}
        </div>
      </div>
    </div>
  );
}
