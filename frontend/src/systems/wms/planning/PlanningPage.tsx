import { useState } from "react";
import { CheckCircle2, Play, Send, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSalesOrders } from "@/systems/wms/outbound/api";

import {
  useNewOrdersAvailability,
  usePlanningConfig,
  useReleaseToWcs,
  useRunPlanning,
  useUpdatePlanningConfig,
} from "./api";
import type { PlanningResult, ReleaseResult } from "./types";

function ConfigCard() {
  const { data: config, isLoading } = usePlanningConfig();
  const updateConfig = useUpdatePlanningConfig();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");

  const startEdit = () => {
    setValue(String(config?.max_active_orders ?? 10));
    setEditing(true);
  };

  const save = async () => {
    const n = parseInt(value, 10);
    if (!isNaN(n) && n > 0) {
      await updateConfig.mutateAsync(n);
    }
    setEditing(false);
  };

  if (isLoading) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Planning Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <Label className="text-sm text-muted-foreground">Max active orders at once</Label>
          {editing ? (
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-24"
                autoFocus
              />
              <Button size="sm" onClick={save} disabled={updateConfig.isPending}>
                Save
              </Button>
              <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold">{config?.max_active_orders}</span>
              <Button size="sm" variant="outline" onClick={startEdit}>
                Edit
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function RunPlanningCard() {
  const runPlanning = useRunPlanning();
  const [lastResult, setLastResult] = useState<PlanningResult | null>(null);

  const handleRun = async () => {
    const result = await runPlanning.mutateAsync();
    setLastResult(result);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run Planning</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <Button onClick={handleRun} disabled={runPlanning.isPending} className="gap-2">
          <Play className="h-4 w-4" />
          {runPlanning.isPending ? "Planningâ€¦" : "Run Planning"}
        </Button>
        {lastResult && (
          <div className="flex gap-4 text-sm">
            <span className="text-green-600 font-medium">
              {lastResult.activated} activated
            </span>
            <span className="text-muted-foreground">
              {lastResult.skipped} skipped
            </span>
            <span className="text-muted-foreground">
              {lastResult.slots_remaining} slot{lastResult.slots_remaining !== 1 ? "s" : ""} remaining
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function NewOrdersTable() {
  const { data: orders = [], isLoading } = useNewOrdersAvailability();

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Orders</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Reference</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Received</TableHead>
              <TableHead>Stock Available</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  Loadingâ€¦
                </TableCell>
              </TableRow>
            ) : orders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No new orders
                </TableCell>
              </TableRow>
            ) : (
              orders.map((o) => (
                <TableRow key={o.so_id}>
                  <TableCell className="font-mono">{o.reference}</TableCell>
                  <TableCell>{o.customer}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(o.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {o.can_fulfill ? (
                      <span className="flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        Available
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-500">
                        <XCircle className="h-4 w-4" />
                        Insufficient stock
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function ReleaseToWCSCard() {
  const releaseToWcs = useReleaseToWcs();
  const [lastResult, setLastResult] = useState<ReleaseResult | null>(null);

  const handleRelease = async () => {
    const result = await releaseToWcs.mutateAsync();
    setLastResult(result);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Release to WCS</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <Button onClick={handleRelease} disabled={releaseToWcs.isPending} variant="outline" className="gap-2">
          <Send className="h-4 w-4" />
          {releaseToWcs.isPending ? "Releasing…" : "Release to WCS"}
        </Button>
        {lastResult && (
          <div className="flex gap-4 text-sm">
            <span className="text-blue-600 font-medium">
              {lastResult.released} released
            </span>
            <span className="text-muted-foreground">
              {lastResult.skipped} skipped
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ActiveOrdersTable() {
  const { data: sos = [], isLoading } = useSalesOrders();
  const activeOrders = sos.filter((s) => s.status === "ACTIVE");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Orders</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Reference</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Received</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  Loadingâ€¦
                </TableCell>
              </TableRow>
            ) : activeOrders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No active orders â€” run planning to activate orders
                </TableCell>
              </TableRow>
            ) : (
              activeOrders.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="font-mono">{o.reference}</TableCell>
                  <TableCell>{o.customer}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(o.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant="success">ACTIVE</Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function PlanningPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Planning</h1>
      <div className="grid grid-cols-3 gap-4">
        <ConfigCard />
        <RunPlanningCard />
        <ReleaseToWCSCard />
      </div>
      <NewOrdersTable />
      <ActiveOrdersTable />
    </div>
  );
}
