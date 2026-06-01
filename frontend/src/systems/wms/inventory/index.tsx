import { NavLink, Route, Routes } from "react-router-dom";

import { cn } from "@/lib/utils";

import LocationsPage from "./LocationsPage";
import MovementsPage from "./MovementsPage";
import ProductsPage from "./ProductsPage";
import StockPage from "./StockPage";

const TABS = [
  { to: "", label: "Products", end: true },
  { to: "locations", label: "Locations" },
  { to: "stock", label: "Stock" },
  { to: "movements", label: "Movements" },
];

export default function InventoryRoutes() {
  return (
    <div className="space-y-4">
      <nav className="flex gap-1 border-b">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.end}
            className={({ isActive }) =>
              cn(
                "border-b-2 px-4 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )
            }
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route index element={<ProductsPage />} />
        <Route path="locations" element={<LocationsPage />} />
        <Route path="stock" element={<StockPage />} />
        <Route path="movements" element={<MovementsPage />} />
      </Routes>
    </div>
  );
}
