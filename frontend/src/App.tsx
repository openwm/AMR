import { Link, NavLink, Route, Routes } from "react-router-dom";
import { BarChart3, Boxes, PackageOpen, Truck } from "lucide-react";

import { cn } from "@/lib/utils";

import InboundRoutes from "./features/inbound";
import InventoryRoutes from "./features/inventory";
import OutboundRoutes from "./features/outbound";
import Dashboard from "./features/reporting/Dashboard";

function Placeholder({ title }: { title: string }) {
  return (
    <div className="rounded-lg border bg-card p-8 text-card-foreground shadow-sm">
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        This module is part of the OpenWM scaffold. Pages will be filled in during the
        corresponding build phase.
      </p>
    </div>
  );
}

function Sidebar() {
  const links = [
    { to: "/", label: "Dashboard", icon: BarChart3, end: true },
    { to: "/inventory", label: "Inventory", icon: Boxes },
    { to: "/inbound", label: "Inbound", icon: PackageOpen },
    { to: "/outbound", label: "Outbound", icon: Truck },
  ];
  return (
    <aside className="flex w-56 flex-col border-r bg-muted/30 p-4">
      <Link to="/" className="mb-6 text-lg font-semibold">
        OpenWM
      </Link>
      <nav className="flex flex-col gap-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <l.icon className="h-4 w-4" />
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto pt-4 text-xs text-muted-foreground">
        OpenWM · demo build
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory/*" element={<InventoryRoutes />} />
          <Route path="/inbound/*" element={<InboundRoutes />} />
          <Route path="/outbound/*" element={<OutboundRoutes />} />
        </Routes>
      </main>
    </div>
  );
}
