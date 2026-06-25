import type { AMR } from "../types";

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  idle:        { label: "Idle",       cls: "bg-slate-100 text-slate-600" },
  traveling:   { label: "Traveling",  cls: "bg-blue-100 text-blue-700" },
  at_location: { label: "Arrived",    cls: "bg-green-100 text-green-700" },
};

interface Props {
  amrs: AMR[];
}

export function AMRPanel({ amrs }: Props) {
  if (amrs.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-center text-sm text-slate-500">
        No AMRs registered yet. Use the form below to add one.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="px-3 py-2 text-left font-medium">AMR</th>
            <th className="px-3 py-2 text-left font-medium">Status</th>
            <th className="px-3 py-2 text-left font-medium">Target</th>
            <th className="px-3 py-2 text-right font-medium">Pos</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {amrs.map((amr) => {
            const badge = STATUS_BADGE[amr.status] ?? STATUS_BADGE.idle;
            return (
              <tr key={amr.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium text-slate-800">{amr.name}</td>
                <td className="px-3 py-2">
                  <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${badge.cls}`}>
                    {badge.label}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-500">
                  {amr.target_location ?? "—"}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs text-slate-400">
                  ({amr.x.toFixed(1)}, {amr.y.toFixed(1)})
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
