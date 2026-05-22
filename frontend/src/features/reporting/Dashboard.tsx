import {
  Activity,
  AlertTriangle,
  Boxes,
  DollarSign,
  MapPin,
  PackageOpen,
  Truck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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

import {
  useKpis,
  useLowStock,
  useRecentActivity,
  useStockByZone,
  useThroughput,
  useTopMovers,
} from "./api";

function Kpi({
  label,
  value,
  icon: Icon,
  hint,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  hint?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const { data: kpis } = useKpis();
  const { data: byZone = [] } = useStockByZone();
  const { data: throughput = [] } = useThroughput(14);
  const { data: topMovers = [] } = useTopMovers();
  const { data: lowStock = [] } = useLowStock();
  const { data: activity = [] } = useRecentActivity();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Warehouse dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Live overview of inventory, inbound, and outbound activity.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi
          label="Stock value"
          value={
            kpis
              ? `$${kpis.stock_value.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}`
              : "—"
          }
          icon={DollarSign}
        />
        <Kpi
          label="Units on hand"
          value={kpis?.units_on_hand.toLocaleString() ?? "—"}
          icon={Boxes}
          hint={`${kpis?.product_count ?? 0} SKUs · ${kpis?.location_count ?? 0} locations`}
        />
        <Kpi
          label="Open POs"
          value={kpis?.open_purchase_orders ?? "—"}
          icon={PackageOpen}
        />
        <Kpi
          label="Open SOs"
          value={kpis?.open_sales_orders ?? "—"}
          icon={Truck}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Throughput — last 14 days</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={throughput}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="inbound"
                  stroke="hsl(142, 71%, 45%)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="outbound"
                  stroke="hsl(0, 84%, 60%)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Stock by zone</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byZone}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="zone" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="units" fill="hsl(222, 47%, 40%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top movers (30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Units moved</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topMovers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center text-muted-foreground">
                      No movement yet
                    </TableCell>
                  </TableRow>
                ) : (
                  topMovers.map((m) => (
                    <TableRow key={m.sku}>
                      <TableCell className="font-mono">{m.sku}</TableCell>
                      <TableCell>{m.name}</TableCell>
                      <TableCell className="text-right">{m.units_moved}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Low stock alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">On hand</TableHead>
                  <TableHead className="text-right">Min</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lowStock.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center text-muted-foreground">
                      All stock levels healthy
                    </TableCell>
                  </TableRow>
                ) : (
                  lowStock.map((p) => (
                    <TableRow key={p.sku}>
                      <TableCell className="font-mono">{p.sku}</TableCell>
                      <TableCell className="text-right">{p.on_hand}</TableCell>
                      <TableCell className="text-right">{p.min_stock}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent activity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {activity.length === 0 ? (
                <li className="text-muted-foreground">No activity yet</li>
              ) : (
                activity.map((e, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-2 border-b pb-2 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant={e.kind === "receipt" ? "success" : "secondary"}>
                        {e.kind}
                      </Badge>
                      <span className="font-mono text-xs">{e.reference}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(e.at).toLocaleString()}
                    </span>
                  </li>
                ))
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
