import apiClient from "./client";

export const getPlantMap = async () => {
  const response = await apiClient.get("/dashboard/plant-map");
  return response.data;
};