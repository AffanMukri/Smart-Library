import { Outlet } from "react-router-dom";
import { useLibrary } from "../hooks/useLibrary";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function AppLayout() {
  const { connected, error, dataError, loading } = useLibrary();

  return (
    <div className="min-h-screen bg-[#f5f7fb]">
      <Sidebar />
      <div className="lg:pl-64">
        <TopBar connected={connected} />
        <main className="mx-auto max-w-[1500px] px-4 py-6 sm:px-7 sm:py-8 lg:px-9">
          {!connected && !loading && (
            <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              Backend connection failed{error ? `: ${error}` : "."} Live values may be out of date.
            </div>
          )}
          {connected && dataError && (
            <div role="status" className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Some dashboard data could not be refreshed: {dataError}
            </div>
          )}
          <Outlet />
          <footer className="mt-7 border-t border-slate-200 py-5 text-center text-xs text-slate-400">
            Smart Library Automation · Real-time IoT monitoring
          </footer>
        </main>
      </div>
    </div>
  );
}
