import apiClient from "./client";

export async function fetchAdminStats() {
  const response = await apiClient.get("/admin/stats");
  return response.data;
}

export async function fetchDoctors() {
  const response = await apiClient.get("/admin/doctors");
  return response.data;
}

export async function createDoctor(payload) {
  const response = await apiClient.post("/admin/doctors", payload);
  return response.data;
}

export async function deployModel({ modelVersion, modelFile }) {
  const formData = new FormData();
  formData.append("model_version", modelVersion);
  formData.append("model_file", modelFile);
  const response = await apiClient.put("/admin/model/deploy", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return response.data;
}
