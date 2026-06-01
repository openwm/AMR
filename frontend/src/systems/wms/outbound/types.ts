export type SOStatus =
  | "DRAFT"
  | "NEW"
  | "ACTIVE"
  | "PICKING"
  | "PARTIAL"
  | "SHIPPED"
  | "CLOSED"
  | "CANCELLED";

export type ShipmentStatus = "DRAFT" | "SHIPPED";

export interface SOLine {
  id: number;
  product_id: number;
  qty_ordered: number;
  qty_shipped: number;
  qty_picked: number;
}

export interface SalesOrder {
  id: number;
  reference: string;
  customer: string;
  status: SOStatus;
  requested_date: string | null;
  notes: string | null;
  created_at: string;
  lines: SOLine[];
}

export interface ShipmentLine {
  id: number;
  so_line_id: number | null;
  product_id: number;
  location_id: number;
  quantity: number;
  lot_number: string;
}

export interface Shipment {
  id: number;
  reference: string;
  so_id: number;
  status: ShipmentStatus;
  carrier: string | null;
  tracking_number: string | null;
  notes: string | null;
  created_at: string;
  shipped_at: string | null;
  lines: ShipmentLine[];
}

export interface SOLineInput {
  product_id: number;
  qty_ordered: number;
}

export interface ShipmentLineInput {
  so_line_id?: number | null;
  product_id: number;
  location_id: number;
  quantity: number;
  lot_number?: string;
}
