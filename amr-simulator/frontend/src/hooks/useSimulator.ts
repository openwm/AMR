import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { AMR, FleetUpdateMessage, WarehouseLayout } from "../types";

const SIM_URL = (import.meta.env.VITE_SIM_URL as string | undefined) ?? "http://localhost:8001";
const SIM_WS  = (import.meta.env.VITE_SIM_WS  as string | undefined) ?? "ws://localhost:8001/ws";

const api = axios.create({ baseURL: SIM_URL });

export function useLayout() {
  return useQuery<WarehouseLayout>({
    queryKey: ["layout"],
    queryFn: async () => (await api.get<WarehouseLayout>("/layout")).data,
    staleTime: Infinity,
    retry: 5,
    retryDelay: 1000,
  });
}

export function useFleet(): AMR[] {
  const [amrs, setAmrs] = useState<AMR[]>([]);
  const activeRef = useRef(true);

  useEffect(() => {
    activeRef.current = true;
    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(SIM_WS);

      ws.onmessage = (evt: MessageEvent) => {
        if (!activeRef.current) return;
        try {
          const msg = JSON.parse(evt.data as string) as FleetUpdateMessage;
          if (msg.type === "fleet_update") setAmrs(msg.amrs);
        } catch (_) {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (activeRef.current) reconnectTimer = setTimeout(connect, 2000);
      };
    }

    connect();

    return () => {
      activeRef.current = false;
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  return amrs;
}

export function useRegisterAMR() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; x: number; y: number; speed?: number }) =>
      (await api.post<AMR>("/amrs", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["layout"] }),
  });
}

export function useDispatchAMR() {
  return useMutation({
    mutationFn: async ({ amrId, locationCode }: { amrId: string; locationCode: string }) =>
      (await api.post<AMR>(`/amrs/${amrId}/dispatch`, { location_code: locationCode })).data,
  });
}
