import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { Location, Product, StockItem, StockMovement } from "./types";

const KEYS = {
  products: ["inventory", "products"] as const,
  product: (id: number) => ["inventory", "product", id] as const,
  locations: ["inventory", "locations"] as const,
  stock: ["inventory", "stock"] as const,
  movements: ["inventory", "movements"] as const,
};

export function useProducts(params?: { search?: string; category?: string }) {
  return useQuery({
    queryKey: [...KEYS.products, params],
    queryFn: async () => {
      const { data } = await api.get<Product[]>("/api/inventory/products", { params });
      return data;
    },
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Product>) => {
      const { data } = await api.post<Product>("/api/inventory/products", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.products }),
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/inventory/products/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.products }),
  });
}

export function useLocations(params?: { zone?: string; type?: string }) {
  return useQuery({
    queryKey: [...KEYS.locations, params],
    queryFn: async () => {
      const { data } = await api.get<Location[]>("/api/inventory/locations", { params });
      return data;
    },
  });
}

export function useCreateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Location>) => {
      const { data } = await api.post<Location>("/api/inventory/locations", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.locations }),
  });
}

export function useStock(params?: { product_id?: number; location_id?: number }) {
  return useQuery({
    queryKey: [...KEYS.stock, params],
    queryFn: async () => {
      const { data } = await api.get<StockItem[]>("/api/inventory/stock", { params });
      return data;
    },
  });
}

export function useMovements(params?: {
  product_id?: number;
  location_id?: number;
  movement_type?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...KEYS.movements, params],
    queryFn: async () => {
      const { data } = await api.get<StockMovement[]>("/api/inventory/movements", {
        params,
      });
      return data;
    },
  });
}
