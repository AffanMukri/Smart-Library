import { useCallback, useEffect, useState } from "react";
import { getAnalytics, getBooks, getDashboard, getDevices, getEvents, getLoans, getStudents } from "../services/api";
export function useLibraryDashboard(intervalMs = 1500) {
  const [data, setData] = useState({ dashboard: null, events: [], analytics: null, devices: [], books: [], students: [], loans: [] });
  const [connected, setConnected] = useState(false), [loading, setLoading] = useState(true), [error, setError] = useState(null), [dataError, setDataError] = useState(null);
  const refresh = useCallback(async (signal) => {
    const calls = [getDashboard(signal), getEvents(signal), getAnalytics(signal), getDevices(signal), getBooks(signal), getStudents(signal), getLoans(signal)];
    const results = await Promise.allSettled(calls); if (signal?.aborted) return;
    const names = ["dashboard", "events", "analytics", "devices", "bookPayload", "students", "loans"];
    const next = {}; results.forEach((result, index) => { if (result.status === "fulfilled") next[names[index]] = result.value; });
    if (next.dashboard) { setConnected(true); setError(null); } else { setConnected(false); setError(results[0].reason?.message ?? "Backend unavailable"); }
    setData((old) => ({ ...old, ...next, books: next.bookPayload?.items ?? old.books }));
    const failures = results.slice(1).filter((x) => x.status === "rejected" && x.reason?.name !== "AbortError").map((x) => x.reason?.message);
    setDataError(failures.length ? failures.join("; ") : null); setLoading(false);
  }, []);
  useEffect(() => { const controller = new AbortController(); const initial = setTimeout(() => refresh(controller.signal), 0); const timer = setInterval(() => refresh(controller.signal), intervalMs); return () => { controller.abort(); clearTimeout(initial); clearInterval(timer); }; }, [intervalMs, refresh]);
  return { ...data, connected, loading, error, dataError, refresh: () => refresh() };
}
