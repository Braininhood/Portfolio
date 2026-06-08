import { ReactNode } from "react";

export function Card({
  title,
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/60 p-4 shadow">
      {title ? <h2 className="text-base font-medium mb-3 text-slate-200">{title}</h2> : null}
      {children}
    </section>
  );
}
