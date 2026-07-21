import apiClient from "./client";

export const getDashboardSummary = async () => {
  const response = await apiClient.get("/dashboard/summary");
  return response.data;
};

export const getRiskByZone = async () => {
  const response = await apiClient.get("/dashboard/risk-by-zone");
  return response.data;
};

export const getRiskTrend = async () => {
  const response = await apiClient.get("/dashboard/risk-trend");
  return response.data;
};

export const getActiveIncidents = async () => {
  const response = await apiClient.get("/dashboard/active-incidents");
  return response.data;
};

export const getPlantMap = async () => {
  const response = await apiClient.get("/dashboard/plant-map");
  return response.data;
};