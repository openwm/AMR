import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  ActivityEvent,
  Kpis,
  LowStockProduct,
  StockByZone,
  ThroughputDay,
  TopMover,
} from "./types";

export function useKpis() {
  return useQuery({
    queryKey: ["reporting", "kpis"],
    queryFn: async () => {
      const { data } = await api.get<Kpis>("/api/reporting/kpis");
      return data;
    },
    refetchInterval: 15_000,
  });
}

export function useStockByZone() {
  return useQuery({
    queryKey: ["reporting", "stock-by-zone"],
    queryFn: async () => {
      const { data } = await api.get<StockByZone[]>("/api/reporting/stock-by-zone");
      return data;
    },
  });
}

export function useThroughput(days = 14) {
  return useQuery({
    queryKey: ["reporting", "throughput", days],
    queryFn: async () => {
      const { data } = await api.get<ThroughputDay[]>("/api/reporting/throughput", {
        params: { days },
      });
      return data;
    },
  });
}

export function useTopMovers() {
  return useQuery({
    queryKey: ["reporting", "top-movers"],
    queryFn: async () => {
      const { data } = await api.get<TopMover[]>("/api/reporting/top-movers");
      return data;
    },
  });
}

export function useLowStock() {
  return useQuery({
    queryKey: ["reporting", "low-stock"],
    queryFn: async () => {
      const { data } = await api.get<LowStockProduct[]>("/api/reporting/low-stock");
      return data;
    },
  });
}

export function useRecentActivity() {
  return useQuery({
    queryKey: ["reporting", "recent-activity"],
    queryFn: async () => {
      const { data } = await api.get<ActivityEvent[]>("/api/reporting/recent-activity");
      return data;
    },
  });
}
