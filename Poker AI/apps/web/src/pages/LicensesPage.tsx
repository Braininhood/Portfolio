import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import ApiOfflineBanner from "../components/ApiOfflineBanner";
import { Card } from "../components/Card";
import PageIntro from "../components/PageIntro";

type LicenseEntry = {
  package: string;
  version: string;
  license_type: string;
  url: string | null;
  note: string | null;
};

type LicensesResponse = {
  entries: LicenseEntry[];
  generated_note: string | null;
};

const HIGHLIGHT = new Set(["TexasSolver", "phevaluator", "pytorch", "fastapi", "react", "sqlalchemy"]);

export default function LicensesPage() {
  const [q, setQ] = useState("");
  const { data, error, isLoading } = useQuery({
    queryKey: ["licenses"],
    queryFn: () => apiGet<LicensesResponse>("/licenses"),
    retry: false,
  });

  const filtered = useMemo(() => {
    const entries = data?.entries ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return entries;
    return entries.filter(
      (e) =>
        e.package.toLowerCase().includes(needle) ||
        e.license_type.toLowerCase().includes(needle) ||
        (e.note ?? "").toLowerCase().includes(needle),
    );
  }, [data, q]);

  return (
    <div className="space-y-4">
      <PageIntro
        title="Third-party licenses"
        description="Inventory for air-gapped installs and AGPL source-disclosure requirements."
      />
      <ApiOfflineBanner />
      {data?.generated_note && (
        <p className="text-xs text-slate-500">{data.generated_note}</p>
      )}
      <Card title="Packages">
        <input
          type="search"
          placeholder="Search package, license, notes…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full max-w-md mb-4 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200"
        />
        {isLoading && <p className="text-slate-500 text-sm">Loading…</p>}
        {error && <p className="text-red-400 text-sm">{(error as Error).message}</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-slate-500 border-b border-slate-700">
                <th className="py-2 pr-4 font-medium">Package</th>
                <th className="py-2 pr-4 font-medium">Version</th>
                <th className="py-2 pr-4 font-medium">License</th>
                <th className="py-2 font-medium">Note</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr
                  key={`${e.package}-${e.version}`}
                  className={`border-b border-slate-800/80 ${
                    HIGHLIGHT.has(e.package) ? "bg-amber-950/20" : ""
                  }`}
                >
                  <td className="py-2 pr-4 text-slate-200">
                    {e.url ? (
                      <a href={e.url} className="text-emerald-400 hover:underline" target="_blank" rel="noreferrer">
                        {e.package}
                      </a>
                    ) : (
                      e.package
                    )}
                  </td>
                  <td className="py-2 pr-4 text-slate-400 font-mono text-xs">{e.version}</td>
                  <td className="py-2 pr-4 text-slate-300">{e.license_type}</td>
                  <td className="py-2 text-slate-500 text-xs">{e.note ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && !isLoading && (
            <p className="text-slate-500 text-sm py-4">No matching packages.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
