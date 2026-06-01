import { Link, NavLink, Route, Routes } from "react-router-dom";
import { BarChart3, Boxes, CalendarCheck, Cpu, PackageOpen, Smartphone, Truck, Wrench } from "lucide-react";

import { cn } from "@/lib/utils";

import InboundRoutes from "@/systems/wms/inbound";
import InventoryRoutes from "@/systems/wms/inventory";
import OutboundRoutes from "@/systems/wms/outbound";
import PlanningRoutes from "@/systems/wms/planning";
import Dashboard from "@/systems/wms/reporting/Dashboard";
import StationQueueManager from "@/systems/wcs";
import EquipmentOverview from "@/systems/equipment";
import DevicesOverview from "@/systems/devices";
import PickingStationPage from "@/systems/devices/PickingStationPage";

type NavLink = { to: string; label: string; icon: React.ElementType; end?: boolean };

const nav: { label: string; links: NavLink[] }[] = [
  {
    label: "WMS",
    links: [
      { to: "/", label: "Dashboard", icon: BarChart3, end: true },
      { to: "/inventory", label: "Inventory", icon: Boxes },
      { to: "/inbound", label: "Inbound", icon: PackageOpen },
      { to: "/outbound", label: "Outbound", icon: Truck },
      { to: "/planning", label: "Planning", icon: CalendarCheck },
    ],
  },
  {
    label: "WCS",
    links: [
      { to: "/wcs/stations", label: "Station Queue", icon: Cpu },
    ],
  },
  {
    label: "Equipment",
    links: [
      { to: "/equipment", label: "Overview", icon: Wrench },
    ],
  },
  {
    label: "Devices",
    links: [
      { to: "/devices", label: "Overview", icon: Smartphone },
    ],
  },
];

function Sidebar() {
  return (
    <aside className="flex w-56 flex-col border-r bg-muted/30 p-4">
      <Link to="/" className="mb-6 text-lg font-semibold">
        OpenWM
      </Link>
      <nav className="flex flex-col gap-4">
        {nav.map((section, i) => (
          <div key={section.label}>
            {i > 0 && <div className="mb-3 border-t" />}
            <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
              {section.label}
            </p>
            <div className="flex flex-col gap-0.5">
              {section.links.map((l) => (
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
            </div>
          </div>
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
          <Route path="/planning/*" element={<PlanningRoutes />} />
          <Route path="/wcs/stations" element={<StationQueueManager />} />
          <Route path="/equipment" element={<EquipmentOverview />} />
          <Route path="/devices" element={<DevicesOverview />} />
          <Route path="/devices/picking/:stationId" element={<PickingStationPage />} />
        </Routes>
      </main>
    </div>
  );
}
