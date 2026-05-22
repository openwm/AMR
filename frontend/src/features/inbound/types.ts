export type POStatus = "DRAFT" | "OPEN" | "PARTIAL" | "RECEIVED" | "CLOSED";
export type ReceiptStatus = "DRAFT" | "COMPLETED";

export interface POLine {
  id: number;
  product_id: number;
  qty_ordered: number;
  qty_received: number;
}

export interface PurchaseOrder {
  id: number;
  reference: string;
  supplier: string;
  status: POStatus;
  expected_date: string | null;
  notes: string | null;
  created_at: string;
  lines: POLine[];
}

export interface ReceiptLine {
  id: number;
  po_line_id: number | null;
  product_id: number;
  location_id: number;
  quantity: number;
  lot_number: string;
  expiry_date: string | null;
}

export interface Receipt {
  id: number;
  reference: string;
  po_id: number | null;
  status: ReceiptStatus;
  notes: string | null;
  created_at: string;
  completed_at: string | null;
  lines: ReceiptLine[];
}

export interface POLineInput {
  product_id: number;
  qty_ordered: number;
}

export interface ReceiptLineInput {
  po_line_id?: number | null;
  product_id: number;
  location_id: number;
  quantity: number;
  lot_number?: string;
  expiry_date?: string | null;
}
