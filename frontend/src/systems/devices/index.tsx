import { Link } from "react-router-dom";
import { Scan, Smartphone } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const PICKING_STATIONS = ["STA-01", "STA-02", "STA-03"];

const planned = [
  { label: "Device registry", description: "Handheld scanners, tablets, label printers, fixed scanners, and displays" },
  { label: "Status monitoring", description: "Live status — ONLINE · OFFLINE · CHARGING · ERROR with last-seen timestamps" },
  { label: "Battery tracking", description: "Battery percentage per device with low-battery alerts" },
  { label: "Firmware management", description: "Track firmware versions and flag devices needing updates" },
  { label: "Location assignment", description: "Assign devices to picking zones and charging stations" },
];

export default function DevicesOverview() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Smartphone className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-semibold">Devices</h1>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Scan className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-medium">Picking Stations</h2>
        </div>
        <div className="flex gap-3">
          {PICKING_STATIONS.map((sid) => (
            <Button key={sid} variant="outline" asChild className="gap-2">
              <Link to={`/devices/picking/${sid}`}>
                <Scan className="h-4 w-4" />
                {sid}
              </Link>
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Open a station to show the operator picking UI. URL:{" "}
          <code className="bg-muted px-1 py-0.5 rounded text-xs">/devices/picking/STA-01</code>
        </p>
      </div>

      <div className="border-t pt-4">
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-base font-medium text-muted-foreground">Planned features</h2>
          <Badge variant="secondary">Scaffolded</Badge>
        </div>
        <p className="text-muted-foreground text-sm max-w-xl mb-4">
          The Devices system manages all digital hardware on the warehouse floor — handhelds,
          tablets, printers, and scanners. API endpoints are registered at{" "}
          <code className="text-xs bg-muted px-1 py-0.5 rounded">/api/devices</code>.
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
    </div>
  );
}
