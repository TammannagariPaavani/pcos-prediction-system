import apiClient from "./client";

export async function submitPrediction(payload) {
  const response = await apiClient.post("/predict", payload);
  return response.data;
}
