import apiClient from "./client";

export async function fetchPatients(params = {}) {
  const response = await apiClient.get("/patients", { params });
  return response.data;
}

export async function fetchPatientHistory(patientId) {
  const response = await apiClient.get(`/patients/${patientId}/history`);
  return response.data;
}

export async function fetchMyPatientHistory() {
  const response = await apiClient.get("/patients/me/history");
  return response.data;
}

export async function fetchPatientDraft() {
  const response = await apiClient.get("/patients/me/draft");
  return response.data;
}

export async function savePatientDraft(payload) {
  const response = await apiClient.put("/patients/me/draft", payload);
  return response.data;
}

export async function deletePatientDraft() {
  await apiClient.delete("/patients/me/draft");
}

export async function assignPatient(patientId, doctorUserId) {
  const response = await apiClient.put(`/patients/${patientId}/assignment`, {
    doctor_user_id: doctorUserId
  });
  return response.data;
}

export async function addClinicianNote(patientId, payload) {
  const response = await apiClient.post(`/patients/${patientId}/notes`, payload);
  return response.data;
}
