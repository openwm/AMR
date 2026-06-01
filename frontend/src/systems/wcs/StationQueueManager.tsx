import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronRight, Package, Zap } from "lucide-react";

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

import {
  useAdvanceTask,
  useCompleteTask,
  useCreateTask,
  useExceptionTask,
  useStationQueue,
  useStations,
} from "./api";
import type { CreateTaskRequest, PickTask, StationSummary, TaskStatus } from "./types";

// ── Status badge ─────────────────────────────────────────────────────────────

const STATUS_VARIANT: Record<TaskStatus, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  queued: "secondary",
  at_dock: "warning",
  picking: "default",
  completed: "success",
  exception: "destructive",
};

function StatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge variant={STATUS_VARIANT[status]}>
      {status.replace("_", " ")}
    </Badge>
  );
}

// ── Station card ──────────────────────────────────────────────────────────────

function StationCard({
  station,
  selected,
  onClick,
}: {
  station: StationSummary;
  selected: boolean;
  onClick: () => void;
}) {
  const depthPct = Math.min(100, (station.queue_depth / 5) * 100);
  const amrPct = Math.min(100, (station.amr_count / 3) * 100);

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border p-4 transition-colors ${
        selected
          ? "border-primary bg-primary/5"
          : "hover:border-muted-foreground/40 hover:bg-muted/40"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold text-sm">{station.station_id}</span>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="space-y-2">
        <Gauge label="Queue" value={station.queue_depth} max={5} pct={depthPct} />
        <Gauge label="AMRs" value={station.amr_count} max={3} pct={amrPct} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            Picks/hr
          </span>
          <span className="font-medium text-foreground">
            {station.picks_per_hour.toFixed(0)}
          </span>
        </div>
      </div>
    </button>
  );
}

function Gauge({
  label,
  value,
  max,
  pct,
}: {
  label: string;
  value: number;
  max: number;
  pct: number;
}) {
  const color =
    pct >= 100 ? "bg-destructive" : pct >= 60 ? "bg-amber-400" : "bg-primary";
  return (
    <div>
      <div className="flex justify-between text-xs mb-0.5">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {value}/{max}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Task row actions ──────────────────────────────────────────────────────────

function TaskActions({ task }: { task: PickTask }) {
  const advance = useAdvanceTask();
  const complete = useCompleteTask();
  const exception = useExceptionTask();

  const args = { stationId: task.station_id, taskId: task.id };
  const busy = advance.isPending || complete.isPending || exception.isPending;

  return (
    <div className="flex gap-1 justify-end">
      {task.status === "at_dock" && (
        <Button
          size="sm"
          variant="outline"
          disabled={busy}
          onClick={() => advance.mutate(args)}
        >
          Advance
        </Button>
      )}
      {task.status === "picking" && (
        <Button
          size="sm"
          disabled={busy}
          onClick={() => complete.mutate(args)}
          className="gap-1"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          Complete
        </Button>
      )}
      {(task.status === "at_dock" || task.status === "picking") && (
        <Button
          size="sm"
          variant="destructive"
          disabled={busy}
          onClick={() => exception.mutate(args)}
          className="gap-1"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Exception
        </Button>
      )}
    </div>
  );
}

// ── Queue panel ───────────────────────────────────────────────────────────────

function QueuePanel({ stationId }: { stationId: string }) {
  const { data, isLoading } = useStationQueue(stationId);

  return (
    <Card className="flex-1">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{stationId} — Queue</span>
          <span className="text-sm font-normal text-muted-foreground">
            {data?.picks_per_hour.toFixed(0)} picks/hr
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Qty</TableHead>
              <TableHead>Deadline</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : !data?.tasks.length ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  Queue empty
                </TableCell>
              </TableRow>
            ) : (
              data.tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell className="font-mono text-sm">{task.product_sku}</TableCell>
                  <TableCell>{task.quantity}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(task.deadline).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={task.status} />
                  </TableCell>
                  <TableCell>
                    <TaskActions task={task} />
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

// ── Create task form ──────────────────────────────────────────────────────────

const EMPTY_FORM: CreateTaskRequest = {
  order_id: 0,
  order_line_id: 0,
  product_id: 0,
  product_sku: "",
  quantity: 1,
  deadline: new Date(Date.now() + 86_400_000).toISOString().slice(0, 16),
};

function CreateTaskForm() {
  const [form, setForm] = useState<CreateTaskRequest>(EMPTY_FORM);
  const createTask = useCreateTask();

  const set = (k: keyof CreateTaskRequest, v: string | number) =>
    setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    await createTask.mutateAsync({
      ...form,
      deadline: new Date(form.deadline).toISOString(),
    });
    setForm(EMPTY_FORM);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Package className="h-4 w-4" />
          Create Pick Task
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div>
            <Label className="text-xs">Order ID</Label>
            <Input
              type="number"
              value={form.order_id || ""}
              onChange={(e) => set("order_id", parseInt(e.target.value) || 0)}
            />
          </div>
          <div>
            <Label className="text-xs">Order Line ID</Label>
            <Input
              type="number"
              value={form.order_line_id || ""}
              onChange={(e) => set("order_line_id", parseInt(e.target.value) || 0)}
            />
          </div>
          <div>
            <Label className="text-xs">Product ID</Label>
            <Input
              type="number"
              value={form.product_id || ""}
              onChange={(e) => set("product_id", parseInt(e.target.value) || 0)}
            />
          </div>
          <div>
            <Label className="text-xs">Product SKU</Label>
            <Input
              value={form.product_sku}
              onChange={(e) => set("product_sku", e.target.value)}
              placeholder="ELE-001"
            />
          </div>
          <div>
            <Label className="text-xs">Quantity</Label>
            <Input
              type="number"
              min={1}
              value={form.quantity}
              onChange={(e) => set("quantity", parseInt(e.target.value) || 1)}
            />
          </div>
          <div>
            <Label className="text-xs">Deadline</Label>
            <Input
              type="datetime-local"
              value={form.deadline}
              onChange={(e) => set("deadline", e.target.value)}
            />
          </div>
        </div>
        <Button
          onClick={submit}
          disabled={createTask.isPending || !form.product_sku}
          className="w-full"
        >
          {createTask.isPending ? "Dispatching…" : "Dispatch to best station"}
        </Button>
        {createTask.isError && (
          <p className="text-sm text-destructive mt-2">
            {(createTask.error as Error).message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function StationQueueManager() {
  const { data: stations = [] } = useStations();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Station Queue Manager</h1>

      <div className="flex gap-6 items-start">
        {/* Station list */}
        <div className="w-52 shrink-0 flex flex-col gap-2">
          {stations.map((s) => (
            <StationCard
              key={s.station_id}
              station={s}
              selected={selected === s.station_id}
              onClick={() => setSelected(s.station_id)}
            />
          ))}
        </div>

        {/* Right panel */}
        <div className="flex-1 flex flex-col gap-4">
          <CreateTaskForm />
          {selected ? (
            <QueuePanel stationId={selected} />
          ) : (
            <div className="flex items-center justify-center h-48 rounded-lg border border-dashed text-muted-foreground text-sm">
              Select a station to view its queue
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
