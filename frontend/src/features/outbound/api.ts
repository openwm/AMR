import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  SalesOrder,
  Shipment,
  SOLineInput,
  ShipmentLineInput,
} from "./types";

const KEYS = {
  sos: ["outbound", "sales-orders"] as const,
  so: (id: number) => ["outbound", "sales-order", id] as const,
  shipments: ["outbound", "shipments"] as const,
};

export function useSalesOrders() {
  return useQuery({
    queryKey: KEYS.sos,
    queryFn: async () => {
      const { data } = await api.get<SalesOrder[]>("/api/outbound/sales-orders");
      return data;
    },
  });
}

export function useSalesOrder(id: number | undefined) {
  return useQuery({
    queryKey: id ? KEYS.so(id) : ["outbound", "sales-order", "none"],
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<SalesOrder>(`/api/outbound/sales-orders/${id}`);
      return data;
    },
  });
}

export function useCreateSalesOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      reference: string;
      customer: string;
      requested_date?: string | null;
      notes?: string | null;
      lines: SOLineInput[];
    }) => {
      const { data } = await api.post<SalesOrder>(
        "/api/outbound/sales-orders",
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.sos }),
  });
}

export function useShipments(soId?: number) {
  return useQuery({
    queryKey: [...KEYS.shipments, soId],
    queryFn: async () => {
      const { data } = await api.get<Shipment[]>("/api/outbound/shipments", {
        params: soId ? { so_id: soId } : undefined,
      });
      return data;
    },
  });
}

export function useCreateShipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      reference: string;
      so_id: number;
      carrier?: string | null;
      tracking_number?: string | null;
      lines: ShipmentLineInput[];
    }) => {
      const { data } = await api.post<Shipment>("/api/outbound/shipments", payload);
      return data;
    },
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: KEYS.shipments });
      qc.invalidateQueries({ queryKey: KEYS.so(vars.so_id) });
    },
  });
}

export function useShipShipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (shipmentId: number) => {
      const { data } = await api.post<Shipment>(
        `/api/outbound/shipments/${shipmentId}/ship`,
      );
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: KEYS.shipments });
      qc.invalidateQueries({ queryKey: KEYS.sos });
      qc.invalidateQueries({ queryKey: KEYS.so(data.so_id) });
      qc.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
}
