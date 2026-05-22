import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { useMovements } from "./api";

const TYPE_VARIANT: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  RECEIPT: "success",
  PUTAWAY: "success",
  PICK: "warning",
  SHIP: "destructive",
  ADJUSTMENT: "secondary",
  TRANSFER: "secondary",
};

export default function MovementsPage() {
  const { data: movements = [], isLoading } = useMovements({ limit: 200 });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stock movements</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>When</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Location</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead>Reference</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : movements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No movements yet
                </TableCell>
              </TableRow>
            ) : (
              movements.map((m) => (
                <TableRow key={m.id}>
                  <TableCell className="whitespace-nowrap text-muted-foreground">
                    {new Date(m.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant={TYPE_VARIANT[m.movement_type] ?? "default"}>
                      {m.movement_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono">{m.product_sku}</TableCell>
                  <TableCell className="font-mono">{m.location_code}</TableCell>
                  <TableCell
                    className={`text-right font-medium ${
                      m.quantity < 0 ? "text-red-600" : "text-emerald-700"
                    }`}
                  >
                    {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {m.reference_type ? `${m.reference_type} #${m.reference_id ?? "—"}` : "—"}
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
