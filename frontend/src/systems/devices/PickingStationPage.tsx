import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, CheckCircle2, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAdvanceTask, useCompleteTask, useExceptionTask, useStationQueue } from "@/systems/wcs/api";
import { useSalesOrder } from "@/systems/wms/outbound/api";
import type { PickTask } from "@/systems/wcs/types";

function OrderInfo({ orderId }: { orderId: number }) {
  const { data: so } = useSalesOrder(orderId);
  if (!so) return null;
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      <span>Order: <span className="font-mono text-foreground">{so.reference}</span></span>
      <span>·</span>
      <span>Customer: <span className="text-foreground">{so.customer}</span></span>
    </div>
  );
}

function ActivePickCard({
  task,
  stationId,
  onDone,
}: {
  task: PickTask;
  stationId: string;
  onDone: () => void;
}) {
  const advance = useAdvanceTask();
  const complete = useCompleteTask();
  const exception = useExceptionTask();
  const busy = advance.isPending || complete.isPending || exception.isPending;

  const handleConfirm = async () => {
    if (task.status === "at_dock") {
      await advance.mutateAsync({ stationId, taskId: task.id });
    }
    await complete.mutateAsync({ stationId, taskId: task.id });
    onDone();
  };

  const handleException = async () => {
    await exception.mutateAsync({ stationId, taskId: task.id });
    onDone();
  };

  return (
    <Card className="border-2 border-primary shadow-lg">
      <CardContent className="flex flex-col items-center gap-6 p-10">
        <div className="flex items-center gap-2">
          <Badge variant="default" className="text-sm">AMR ARRIVED</Badge>
          <Badge variant="outline">{stationId}</Badge>
        </div>

        <div className="flex flex-col items-center gap-2 text-center">
          <p className="text-sm text-muted-foreground uppercase tracking-widest">SKU</p>
          <p className="font-mono text-4xl font-semibold">{task.product_sku}</p>
        </div>

        <div className="flex flex-col items-center gap-2 text-center">
          <p className="text-sm text-muted-foreground uppercase tracking-widest">Quantity to pick</p>
          <p className="text-7xl font-bold tabular-nums">{task.quantity}</p>
        </div>

        <OrderInfo orderId={task.order_id} />

        <div className="flex gap-3 pt-2">
          <Button
            size="lg"
            onClick={handleConfirm}
            disabled={busy}
            className="gap-2 px-8"
          >
            {busy ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <CheckCircle2 className="h-5 w-5" />
            )}
            Confirm Pick
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={handleException}
            disabled={busy}
            className="gap-2"
          >
            <AlertTriangle className="h-5 w-5" />
            Exception
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function PickingStationPage() {
  const { stationId } = useParams<{ stationId: string }>();
  const sid = stationId ?? "";

  const { data: queue } = useStationQueue(sid);

  const [activeTask, setActiveTask] = useState<PickTask | null>(null);
  const seenTaskIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!queue) return;
    const atDockTask = queue.tasks.find((t) => t.status === "at_dock") ?? null;

    if (atDockTask && !seenTaskIds.current.has(atDockTask.id)) {
      seenTaskIds.current.add(atDockTask.id);
      setActiveTask(atDockTask);
    } else if (atDockTask && !activeTask) {
      // Page reload — task already seen but still at_dock; show it
      setActiveTask(atDockTask);
    } else if (!atDockTask && activeTask?.status === "completed") {
      setActiveTask(null);
    }
  }, [queue, activeTask]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link
          to="/devices"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Devices
        </Link>
        <span className="text-muted-foreground">/</span>
        <h1 className="text-2xl font-semibold">Picking Station</h1>
        <Badge variant="outline" className="font-mono">{sid}</Badge>
      </div>

      {activeTask ? (
        <ActivePickCard
          task={activeTask}
          stationId={sid}
          onDone={() => setActiveTask(null)}
        />
      ) : (
        <div className="flex flex-col items-center justify-center gap-4 py-24 text-muted-foreground">
          <Loader2 className="h-10 w-10 animate-spin opacity-40" />
          <p className="text-lg">Waiting for next task…</p>
          <p className="text-sm">Station <span className="font-mono">{sid}</span> is idle</p>
        </div>
      )}

      {queue && queue.queue_depth > 0 && (
        <p className="text-center text-xs text-muted-foreground">
          {queue.queue_depth} task{queue.queue_depth !== 1 ? "s" : ""} in queue · {queue.picks_per_hour} picks/hr
        </p>
      )}
    </div>
  );
}
