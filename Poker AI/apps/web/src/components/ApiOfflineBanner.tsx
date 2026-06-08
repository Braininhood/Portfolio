import { useApiOnline } from "../hooks/useApiOnline";

type Props = {
  /** When true, never show offline (e.g. jobs are actively updating). */
  suppressWhenBusy?: boolean;
};

export default function ApiOfflineBanner({ suppressWhenBusy }: Props = {}) {
  const online = useApiOnline();

  if (suppressWhenBusy || online !== false) return null;

  return (
    <div
      className="mb-6 rounded-lg border border-amber-700/60 bg-amber-950/40 px-4 py-3 text-sm text-amber-100"
      role="alert"
    >
      <p className="font-medium">Analysis server is not running</p>
      <p className="mt-1 text-amber-200/90 leading-relaxed">
        The web page cannot talk to the backend API. In PowerShell, from your{" "}
        <strong className="font-normal text-white">poker_ai</strong> folder run:{" "}
        <code className="text-emerald-300 bg-slate-900 px-1 rounded">python -m poker_ai serve</code>
        . Keep that terminal open, then reload this page.
      </p>
      <p className="mt-2 text-xs text-amber-300/80">
        If you only started the web dev server (Vite), that is not enough — serve starts both API and
        web together. Large folder scans can make the server look busy for a minute — wait and reload
        before assuming it is down.
      </p>
    </div>
  );
}
