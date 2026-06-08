type Props = {
  title: string;
  description: string;
};

/** Consistent plain-language page header for non-technical users. */
export default function PageIntro({ title, description }: Props) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
      <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">{description}</p>
    </div>
  );
}
