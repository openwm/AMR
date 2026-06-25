import { useState } from "react";
import type { AMR, WarehouseLayout } from "../types";
import { useDispatchAMR } from "../hooks/useSimulator";

interface Props {
  amrs: AMR[];
  layout: WarehouseLayout;
}

export function DispatchForm({ amrs, layout }: Props) {
  const [amrId, setAmrId]       = useState("");
  const [location, setLocation] = useState("");
  const dispatch = useDispatchAMR();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!amrId || !location.trim()) return;
    dispatch.mutate(
      { amrId, locationCode: location.trim().toUpperCase() },
      {
        onSuccess: () => setLocation(""),
        onError: (err) => {
          const msg = (err as { response?: { data?: { detail?: string } } })
            ?.response?.data?.detail ?? "Dispatch failed";
          alert(msg);
        },
      }
    );
  }

  const locationCodes = Object.keys(layout.locations);

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">AMR</label>
        <select
          value={amrId}
          onChange={(e) => setAmrId(e.target.value)}
          className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          required
        >
          <option value="">Select AMR…</option>
          {amrs.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.status})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">Location</label>
        <input
          list="location-codes"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. A-01-02 or STA-01"
          className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          required
        />
        <datalist id="location-codes">
          {locationCodes.map((code) => (
            <option key={code} value={code} />
          ))}
        </datalist>
      </div>

      <button
        type="submit"
        disabled={dispatch.isPending}
        className="w-full rounded bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {dispatch.isPending ? "Dispatching…" : "Dispatch AMR"}
      </button>
    </form>
  );
}
