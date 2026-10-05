import StatusBadge from "./StatusBadge";
export default function DeviceCard({ icon: Icon, name, status, reading, purpose, source }) {
  return <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50">
    <div className="flex items-start justify-between gap-3"><div className="grid size-11 place-items-center rounded-xl bg-indigo-50 text-library-600"><Icon size={22} /></div><StatusBadge>{status}</StatusBadge></div>
    <h3 className="mt-5 font-bold text-slate-900">{name}</h3><p className="mt-1 text-xl font-bold tracking-tight text-library-700">{reading ?? "—"}</p>
    {source && <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Source: {source.replaceAll("_", " ")}</p>}<p className="mt-3 text-sm leading-6 text-slate-500">{purpose}</p>
  </article>;
}
