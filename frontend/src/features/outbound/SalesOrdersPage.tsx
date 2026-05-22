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

import { useCreateSalesOrder, useSalesOrders } from "./api";
import type { SOStatus } from "./types";

const STATUS_VARIANT: Record<SOStatus, "default" | "success" | "warning" | "secondary" | "destructive"> = {
  DRAFT: "secondary",
  OPEN: "default",
  PARTIAL: "warning",
  SHIPPED: "success",
  CLOSED: "secondary",
  CANCELLED: "destructive",
};

export default function SalesOrdersPage() {
  const { data: sos = [], isLoading } = useSalesOrders();
  const { data: products = [] } = useProducts();
  const createSO = useCreateSalesOrder();
  const [dialogOpen, setDialogOpen] = useState(false);

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
    setForm({
      reference: "",
      customer: "",
      requested_date: "",
      lines: [{ product_id: 0, qty_ordered: 1 }],
    });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Sales orders</CardTitle>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
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
                    onChange={(e) =>
                      setForm({ ...form, requested_date: e.target.value })
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
                <Button type="submit" disabled={createSO.isPending}>
                  {createSO.isPending ? "Saving..." : "Create SO"}
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
              <TableHead>Customer</TableHead>
              <TableHead>Requested</TableHead>
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
            ) : sos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No sales orders yet
                </TableCell>
              </TableRow>
            ) : (
              sos.map((so) => (
                <TableRow key={so.id}>
                  <TableCell>
                    <Link to={`${so.id}`} className="font-mono text-primary hover:underline">
                      {so.reference}
                    </Link>
                  </TableCell>
                  <TableCell>{so.customer}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {so.requested_date ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[so.status]}>{so.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">{so.lines.length}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
