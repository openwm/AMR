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

import { useStock } from "./api";

export default function StockPage() {
  const { data: stock = [], isLoading } = useStock();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stock on hand</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Lot</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : stock.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No stock yet — receive a purchase order to populate
                </TableCell>
              </TableRow>
            ) : (
              stock.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-mono">{s.product_sku}</TableCell>
                  <TableCell>{s.product_name}</TableCell>
                  <TableCell className="font-mono">{s.location_code}</TableCell>
                  <TableCell>{s.lot_number || "—"}</TableCell>
                  <TableCell>
                    <Badge variant={s.status === "ALLOCATED" ? "warning" : "success"}>
                      {s.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">{s.quantity}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
