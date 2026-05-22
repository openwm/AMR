import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";

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
import { useProducts } from "@/features/inventory/api";

import { useCreatePurchaseOrder, usePurchaseOrders } from "./api";
import type { POStatus } from "./types";

const STATUS_VARIANT: Record<POStatus, "default" | "success" | "warning" | "secondary"> = {
  DRAFT: "secondary",
  OPEN: "default",
  PARTIAL: "warning",
  RECEIVED: "success",
  CLOSED: "secondary",
};

export default function PurchaseOrdersPage() {
  const { data: pos = [], isLoading } = usePurchaseOrders();
  const { data: products = [] } = useProducts();
  const createPO = useCreatePurchaseOrder();
  const [dialogOpen, setDialogOpen] = useState(false);

  const [form, setForm] = useState({
    reference: "",
    supplier: "",
    expected_date: "",
    lines: [{ product_id: 0, qty_ordered: 1 }],
  });

  const addLine = () =>
    setForm({ ...form, lines: [...form.lines, { product_id: 0, qty_ordered: 1 }] });
  const removeLine = (i: number) =>
    setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createPO.mutateAsync({
      reference: form.reference,
      supplier: form.supplier,
      expected_date: form.expected_date || null,
      lines: form.lines.filter((l) => l.product_id > 0 && l.qty_ordered > 0),
    });
    setDialogOpen(false);
    setForm({
      reference: "",
      supplier: "",
      expected_date: "",
      lines: [{ product_id: 0, qty_ordered: 1 }],
    });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Purchase orders</CardTitle>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" /> New PO
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>New purchase order</DialogTitle>
            </DialogHeader>
            <form onSubmit={submit} className="grid gap-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="reference">Reference</Label>
                  <Input
                    id="reference"
                    required
                    value={form.reference}
                    onChange={(e) => setForm({ ...form, reference: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="supplier">Supplier</Label>
                  <Input
                    id="supplier"
                    required
                    value={form.supplier}
                    onChange={(e) => setForm({ ...form, supplier: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="expected_date">Expected date</Label>
                  <Input
                    id="expected_date"
                    type="date"
                    value={form.expected_date}
                    onChange={(e) =>
                      setForm({ ...form, expected_date: e.target.value })
                    }
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
                      <option value={0}>— select product —</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.sku} — {p.name}
                        </option>
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
                <Button type="submit" disabled={createPO.isPending}>
                  {createPO.isPending ? "Saving..." : "Create PO"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Reference</TableHead>
              <TableHead>Supplier</TableHead>
              <TableHead>Expected</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Lines</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : pos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No purchase orders yet
                </TableCell>
              </TableRow>
            ) : (
              pos.map((po) => (
                <TableRow key={po.id}>
                  <TableCell>
                    <Link
                      to={`${po.id}`}
                      className="font-mono text-primary hover:underline"
                    >
                      {po.reference}
                    </Link>
                  </TableCell>
                  <TableCell>{po.supplier}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {po.expected_date ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[po.status]}>{po.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">{po.lines.length}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
