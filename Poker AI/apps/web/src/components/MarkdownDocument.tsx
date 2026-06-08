import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const mdComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4 mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-semibold text-slate-800 mt-8 mb-3">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-slate-700 mt-6 mb-2">{children}</h3>
  ),
  p: ({ children }) => <p className="text-[15px] leading-relaxed text-slate-700 mb-3">{children}</p>,
  ul: ({ children }) => (
    <ul className="list-disc pl-5 mb-4 space-y-1 text-slate-700 text-[15px]">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 mb-4 space-y-1 text-slate-700 text-[15px]">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ href, children }) => (
    <a href={href} className="text-emerald-700 underline hover:text-emerald-900">
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-slate-200 shadow-sm">
      <table className="w-full min-w-[32rem] border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-slate-100">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-slate-200 bg-white">{children}</tbody>,
  tr: ({ children }) => <tr className="hover:bg-slate-50/80">{children}</tr>,
  th: ({ children }) => (
    <th className="border-b border-slate-200 px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2.5 text-slate-800 align-top">{children}</td>
  ),
  code: ({ className, children }) => {
    const inline = !className;
    if (inline) {
      return (
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[13px] font-mono text-slate-800">
          {children}
        </code>
      );
    }
    return (
      <code className="block overflow-x-auto rounded-md bg-slate-900 p-3 text-[13px] font-mono text-slate-100">
        {children}
      </code>
    );
  },
  hr: () => <hr className="my-6 border-slate-200" />,
};

export default function MarkdownDocument({ markdown }: { markdown: string }) {
  return (
    <div className="doc-sheet rounded-xl border border-slate-200 bg-white px-6 py-8 sm:px-10 shadow-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
