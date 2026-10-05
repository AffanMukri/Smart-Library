import { Activity, Clock3 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#4359c7", "#10b981", "#38bdf8", "#f59e0b", "#64748b", "#8b5cf6"];

function ChartCard({ title, subtitle, children, empty = false }) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50">
      <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
      <div className="mt-5 h-56">
        {empty ? <div className="grid h-full place-items-center text-sm text-slate-400">Waiting for historical data…</div> : children}
      </div>
    </article>
  );
}

function timeLabel(value) {
  if (!value) return "";
  const normalized = /Z|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(normalized));
}

function formatUptime(seconds = 0) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m ${remainder}s`;
}

export default function AnalyticsPanel({ dashboard, analytics }) {
  const bookData = dashboard ? [
    { name: "Available", value: dashboard.books },
    { name: "Issued", value: dashboard.max_books - dashboard.books },
  ] : [];
  const history = analytics?.sensor_history ?? [];
  const eventData = (analytics?.event_distribution ?? []).map((item) => ({ ...item, label: item.name.replaceAll("_", " ") }));

  return (
    <section className="mt-5">
      <div className="mb-4 flex items-center gap-2">
        <Activity size={18} className="text-library-600" />
        <div><h2 className="font-bold text-slate-900">IoT analytics</h2><p className="text-xs text-slate-400">Historical readings and operational trends</p></div>
      </div>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <ChartCard title="Book availability" subtitle="Current inventory split" empty={!dashboard}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart><Pie data={bookData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={82} paddingAngle={3}>{bookData.map((entry, index) => <Cell key={entry.name} fill={COLORS[index]} />)}</Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Issue vs return" subtitle="All recorded transactions" empty={!analytics}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analytics?.transaction_counts ?? []} margin={{ left: -24, right: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" /><XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip /><Bar dataKey="count" fill="#4359c7" radius={[6, 6, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50">
          <h3 className="text-sm font-bold text-slate-900">System uptime</h3><p className="mt-1 text-xs text-slate-400">Current backend process</p>
          <div className="flex h-56 flex-col items-center justify-center">
            <div className="grid size-16 place-items-center rounded-2xl bg-emerald-50 text-emerald-600"><Clock3 size={29} /></div>
            <p className="mt-5 text-3xl font-bold tracking-tight text-slate-900">{formatUptime(analytics?.uptime_seconds)}</p>
            <span className={`mt-3 rounded-full px-3 py-1 text-xs font-bold ${analytics?.system_status === "ONLINE" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{analytics?.system_status ?? "UNKNOWN"}</span>
          </div>
        </article>

        <ChartCard title="LDR history" subtitle="Last 60 sensor samples" empty={history.length === 0}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history} margin={{ left: -22, right: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" /><XAxis dataKey="timestamp" tickFormatter={timeLabel} minTickGap={35} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 1023]} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip labelFormatter={timeLabel} /><Line type="monotone" dataKey="light" stroke="#f59e0b" strokeWidth={2.5} dot={false} /></LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Ultrasonic distance" subtitle="Last 60 sensor samples · cm" empty={history.length === 0}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history} margin={{ left: -22, right: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" /><XAxis dataKey="timestamp" tickFormatter={timeLabel} minTickGap={35} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip labelFormatter={timeLabel} /><Line type="monotone" dataKey="distance" stroke="#38bdf8" strokeWidth={2.5} dot={false} /></LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Event distribution" subtitle="Events grouped by type" empty={eventData.length === 0}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={eventData} layout="vertical" margin={{ left: 18, right: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" /><XAxis type="number" allowDecimals={false} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="label" width={90} tick={{ fontSize: 9 }} axisLine={false} tickLine={false} /><Tooltip /><Bar dataKey="count" fill="#596fe0" radius={[0, 6, 6, 0]} /></BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </section>
  );
}
