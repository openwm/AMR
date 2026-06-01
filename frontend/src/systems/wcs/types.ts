export type TaskStatus = "queued" | "at_dock" | "picking" | "completed" | "exception";

export interface PickTask {
  id: string;
  order_id: number;
  order_line_id: number;
  product_id: number;
  product_sku: string;
  quantity: number;
  deadline: string;
  priority_score: number;
  station_id: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface StationQueue {
  station_id: string;
  tasks: PickTask[];
  queue_depth: number;
  amr_count: number;
  picks_per_hour: number;
}

export interface StationSummary {
  station_id: string;
  queue_depth: number;
  amr_count: number;
  picks_per_hour: number;
}

export interface CreateTaskRequest {
  order_id: number;
  order_line_id: number;
  product_id: number;
  product_sku: string;
  quantity: number;
  deadline: string;
}
