import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Plus } from "lucide-react";

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
import { useLocations, useProducts } from "@/features/inventory/api";

import {
  useCompleteReceipt,
  useCreateReceipt,
  usePurchaseOrder,
  useReceipts,
} from "./api";

export default function PurchaseOrderDetailPage() {
  const { poId } = useParams<{ poId: string }>();
  const id = poId ? Number(poId) : undefined;
  const { data: po } = usePurchaseOrder(id);
  const { data: receipts = [] } = useReceipts(id);
  const { data: products = [] } = useProducts();
  const { data: locations = [] } = useLocations({ type: "STORAGE" });
  const createReceipt = useCreateReceipt();
  const completeReceipt = useCompleteReceipt();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [receiptForm, setReceiptForm] = useState<{
    reference: string;
    lines: {
      po_line_id: number;
      product_id: number;
      location_id: number;
      quantity: number;
      lot_number: string;
    }[];
  }>({ reference: "", lines: [] });

  if (!po) return <div className="text-muted-foreground">Loading…</div>;

  const productById = (pid: number) => products.find((p) => p.id === pid);

  const startReceipt = () => {
    setReceiptForm({
      reference: `R-${po.reference}-${(receipts.length + 1).toString().padStart(2, "0")}`,
      lines: po.lines
        .filter((ln) => ln.qty_received < ln.qty_ordered)
        .map((ln) => ({
          po_line_id: ln.id,
          product_id: ln.product_id,
          location_id: locations[0]?.id ?? 0,
          quantity: ln.qty_ordered - ln.qty_received,
          lot_number: "",
        })),
    });
    setDialogOpen(true);
  };

  const submitReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    const created = await createReceipt.mutateAsync({
      reference: receiptForm.reference,
      po_id: po.id,
      lines: receiptForm.lines.filter((l) => l.quantity > 0),
    });
    await completeReceipt.mutateAsync(created.id);
    setDialogOpen(false);
  };

  return (
    <div className="space-y-4">
      <Link
        to=".."
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to purchase orders
      </Link>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle className="font-mono">{po.reference}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Supplier: {po.supplier} · Expected:{" "}
              {po.expected_date ?? "—"} · <Badge variant="outline">{po.status}</Badge>
            </p>
          </div>
          {po.status !== "RECEIVED" && po.status !== "CLOSED" && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm" onClick={startReceipt}>
                  <Plus className="mr-2 h-4 w-4" /> Receive
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Receive against {po.reference}</DialogTitle>
                </DialogHeader>
                <form onSubmit={submitReceipt} className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="receiptRef">Receipt reference</Label>
                    <Input
                      id="receiptRef"
                      required
                      value={receiptForm.reference}
                      onChange={(e) =>
                        setReceiptForm({ ...receiptForm, reference: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Lines</Label>
                    {receiptForm.lines.map((line, i) => (
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
                            const lines = [...receiptForm.lines];
                            lines[i] = { ...line, location_id: Number(e.target.value) };
                            setReceiptForm({ ...receiptForm, lines });
                          }}
                        >
                          {locations.map((l) => (
                            <option key={l.id} value={l.id}>
                              {l.code}
                            </option>
                          ))}
                        </select>
                        <Input
                          type="number"
                          min={0}
                          value={line.quantity}
                          onChange={(e) => {
                            const lines = [...receiptForm.lines];
                            lines[i] = { ...line, quantity: Number(e.target.value) };
                            setReceiptForm({ ...receiptForm, lines });
                          }}
                        />
                        <Input
                          placeholder="lot (optional)"
                          value={line.lot_number}
                          onChange={(e) => {
                            const lines = [...receiptForm.lines];
                            lines[i] = { ...line, lot_number: e.target.value };
                            setReceiptForm({ ...receiptForm, lines });
                          }}
                        />
                      </div>
                    ))}
                  </div>
                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={createReceipt.isPending || completeReceipt.isPending}
                    >
                      {createReceipt.isPending || completeReceipt.isPending
                        ? "Receiving…"
                        : "Receive & put away"}
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
                <TableHead className="text-right">Received</TableHead>
                <TableHead className="text-right">Remaining</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {po.lines.map((ln) => {
                const p = productById(ln.product_id);
                const remaining = ln.qty_ordered - ln.qty_received;
                return (
                  <TableRow key={ln.id}>
                    <TableCell>
                      <span className="font-mono">{p?.sku ?? "?"}</span> — {p?.name}
                    </TableCell>
                    <TableCell className="text-right">{ln.qty_ordered}</TableCell>
                    <TableCell className="text-right">{ln.qty_received}</TableCell>
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

      {receipts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Receipts</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reference</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Lines</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {receipts.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono">{r.reference}</TableCell>
                    <TableCell>
                      <Badge variant={r.status === "COMPLETED" ? "success" : "secondary"}>
                        {r.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(r.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">{r.lines.length}</TableCell>
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
