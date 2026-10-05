export default function MetricCard({ title, value, caption, icon: Icon, tone = "indigo", id }) {
  const tones = {
    indigo: "bg-indigo-50 text-library-600",
    blue: "bg-sky-50 text-sky-600",
    green: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
  };

  return (
    <article id={id} className="scroll-mt-24 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{value ?? "—"}</p>
          <p className="mt-1.5 text-xs text-slate-400">{caption}</p>
        </div>
        <div className={`grid size-11 shrink-0 place-items-center rounded-xl ${tones[tone]}`}>
          <Icon size={22} strokeWidth={2} />
        </div>
      </div>
    </article>
  );
}

