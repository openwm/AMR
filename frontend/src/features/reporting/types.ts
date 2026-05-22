export interface Kpis {
  product_count: number;
  location_count: number;
  stock_value: number;
  units_on_hand: number;
  open_purchase_orders: number;
  open_sales_orders: number;
  low_stock_products: number;
}

export interface StockByZone {
  zone: string;
  units: number;
}

export interface ThroughputDay {
  day: string;
  inbound: number;
  outbound: number;
}

export interface TopMover {
  sku: string;
  name: string;
  units_moved: number;
}

export interface LowStockProduct {
  sku: string;
  name: string;
  min_stock: number;
  on_hand: number;
}

export interface ActivityEvent {
  kind: "receipt" | "shipment";
  reference: string;
  status: string;
  at: string;
}
