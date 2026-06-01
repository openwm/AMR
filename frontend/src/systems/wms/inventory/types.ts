export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string | null;
  uom: string;
  barcode: string | null;
  category: string | null;
  min_stock: number;
  unit_cost: string;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: number;
  code: string;
  zone: string;
  aisle: string | null;
  rack: string | null;
  bin: string | null;
  type: "STORAGE" | "RECEIVING" | "SHIPPING" | "QUARANTINE";
  is_pickable: boolean;
}

export interface StockItem {
  id: number;
  product_id: number;
  location_id: number;
  quantity: number;
  status: "AVAILABLE" | "ALLOCATED";
  lot_number: string;
  expiry_date: string | null;
  updated_at: string;
  product_sku: string | null;
  product_name: string | null;
  location_code: string | null;
}

export interface StockMovement {
  id: number;
  product_id: number;
  location_id: number;
  quantity: number;
  movement_type:
    | "RECEIPT"
    | "PUTAWAY"
    | "PICK"
    | "SHIP"
    | "ADJUSTMENT"
    | "TRANSFER";
  reference_type: string | null;
  reference_id: number | null;
  lot_number: string;
  note: string | null;
  created_at: string;
  product_sku: string | null;
  product_name: string | null;
  location_code: string | null;
}
