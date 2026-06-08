import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

/** Orange count badge when setup steps are still pending. */
export default function SetupNavBadge() {
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiGet<{ pending_count: number }>("/setup/steps");
        setPending(res.pending_count);
      } catch {
        setPending(0);
      }
    };
    void load();
    const id = window.setInterval(() => void load(), 20_000);
    return () => clearInterval(id);
  }, []);

  if (pending <= 0) return null;
  return (
    <span className="ml-1.5 inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-slate-900">
      {pending > 9 ? "9+" : pending}
    </span>
  );
}
