import { useState } from "react";
import { Plus } from "lucide-react";

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

import { useCreateLocation, useLocations } from "./api";

const LOCATION_TYPES = ["STORAGE", "RECEIVING", "SHIPPING", "QUARANTINE"] as const;

export default function LocationsPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: locations = [], isLoading } = useLocations();
  const createLocation = useCreateLocation();
  const [form, setForm] = useState({
    code: "",
    zone: "A",
    aisle: "",
    rack: "",
    bin: "",
    type: "STORAGE",
    is_pickable: true,
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createLocation.mutateAsync(form as any);
    setDialogOpen(false);
    setForm({ code: "", zone: "A", aisle: "", rack: "", bin: "", type: "STORAGE", is_pickable: true });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Locations</CardTitle>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" /> New location
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New location</DialogTitle>
            </DialogHeader>
            <form onSubmit={submit} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="code">Code</Label>
                <Input
                  id="code"
                  required
                  placeholder="A-01-02-03"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="zone">Zone</Label>
                  <Input
                    id="zone"
                    required
                    value={form.zone}
                    onChange={(e) => setForm({ ...form, zone: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="type">Type</Label>
                  <select
                    id="type"
                    className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    value={form.type}
                    onChange={(e) => setForm({ ...form, type: e.target.value })}
                  >
                    {LOCATION_TYPES.map((t) => (
                      <option key={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createLocation.isPending}>
                  {createLocation.isPending ? "Saving..." : "Create"}
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
              <TableHead>Code</TableHead>
              <TableHead>Zone</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Pickable</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : locations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No locations defined
                </TableCell>
              </TableRow>
            ) : (
              locations.map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="font-mono">{l.code}</TableCell>
                  <TableCell>{l.zone}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{l.type}</Badge>
                  </TableCell>
                  <TableCell>
                    {l.is_pickable ? (
                      <Badge variant="success">Yes</Badge>
                    ) : (
                      <Badge variant="outline">No</Badge>
                    )}
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
