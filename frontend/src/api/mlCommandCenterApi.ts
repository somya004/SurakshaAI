import apiClient from "./client";
import type {
  CommandCenterAssessment,
  CommandCenterOverview,
  ModelMetrics,
  SensorAssessmentRequest,
} from "../types/mlCommandCenter";

export async function assessSensorData(
  payload: SensorAssessmentRequest,
): Promise<CommandCenterAssessment> {
  const response = await apiClient.post<CommandCenterAssessment>(
    "/ml-command-center/assess",
    payload,
  );
  return response.data;
}

export async function fetchCommandCenterOverview(): Promise<CommandCenterOverview> {
  const response = await apiClient.get<CommandCenterOverview>(
    "/ml-command-center/overview",
  );
  return response.data;
}

export async function fetchModelMetrics(): Promise<ModelMetrics> {
  const response = await apiClient.get<ModelMetrics>(
    "/ml-command-center/model-metrics",
  );
  return response.data;
}
