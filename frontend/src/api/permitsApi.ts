import apiClient from "./client";

export const getPermits = async () => {
  const response = await apiClient.get("/permits");
  return response.data;
};

export const getOperationsSummary = async () => {
  const response = await apiClient.get("/dashboard/operations");
  return response.data;
};