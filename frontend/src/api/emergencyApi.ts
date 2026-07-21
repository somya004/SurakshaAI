import apiClient from "./client";

export const getResponseActions = async () => {
  const response = await apiClient.get("/response-actions");
  return response.data;
};

export const getEmergencySummary = async () => {
  const response = await apiClient.get("/dashboard/emergency-response");
  return response.data;
};