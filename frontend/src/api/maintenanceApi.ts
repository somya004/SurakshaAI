import apiClient from "./client";

export const getMaintenanceOrders = async () => {
  const response = await apiClient.get("/maintenance");
  return response.data;
};

export const getOperationsSummary = async () => {
  const response = await apiClient.get("/dashboard/operations");
  return response.data;
};