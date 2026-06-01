import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { OrderAvailability, PlanningConfig, PlanningResult, ReleaseResult } from "./types";

const KEYS = {
  config: ["planning", "config"] as const,
  newOrders: ["planning", "new-orders"] as const,
};

export function usePlanningConfig() {
  return useQuery({
    queryKey: KEYS.config,
    queryFn: async () => {
      const { data } = await api.get<PlanningConfig>("/api/wms/planning/config");
      return data;
    },
  });
}

export function useUpdatePlanningConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (max_active_orders: number) => {
      const { data } = await api.patch<PlanningConfig>("/api/wms/planning/config", {
        max_active_orders,
      });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.config }),
  });
}

export function useRunPlanning() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<PlanningResult>("/api/wms/planning/run");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.newOrders });
      qc.invalidateQueries({ queryKey: ["outbound", "sales-orders"] });
      qc.invalidateQueries({ queryKey: ["inventory", "stock"] });
    },
  });
}

export function useReleaseToWcs() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ReleaseResult>("/api/wms/planning/release");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["outbound", "sales-orders"] });
      qc.invalidateQueries({ queryKey: ["wcs", "stations"] });
    },
  });
}

export function useNewOrdersAvailability() {
  return useQuery({
    queryKey: KEYS.newOrders,
    queryFn: async () => {
      const { data } = await api.get<OrderAvailability[]>("/api/wms/planning/new-orders");
      return data;
    },
  });
}
