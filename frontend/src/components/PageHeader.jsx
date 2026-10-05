export default function PageHeader({ eyebrow, title, description }) {
  return (
    <div className="mb-6">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-library-600">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title}</h2>
      <p className="mt-1.5 text-sm text-slate-500">{description}</p>
    </div>
  );
}

