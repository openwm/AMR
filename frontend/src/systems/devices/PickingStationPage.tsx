import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, Loader2, PackageOpen } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAdvanceTask, useCompleteTask, useExceptionTask, useStationQueue } from "@/systems/wcs/api";
import { useSalesOrder } from "@/systems/wms/outbound/api";
import type { PickTask } from "@/systems/wcs/types";

// ── Sub-components ────────────────────────────────────────────────────────────

function PickSquare({
  label,
  active = false,
  children,
}: {
  label: string;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3">
      <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <div
        className={cn(
          "flex h-52 w-52 flex-col items-center justify-center rounded-2xl border-2 transition-all duration-500",
          active
            ? "border-blue-500 bg-blue-500 text-white shadow-xl shadow-blue-200 dark:shadow-blue-900"
            : "border-border bg-muted text-muted-foreground"
        )}
      >
        {children}
      </div>
    </div>
  );
}

function TargetContent({ orderId }: { orderId: number }) {
  const { data: so } = useSalesOrder(orderId);
  return (
    <>
      <PackageOpen className="h-12 w-12 opacity-40" />
      <p className="mt-3 text-sm font-medium">Outbound</p>
      {so && (
        <p className="mt-1 font-mono text-xs opacity-60">{so.reference}</p>
      )}
    </>
  );
}

function PickingView({
  task,
  stationId,
  onDone,
}: {
  task: PickTask | null;
  stationId: string;
  onDone: () => void;
}) {
  const advance = useAdvanceTask();
  const complete = useCompleteTask();
  const exception = useExceptionTask();
  const busy = advance.isPending || complete.isPending || exception.isPending;

  const handleConfirm = async () => {
    if (!task) return;
    if (task.status === "at_dock") {
      await advance.mutateAsync({ stationId, taskId: task.id });
    }
    await complete.mutateAsync({ stationId, taskId: task.id });
    onDone();
  };

  const handleException = async () => {
    if (!task) return;
    await exception.mutateAsync({ stationId, taskId: task.id });
    onDone();
  };

  const isActive = task?.status === "at_dock";

  return (
    <div className="flex flex-col items-center gap-10">
      {/* Two squares */}
      <div className="flex items-center gap-6">
        {/* Source — turns blue when AMR has arrived */}
        <PickSquare label="Source" active={isActive}>
          {isActive && task ? (
            <>
              <span className="text-8xl font-bold tabular-nums leading-none">
                {task.quantity}
              </span>
              <span className="mt-3 font-mono text-sm opacity-80">{task.product_sku}</span>
            </>
          ) : (
            <>
              <Loader2 className="h-10 w-10 animate-spin opacity-30" />
              <span className="mt-3 text-xs opacity-50">Waiting for AMR…</span>
            </>
          )}
        </PickSquare>

        <ArrowRight className="h-8 w-8 shrink-0 text-muted-foreground" />

        {/* Target — static outbound destination */}
        <PickSquare label="Target">
          {task ? (
            <TargetContent orderId={task.order_id} />
          ) : (
            <>
              <PackageOpen className="h-12 w-12 opacity-20" />
              <p className="mt-3 text-sm opacity-40">Outbound</p>
            </>
          )}
        </PickSquare>
      </div>

      {/* Action buttons — only visible when there is an active task */}
      {task && (
        <div className="flex gap-3">
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
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

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
      setActiveTask(atDockTask);
    } else if (!atDockTask && activeTask?.status === "completed") {
      setActiveTask(null);
    }
  }, [queue, activeTask]);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
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

      {/* Picking squares — always rendered; source animates to blue on task arrival */}
      <div className="flex justify-center py-8">
        <PickingView
          task={activeTask}
          stationId={sid}
          onDone={() => setActiveTask(null)}
        />
      </div>

      {/* Queue depth footer */}
      {queue && queue.queue_depth > 0 && (
        <p className="text-center text-xs text-muted-foreground">
          {queue.queue_depth} task{queue.queue_depth !== 1 ? "s" : ""} in queue
          {" · "}
          {queue.picks_per_hour} picks/hr
        </p>
      )}
    </div>
  );
}
