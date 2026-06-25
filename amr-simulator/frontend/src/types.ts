export type AMRStatus = "idle" | "traveling" | "at_location";

export interface AMR {
  id: string;
  name: string;
  x: number;
  y: number;
  target_x: number | null;
  target_y: number | null;
  target_location: string | null;
  status: AMRStatus;
  speed: number;
}

export interface LocationCoord {
  x: number;
  y: number;
}

export interface ZoneLabel {
  zone: string;
  x_start: number;
  x_end: number;
}

export interface WarehouseLayout {
  grid_width: number;
  grid_height: number;
  zone_labels: ZoneLabel[];
  locations: Record<string, LocationCoord>;
  stations: Record<string, LocationCoord>;
  dock_in: LocationCoord;
  dock_out: LocationCoord;
}

export interface FleetUpdateMessage {
  type: "fleet_update";
  amrs: AMR[];
}
