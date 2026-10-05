import { BookDown, BookUp, DoorClosed, DoorOpen, Lightbulb, LightbulbOff, Radio } from "lucide-react";

const eventMeta = {
  BOOK_ISSUED: { label: "Book issued", detail: "Inventory updated", icon: BookUp, color: "text-indigo-600 bg-indigo-50" },
  BOOK_RETURNED: { label: "Book returned", detail: "Inventory updated", icon: BookDown, color: "text-emerald-600 bg-emerald-50" },
  DOOR_OPENED: { label: "Smart door opened", detail: "Person detected", icon: DoorOpen, color: "text-sky-600 bg-sky-50" },
  DOOR_CLOSED: { label: "Smart door closed", detail: "Entrance secured", icon: DoorClosed, color: "text-slate-600 bg-slate-100" },
  LIGHTS_ON: { label: "Library lights on", detail: "Low ambient light", icon: Lightbulb, color: "text-amber-600 bg-amber-50" },
  LIGHTS_OFF: { label: "Library lights off", detail: "Ambient light restored", icon: LightbulbOff, color: "text-slate-600 bg-slate-100" },
};

function formatTime(timestamp) {
  if (!timestamp) return "—";
  const normalized = /Z|[+-]\d\d:\d\d$/.test(timestamp) ? timestamp : `${timestamp}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(date);
}

export default function ActivityList({ events, loading }) {
  return (
    <section id="activity" className="scroll-mt-24 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50 sm:p-6">
      <div className="mb-5 flex items-end justify-between">
        <div>
          <h2 className="font-bold tracking-tight text-slate-900">Recent activity</h2>
          <p className="mt-1 text-xs text-slate-400">Latest system and inventory events</p>
        </div>
        <span className="text-xs font-semibold text-library-600">Last 50</span>
      </div>

      <div className="max-h-[390px] space-y-1 overflow-y-auto pr-1">
        {loading && events.length === 0 && <p className="py-12 text-center text-sm text-slate-400">Loading activity…</p>}
        {!loading && events.length === 0 && <p className="py-12 text-center text-sm text-slate-400">No activity recorded yet.</p>}
        {events.map((event) => {
          const meta = eventMeta[event.event] ?? eventMeta[event.event_type] ?? {
            label: (event.event ?? event.event_type).replaceAll("_", " "),
            detail: "System event",
            icon: Radio,
            color: "text-library-600 bg-indigo-50",
          };
          const Icon = meta.icon;
          return (
            <div key={event.id} className="flex items-center gap-3 rounded-xl px-2 py-3 transition-colors hover:bg-slate-50">
              <div className={`grid size-9 shrink-0 place-items-center rounded-lg ${meta.color}`}><Icon size={17} /></div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-700">{meta.label}</p>
                <p className="mt-0.5 text-xs text-slate-400">{meta.detail}{event.books != null ? ` · ${event.books} books available` : ""}</p>
              </div>
              <time className="text-xs tabular-nums text-slate-400">{formatTime(event.timestamp)}</time>
            </div>
          );
        })}
      </div>
    </section>
  );
}
