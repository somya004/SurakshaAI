import apiClient from "./client";

export const getRiskEvents = async () => {
  const response = await apiClient.get("/risks");
  return response.data;
};

export const getDashboardSummary = async () => {
  const response = await apiClient.get("/dashboard/summary");
  return response.data;
};

export const getPlantMap = async () => {
  const response = await apiClient.get("/dashboard/plant-map");
  return response.data;
};

export const getWorkerSafety = async () => {
  const response = await apiClient.get("/dashboard/worker-safety");
  return response.data;
};

export const getOperationsSummary = async () => {
  const response = await apiClient.get("/dashboard/operations");
  return response.data;
};

export const getEmergencyResponse = async () => {
  const response = await apiClient.get("/dashboard/emergency-response");
  return response.data;
};