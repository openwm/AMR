import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Plus, Search, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { useProducts } from "@/systems/wms/inventory/api";

import { useCreateSalesOrder, useSalesOrders } from "./api";
import type { SOStatus } from "./types";

const STATUS_VARIANT: Record<SOStatus, "default" | "success" | "warning" | "secondary" | "destructive"> = {
  DRAFT: "secondary",
  NEW: "default",
  ACTIVE: "success",
  PICKING: "default",
  PARTIAL: "warning",
  SHIPPED: "success",
  CLOSED: "secondary",
  CANCELLED: "destructive",
};

const ALL_STATUSES: SOStatus[] = ["DRAFT", "NEW", "ACTIVE", "PICKING", "PARTIAL", "SHIPPED", "CLOSED", "CANCELLED"];

export default function SalesOrdersPage() {
  const { data: sos = [], isLoading } = useSalesOrders();
  const { data: products = [] } = useProducts();
  const createSO = useCreateSalesOrder();

  const [selectedSoId, setSelectedSoId] = useState<number | null>(null);
  const [filterText, setFilterText] = useState("");
  const [filterStatus, setFilterStatus] = useState<SOStatus | "">("");
  const [splitPx, setSplitPx] = useState(280);
  const [dialogOpen, setDialogOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  const [form, setForm] = useState({
    reference: "",
    customer: "",
    requested_date: "",
    lines: [{ product_id: 0, qty_ordered: 1 }],
  });

  const addLine = () =>
    setForm({ ...form, lines: [...form.lines, { product_id: 0, qty_ordered: 1 }] });
  const removeLine = (i: number) =>
    setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createSO.mutateAsync({
      reference: form.reference,
      customer: form.customer,
      requested_date: form.requested_date || null,
      lines: form.lines.filter((l) => l.product_id > 0 && l.qty_ordered > 0),
    });
    setDialogOpen(false);
    setForm({ reference: "", customer: "", requested_date: "", lines: [{ product_id: 0, qty_ordered: 1 }] });
  };

  const filteredSos = useMemo(() => {
    const text = filterText.toLowerCase();
    return sos.filter((so) => {
      if (filterStatus && so.status !== filterStatus) return false;
      if (text && !so.reference.toLowerCase().includes(text) && !so.customer.toLowerCase().includes(text)) return false;
      return true;
    });
  }, [sos, filterText, filterStatus]);

  const selectedSo = sos.find((s) => s.id === selectedSoId) ?? null;
  const productById = (pid: number) => products.find((p) => p.id === pid);

  const onDragStart = (e: React.MouseEvent) => {
    e.preventDefault();
    const container = containerRef.current;
    if (!container) return;

    const move = (ev: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const next = ev.clientY - rect.top;
      setSplitPx(Math.max(120, Math.min(rect.height - 120, next)));
    };
    const up = () => {
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  };

  return (
    <Card className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Filter bar */}
      <div className="shrink-0 flex items-center gap-3 px-4 py-3 border-b">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search reference or customerâ€¦"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as SOStatus | "")}
        >
          <option value="">All statuses</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="ml-auto">
              <Plus className="mr-2 h-4 w-4" /> New SO
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>New sales order</DialogTitle>
            </DialogHeader>
            <form onSubmit={submit} className="grid gap-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="ref">Reference</Label>
                  <Input
                    id="ref"
                    required
                    value={form.reference}
                    onChange={(e) => setForm({ ...form, reference: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="customer">Customer</Label>
                  <Input
                    id="customer"
                    required
                    value={form.customer}
                    onChange={(e) => setForm({ ...form, customer: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="reqdate">Requested date</Label>
                  <Input
                    id="reqdate"
                    type="date"
                    value={form.requested_date}
                    onChange={(e) => setForm({ ...form, requested_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Lines</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addLine}>
                    <Plus className="mr-1 h-3 w-3" /> Add line
                  </Button>
                </div>
                {form.lines.map((line, i) => (
                  <div key={i} className="grid grid-cols-[1fr,120px,40px] gap-2">
                    <select
                      className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                      value={line.product_id}
                      onChange={(e) => {
                        const lines = [...form.lines];
                        lines[i] = { ...line, product_id: Number(e.target.value) };
                        setForm({ ...form, lines });
                      }}
                    >
                      <option value={0}>â€” select product â€”</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>{p.sku} â€” {p.name}</option>
                      ))}
                    </select>
                    <Input
                      type="number"
                      min={1}
                      value={line.qty_ordered}
                      onChange={(e) => {
                        const lines = [...form.lines];
                        lines[i] = { ...line, qty_ordered: Number(e.target.value) };
                        setForm({ ...form, lines });
                      }}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeLine(i)}
                      disabled={form.lines.length === 1}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createSO.isPending}>
                  {createSO.isPending ? "Saving..." : "Create SO"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Split area */}
      <div ref={containerRef} className="flex-1 flex flex-col min-h-0">
        {/* Upper panel */}
        <div style={{ height: splitPx }} className="overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Requested</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Lines</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">Loadingâ€¦</TableCell>
                </TableRow>
              ) : filteredSos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">No sales orders found</TableCell>
                </TableRow>
              ) : (
                filteredSos.map((so) => (
                  <TableRow
                    key={so.id}
                    className={`cursor-pointer ${selectedSoId === so.id ? "bg-muted" : "hover:bg-muted/50"}`}
                    onClick={() => setSelectedSoId(so.id === selectedSoId ? null : so.id)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Link to={`${so.id}`} className="font-mono text-primary hover:underline">
                        {so.reference}
                      </Link>
                    </TableCell>
                    <TableCell>{so.customer}</TableCell>
                    <TableCell className="text-muted-foreground">{so.requested_date ?? "â€”"}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[so.status]}>{so.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">{so.lines.length}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Drag handle */}
        <div
          onMouseDown={onDragStart}
          className="shrink-0 h-1.5 cursor-row-resize bg-border hover:bg-primary transition-colors"
        />

        {/* Lower panel */}
        <div className="flex-1 overflow-auto">
          {selectedSo === null ? (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              Select an order above to view its lines
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Ordered</TableHead>
                  <TableHead className="text-right">Shipped</TableHead>
                  <TableHead className="text-right">Remaining</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selectedSo.lines.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">No lines on this order</TableCell>
                  </TableRow>
                ) : (
                  selectedSo.lines.map((ln) => {
                    const p = productById(ln.product_id);
                    const remaining = ln.qty_ordered - ln.qty_shipped;
                    return (
                      <TableRow key={ln.id}>
                        <TableCell>
                          <span className="font-mono">{p?.sku ?? "?"}</span> â€” {p?.name}
                        </TableCell>
                        <TableCell className="text-right">{ln.qty_ordered}</TableCell>
                        <TableCell className="text-right">{ln.qty_shipped}</TableCell>
                        <TableCell className="text-right">
                          {remaining === 0 ? (
                            <Badge variant="success">
                              <CheckCircle2 className="mr-1 h-3 w-3" /> Complete
                            </Badge>
                          ) : (
                            remaining
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          )}
        </div>
      </div>
    </Card>
  );
}
