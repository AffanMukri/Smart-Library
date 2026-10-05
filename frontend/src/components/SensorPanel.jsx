import { DoorOpen, Lightbulb, Radio, Ruler } from "lucide-react";

function Reading({ icon: Icon, label, value, detail, id }) {
  return (
    <div id={id} className="scroll-mt-24 flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50/70 p-4">
      <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-white text-library-600 shadow-sm">
        <Icon size={19} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-slate-400">{label}</p>
        <p className="mt-0.5 truncate text-base font-bold text-slate-800">{value ?? "—"}</p>
      </div>
      <span className="text-right text-[11px] font-medium text-slate-400">{detail}</span>
    </div>
  );
}

export default function SensorPanel({ state }) {
  const operational = state?.system_status === "ONLINE";

  return (
    <section id="sensors" className="scroll-mt-24 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50 sm:p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="font-bold tracking-tight text-slate-900">Sensor monitoring</h2>
          <p className="mt-1 text-xs text-slate-400">Current IoT telemetry</p>
        </div>
        <span className={`flex items-center gap-2 text-xs font-semibold ${operational ? "text-emerald-600" : "text-red-600"}`}>
          <span className={`size-2 rounded-full ${operational ? "bg-emerald-500" : "bg-red-500"}`} />
          {state?.system_status ?? "UNKNOWN"}
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Reading icon={Ruler} label="Ultrasonic distance" value={state?.distance == null ? null : `${state.distance} cm`} detail="HC-SR04" />
        <Reading icon={Radio} label="LDR raw reading" value={state?.light} detail="0–1023" />
        <Reading id="entrance" icon={DoorOpen} label="Door state" value={state?.door} detail="Smart entrance" />
        <Reading id="lighting" icon={Lightbulb} label="Lighting state" value={state?.lights} detail="Auto lighting" />
      </div>
    </section>
  );
}

