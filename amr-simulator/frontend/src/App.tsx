import { useLayout, useFleet } from "./hooks/useSimulator";
import { WarehouseMap } from "./components/WarehouseMap";
import { AMRPanel } from "./components/AMRPanel";
import { DispatchForm } from "./components/DispatchForm";
import { RegisterForm } from "./components/RegisterForm";

export default function App() {
  const { data: layout, isLoading, error } = useLayout();
  const amrs = useFleet();

  return (
    <div className="flex h-screen flex-col bg-slate-100">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-slate-800">AMR Simulator</span>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
            OpenWM
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              layout ? "bg-green-500" : "bg-amber-400"
            }`}
          />
          {layout ? `${amrs.length} AMR${amrs.length !== 1 ? "s" : ""} registered` : "Connecting…"}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Map (left) */}
        <main className="flex-1 overflow-auto p-4">
          {isLoading && (
            <div className="flex h-full items-center justify-center text-slate-500">
              Loading warehouse layout…
            </div>
          )}
          {error && (
            <div className="flex h-full items-center justify-center text-red-500">
              Could not reach AMR simulator backend. Make sure it is running on port 8001.
            </div>
          )}
          {layout && (
            <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              <WarehouseMap layout={layout} amrs={amrs} />
            </div>
          )}
        </main>

        {/* Sidebar (right) */}
        <aside className="flex w-72 flex-col gap-4 overflow-y-auto border-l border-slate-200 bg-white p-4">
          {/* Fleet status */}
          <section>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Fleet
            </h2>
            <AMRPanel amrs={amrs} />
          </section>

          <hr className="border-slate-100" />

          {/* Dispatch */}
          <section>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Dispatch AMR
            </h2>
            {layout ? (
              <DispatchForm amrs={amrs} layout={layout} />
            ) : (
              <p className="text-xs text-slate-400">Waiting for layout…</p>
            )}
          </section>

          <hr className="border-slate-100" />

          {/* Register */}
          <section>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Register AMR
            </h2>
            <RegisterForm />
          </section>
        </aside>
      </div>
    </div>
  );
}
