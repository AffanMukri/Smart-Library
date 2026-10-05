import { Cloud, CloudOff } from "lucide-react";

export default function TopBar({ connected }) {
  return (
    <header className="sticky top-0 z-20 flex h-18 items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-md sm:px-7 lg:h-20 lg:px-9">
      <div>
        <h1 className="text-base font-bold tracking-tight text-slate-900 sm:text-xl">Smart Library Automation System</h1>
        <p className="mt-0.5 hidden text-xs text-slate-400 sm:block">Live operations and environmental monitoring</p>
      </div>
      <div
        className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold ${
          connected
            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
            : "border-red-200 bg-red-50 text-red-700"
        }`}
      >
        {connected ? <Cloud size={15} /> : <CloudOff size={15} />}
        <span className="hidden sm:inline">BACKEND</span> {connected ? "ONLINE" : "OFFLINE"}
      </div>
    </header>
  );
}

