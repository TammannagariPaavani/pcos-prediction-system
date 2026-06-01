import apiClient from "./client";

export async function fetchReport(predictionId) {
  const response = await apiClient.get(`/reports/${predictionId}`);
  return response.data;
}
