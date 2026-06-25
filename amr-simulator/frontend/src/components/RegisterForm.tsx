import { useState } from "react";
import { useRegisterAMR } from "../hooks/useSimulator";

export function RegisterForm() {
  const [name, setName]   = useState("");
  const [x, setX]         = useState("0");
  const [y, setY]         = useState("0");
  const register = useRegisterAMR();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    register.mutate(
      { name: name.trim(), x: parseFloat(x) || 0, y: parseFloat(y) || 0 },
      {
        onSuccess: () => setName(""),
        onError: () => alert("Failed to register AMR"),
      }
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">Name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. AMR-1"
          className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          required
        />
      </div>
      <div className="flex gap-2">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-600">Start X</label>
          <input
            type="number"
            value={x}
            onChange={(e) => setX(e.target.value)}
            className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-600">Start Y</label>
          <input
            type="number"
            value={y}
            onChange={(e) => setY(e.target.value)}
            className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={register.isPending}
        className="w-full rounded bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {register.isPending ? "Registering…" : "Register AMR"}
      </button>
    </form>
  );
}
