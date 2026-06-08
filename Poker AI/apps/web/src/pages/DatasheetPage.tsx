import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import MarkdownDocument from "../components/MarkdownDocument";
import PageIntro from "../components/PageIntro";

type DatasheetResponse = {
  title: string;
  markdown: string;
};

export default function DatasheetPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["datasheet"],
    queryFn: () => apiGet<DatasheetResponse>("/compliance/datasheet/content"),
    retry: false,
  });

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      <PageIntro
        title="Model datasheet"
        description="Dataset scope, limitations, and compliance notes for air-gapped installs."
      />
      <ApiOfflineBanner />
      {isLoading && (
        <p className="text-slate-500 text-sm px-1">Loading datasheet…</p>
      )}
      {error && (
        <p className="text-red-400 text-sm px-1">{(error as Error).message}</p>
      )}
      {data?.markdown && <MarkdownDocument markdown={data.markdown} />}
    </div>
  );
}
