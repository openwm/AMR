import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  CreateTaskRequest,
  PickTask,
  StationQueue,
  StationSummary,
} from "./types";

const KEYS = {
  stations: ["wcs", "stations"] as const,
  queue: (id: string) => ["wcs", "queue", id] as const,
};

export function useStations() {
  return useQuery({
    queryKey: KEYS.stations,
    queryFn: async () => {
      const { data } = await api.get<StationSummary[]>("/api/wcs/stations");
      return data;
    },
    refetchInterval: 5_000,
  });
}

export function useStationQueue(stationId: string | null) {
  return useQuery({
    queryKey: stationId ? KEYS.queue(stationId) : ["wcs", "queue", "none"],
    enabled: !!stationId,
    queryFn: async () => {
      const { data } = await api.get<StationQueue>(
        `/api/wcs/stations/${stationId}/queue`,
      );
      return data;
    },
    refetchInterval: 3_000,
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateTaskRequest) => {
      const { data } = await api.post<PickTask>("/api/wcs/tasks", payload);
      return data;
    },
    onSuccess: (task) => {
      qc.invalidateQueries({ queryKey: KEYS.stations });
      qc.invalidateQueries({ queryKey: KEYS.queue(task.station_id) });
    },
  });
}

function taskAction(action: "advance" | "complete" | "exception") {
  return async ({
    stationId,
    taskId,
  }: {
    stationId: string;
    taskId: string;
  }) => {
    const { data } = await api.post<PickTask>(
      `/api/wcs/stations/${stationId}/tasks/${taskId}/${action}`,
    );
    return data;
  };
}

function useTaskMutation(action: "advance" | "complete" | "exception") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: taskAction(action),
    onSuccess: (_data, { stationId }) => {
      qc.invalidateQueries({ queryKey: KEYS.stations });
      qc.invalidateQueries({ queryKey: KEYS.queue(stationId) });
    },
  });
}

export const useAdvanceTask = () => useTaskMutation("advance");
export const useCompleteTask = () => useTaskMutation("complete");
export const useExceptionTask = () => useTaskMutation("exception");
