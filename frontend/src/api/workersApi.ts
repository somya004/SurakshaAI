import apiClient from "./client";

export const getWorkers = async () => {
  const response = await apiClient.get("/workers");
  return response.data;
};

export const getWorkerSafety = async () => {
  const response = await apiClient.get("/dashboard/worker-safety");
  return response.data;
};