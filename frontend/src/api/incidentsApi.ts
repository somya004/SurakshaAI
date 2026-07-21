import apiClient from "./client";

export const getIncidents = async () => {
  const response = await apiClient.get("/incidents");
  return response.data;
};

export const getAlerts = async () => {
  const response = await apiClient.get("/alerts");
  return response.data;
};