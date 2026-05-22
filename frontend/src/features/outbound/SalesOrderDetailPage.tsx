import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Truck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { useProducts, useStock } from "@/features/inventory/api";

import {
  useCreateShipment,
  useSalesOrder,
  useShipShipment,
  useShipments,
} from "./api";

export default function SalesOrderDetailPage() {
  const { soId } = useParams<{ soId: string }>();
  const id = soId ? Number(soId) : undefined;
  const { data: so } = useSalesOrder(id);
  const { data: shipments = [] } = useShipments(id);
  const { data: products = [] } = useProducts();
  const { data: stock = [] } = useStock();
  const createShipment = useCreateShipment();
  const shipShipment = useShipShipment();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<{
    reference: string;
    carrier: string;
    tracking_number: string;
    lines: {
      so_line_id: number;
      product_id: number;
      location_id: number;
      quantity: number;
      lot_number: string;
    }[];
  }>({ reference: "", carrier: "", tracking_number: "", lines: [] });

  const stockByProduct = useMemo(() => {
    const map = new Map<number, typeof stock>();
    for (const s of stock) {
      const arr = map.get(s.product_id) ?? [];
      arr.push(s);
      map.set(s.product_id, arr);
    }
    return map;
  }, [stock]);

  if (!so) return <div className="text-muted-foreground">Loading…</div>;

  const productById = (pid: number) => products.find((p) => p.id === pid);

  const startShipment = () => {
    const open_lines = so.lines.filter((ln) => ln.qty_shipped < ln.qty_ordered);
    setForm({
      reference: `S-${so.reference}-${(shipments.length + 1).toString().padStart(2, "0")}`,
      carrier: "",
      tracking_number: "",
      lines: open_lines.map((ln) => {
        const stocks = stockByProduct.get(ln.product_id) ?? [];
        const first = stocks[0];
        return {
          so_line_id: ln.id,
          product_id: ln.product_id,
          location_id: first?.location_id ?? 0,
          quantity: Math.min(
            ln.qty_ordered - ln.qty_shipped,
            first?.quantity ?? 0,
          ),
          lot_number: first?.lot_number ?? "",
        };
      }),
    });
    setDialogOpen(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const created = await createShipment.mutateAsync({
      reference: form.reference,
      so_id: so.id,
      carrier: form.carrier || null,
      tracking_number: form.tracking_number || null,
      lines: form.lines.filter((l) => l.quantity > 0 && l.location_id > 0),
    });
    await shipShipment.mutateAsync(created.id);
    setDialogOpen(false);
  };

  return (
    <div className="space-y-4">
      <Link
        to=".."
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to sales orders
      </Link>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle className="font-mono">{so.reference}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Customer: {so.customer} · Requested: {so.requested_date ?? "—"} ·{" "}
              <Badge variant="outline">{so.status}</Badge>
            </p>
          </div>
          {so.status !== "SHIPPED" && so.status !== "CLOSED" && so.status !== "CANCELLED" && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm" onClick={startShipment}>
                  <Truck className="mr-2 h-4 w-4" /> Pick &amp; ship
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl">
                <DialogHeader>
                  <DialogTitle>Pick &amp; ship for {so.reference}</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="grid gap-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="ref">Shipment ref</Label>
                      <Input
                        id="ref"
                        required
                        value={form.reference}
                        onChange={(e) =>
                          setForm({ ...form, reference: e.target.value })
                        }
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="carrier">Carrier</Label>
                      <Input
                        id="carrier"
                        value={form.carrier}
                        onChange={(e) => setForm({ ...form, carrier: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="tracking">Tracking #</Label>
                      <Input
                        id="tracking"
                        value={form.tracking_number}
                        onChange={(e) =>
                          setForm({ ...form, tracking_number: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Picks</Label>
                    {form.lines.length === 0 && (
                      <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
                        Order is fully shipped.
                      </div>
                    )}
                    {form.lines.map((line, i) => {
                      const stocks = stockByProduct.get(line.product_id) ?? [];
                      return (
                        <div
                          key={i}
                          className="grid grid-cols-[1fr,1fr,100px,120px] gap-2 text-sm"
                        >
                          <div className="flex items-center font-mono">
                            {productById(line.product_id)?.sku}
                          </div>
                          <select
                            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                            value={line.location_id}
                            onChange={(e) => {
                              const lines = [...form.lines];
                              const sid = Number(e.target.value);
                              const matched = stocks.find((s) => s.location_id === sid);
                              lines[i] = {
                                ...line,
                                location_id: sid,
                                lot_number: matched?.lot_number ?? "",
                              };
                              setForm({ ...form, lines });
                            }}
                          >
                            <option value={0}>— select location —</option>
                            {stocks.map((s) => (
                              <option key={s.id} value={s.location_id}>
                                {s.location_code} ({s.quantity} avail
                                {s.lot_number ? ` · lot ${s.lot_number}` : ""})
                              </option>
                            ))}
                          </select>
                          <Input
                            type="number"
                            min={0}
                            value={line.quantity}
                            onChange={(e) => {
                              const lines = [...form.lines];
                              lines[i] = { ...line, quantity: Number(e.target.value) };
                              setForm({ ...form, lines });
                            }}
                          />
                          <Input
                            placeholder="lot (optional)"
                            value={line.lot_number}
                            onChange={(e) => {
                              const lines = [...form.lines];
                              lines[i] = { ...line, lot_number: e.target.value };
                              setForm({ ...form, lines });
                            }}
                          />
                        </div>
                      );
                    })}
                  </div>
                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={createShipment.isPending || shipShipment.isPending}
                    >
                      {createShipment.isPending || shipShipment.isPending
                        ? "Shipping…"
                        : "Pick & ship"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </CardHeader>
        <CardContent>
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
              {so.lines.map((ln) => {
                const p = productById(ln.product_id);
                const remaining = ln.qty_ordered - ln.qty_shipped;
                return (
                  <TableRow key={ln.id}>
                    <TableCell>
                      <span className="font-mono">{p?.sku ?? "?"}</span> — {p?.name}
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
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {shipments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Shipments</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reference</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Carrier</TableHead>
                  <TableHead>Tracking</TableHead>
                  <TableHead>Shipped at</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shipments.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono">{s.reference}</TableCell>
                    <TableCell>
                      <Badge variant={s.status === "SHIPPED" ? "success" : "secondary"}>
                        {s.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{s.carrier ?? "—"}</TableCell>
                    <TableCell>{s.tracking_number ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {s.shipped_at ? new Date(s.shipped_at).toLocaleString() : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
