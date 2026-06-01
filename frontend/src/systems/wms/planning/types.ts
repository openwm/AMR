export interface PlanningConfig {
  id: number;
  max_active_orders: number;
  max_picking_orders: number;
}

export interface PlanningResult {
  activated: number;
  skipped: number;
  slots_remaining: number;
}

export interface ReleaseResult {
  released: number;
  skipped: number;
}

export interface OrderAvailability {
  so_id: number;
  reference: string;
  customer: string;
  created_at: string;
  can_fulfill: boolean;
  missing_product_ids: number[];
}
