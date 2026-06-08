import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";

type Compliance = {
  owned_data_only: boolean;
  no_external_ai_services: boolean;
  offline_mode_verified: boolean;
  tos_note: string;
  datasheet_url: string | null;
  licenses_count: number;
  agpl_packages: string[];
};

function Dot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 ${ok ? "text-emerald-400/90" : "text-slate-500"}`}
      title={ok ? `${label} — verified` : `${label} — not verified`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-slate-600"}`}
        aria-hidden
      />
      {label}
    </span>
  );
}

export default function ComplianceFooter() {
  const { data } = useQuery({
    queryKey: ["compliance"],
    queryFn: () => apiGet<Compliance>("/compliance"),
    staleTime: 60_000,
    retry: false,
  });

  return (
    <footer className="border-t border-slate-800 bg-slate-950/80 mt-auto">
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          <Dot ok={data?.offline_mode_verified ?? false} label="Offline" />
          <Dot ok={data?.no_external_ai_services ?? true} label="No external AI" />
          <Dot ok={data?.owned_data_only ?? true} label="Owned data only" />
        </div>
        <span className="hidden sm:inline text-slate-700">·</span>
        <Link to="/licenses" className="hover:text-emerald-400">
          Licenses{data ? ` (${data.licenses_count})` : ""}
        </Link>
        {data?.datasheet_url && (
          <Link to={data.datasheet_url} className="hover:text-emerald-400">
            Datasheet
          </Link>
        )}
        <Link to="/status" className="ml-auto hover:text-emerald-400">
          Smoke test
        </Link>
      </div>
    </footer>
  );
}
