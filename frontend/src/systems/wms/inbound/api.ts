import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  POLineInput,
  PurchaseOrder,
  Receipt,
  ReceiptLineInput,
} from "./types";

const KEYS = {
  pos: ["inbound", "purchase-orders"] as const,
  po: (id: number) => ["inbound", "purchase-order", id] as const,
  receipts: ["inbound", "receipts"] as const,
};

export function usePurchaseOrders() {
  return useQuery({
    queryKey: KEYS.pos,
    queryFn: async () => {
      const { data } = await api.get<PurchaseOrder[]>("/api/wms/inbound/purchase-orders");
      return data;
    },
  });
}

export function usePurchaseOrder(id: number | undefined) {
  return useQuery({
    queryKey: id ? KEYS.po(id) : ["inbound", "purchase-order", "none"],
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<PurchaseOrder>(
        `/api/wms/inbound/purchase-orders/${id}`,
      );
      return data;
    },
  });
}

export function useCreatePurchaseOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      reference: string;
      supplier: string;
      expected_date?: string | null;
      notes?: string | null;
      lines: POLineInput[];
    }) => {
      const { data } = await api.post<PurchaseOrder>(
        "/api/wms/inbound/purchase-orders",
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.pos }),
  });
}

export function useReceipts(poId?: number) {
  return useQuery({
    queryKey: [...KEYS.receipts, poId],
    queryFn: async () => {
      const { data } = await api.get<Receipt[]>("/api/wms/inbound/receipts", {
        params: poId ? { po_id: poId } : undefined,
      });
      return data;
    },
  });
}

export function useCreateReceipt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      reference: string;
      po_id?: number | null;
      notes?: string | null;
      lines: ReceiptLineInput[];
    }) => {
      const { data } = await api.post<Receipt>("/api/wms/inbound/receipts", payload);
      return data;
    },
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: KEYS.receipts });
      if (vars.po_id) qc.invalidateQueries({ queryKey: KEYS.po(vars.po_id) });
    },
  });
}

export function useCompleteReceipt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (receiptId: number) => {
      const { data } = await api.post<Receipt>(
        `/api/wms/inbound/receipts/${receiptId}/complete`,
      );
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: KEYS.receipts });
      qc.invalidateQueries({ queryKey: KEYS.pos });
      if (data.po_id) qc.invalidateQueries({ queryKey: KEYS.po(data.po_id) });
      qc.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
}
