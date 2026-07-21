import apiClient from "./client";

export const getAnalyticsData = async () => {
  const [
    dashboardResponse,
    risksResponse,
    workerSafetyResponse,
    plantMapResponse,
    operationsResponse,
    incidentsResponse,
    alertsResponse,
  ] = await Promise.all([
    apiClient.get("/dashboard/summary"),
    apiClient.get("/risks"),
    apiClient.get("/dashboard/worker-safety"),
    apiClient.get("/dashboard/plant-map"),
    apiClient.get("/dashboard/operations"),
    apiClient.get("/incidents"),
    apiClient.get("/alerts"),
  ]);

  return {
    dashboard: dashboardResponse.data,
    risks: risksResponse.data,
    workerSafety: workerSafetyResponse.data,
    plantMap: plantMapResponse.data,
    operations: operationsResponse.data,
    incidents: incidentsResponse.data,
    alerts: alertsResponse.data,
  };
};