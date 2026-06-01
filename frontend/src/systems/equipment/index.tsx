import { Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const planned = [
  { label: "Asset registry", description: "Track forklifts, conveyors, dock doors, cranes, and pallet jacks" },
  { label: "Status board", description: "Live availability — AVAILABLE · IN_USE · MAINTENANCE · OFFLINE" },
  { label: "Maintenance log", description: "Service history, upcoming schedules, technician notes" },
  { label: "Hours tracking", description: "Cumulative operating hours per asset with service-interval alerts" },
  { label: "Location mapping", description: "Assign assets to zones and dock positions" },
];

export default function EquipmentOverview() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Wrench className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-semibold">Equipment</h1>
        <Badge variant="secondary">Scaffolded</Badge>
      </div>

      <p className="text-muted-foreground max-w-xl">
        The Equipment system manages all physical warehouse hardware — powered equipment,
        fixed infrastructure, and dock assets. API endpoints are registered at{" "}
        <code className="text-xs bg-muted px-1 py-0.5 rounded">/api/equipment/assets</code>.
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {planned.map((f) => (
          <Card key={f.label} className="opacity-60">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">{f.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">{f.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
