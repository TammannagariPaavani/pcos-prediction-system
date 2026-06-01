import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import { createDoctor, deployModel, fetchAdminStats, fetchDoctors } from "@/api/admin";
import { assignPatient, fetchPatients } from "@/api/patients";
import WorkspaceShell from "@/components/WorkspaceShell";
import { useAuth } from "@/context/AuthContext";

export default function AdminPanelPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [patientPage, setPatientPage] = useState(1);
  const [patientTotal, setPatientTotal] = useState(0);
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedDoctors, setSelectedDoctors] = useState({});
  const [modelVersion, setModelVersion] = useState("v1.4.0");
  const [modelFile, setModelFile] = useState(null);
  const [doctorForm, setDoctorForm] = useState({
    full_name: "",
    email: "",
    password: ""
  });
  const [doctorBusy, setDoctorBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
      return;
    }
    if (user && user.role !== "admin") {
      router.replace(user.role === "patient" ? "/patient" : "/doctor");
    }
  }, [loading, router, user]);

  useEffect(() => {
    const hydrateStats = async () => {
      try {
        const response = await fetchAdminStats();
        setStats(response);
      } catch (error) {
        setMessage(error.response?.data?.error || "Unable to load admin statistics.");
      }
    };

    const hydrateDoctors = async () => {
      try {
        const response = await fetchDoctors();
        setDoctors(response);
      } catch (error) {
        setMessage(error.response?.data?.error || "Unable to load doctor directory.");
      }
    };

    if (user?.role === "admin") {
      hydrateStats();
      hydrateDoctors();
    }
  }, [user]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (user?.role !== "admin") {
        return;
      }
      try {
        const response = await fetchPatients({
          page: patientPage,
          page_size: 6,
          search: patientSearch || undefined
        });
        setPatients(response.items);
        setPatientTotal(response.total);
        setSelectedDoctors((current) => {
          const next = { ...current };
          response.items.forEach((item) => {
            if (!next[item.patient_id]) {
              next[item.patient_id] = item.assigned_doctor_id || "";
            }
          });
          return next;
        });
      } catch (error) {
        setMessage(error.response?.data?.error || "Unable to load patient assignment queue.");
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [patientPage, patientSearch, user]);

  const totalPages = Math.max(1, Math.ceil(patientTotal / 6));

  const modelCards = useMemo(
    () => [
      {
        label: "Total Doctors",
        value: stats?.total_doctors ?? "--"
      },
      {
        label: "Total Patients",
        value: stats?.total_patients ?? "--"
      },
      {
        label: "High-Risk Patients",
        value: stats?.total_high_risk_patients ?? "--"
      },
      {
        label: "Artifact Status",
        value: stats?.model_governance?.artifact_available ? "Ready" : "Offline"
      },
      {
        label: "Feature Count",
        value: stats?.model_governance?.feature_count ?? "--"
      },
      {
        label: "Explainer",
        value: stats?.model_governance?.explainer_model_name ?? "--"
      },
      {
        label: "Environment",
        value: stats?.model_governance?.environment ?? "--"
      }
    ],
    [stats]
  );

  const refreshDashboard = async () => {
    const [statsResponse, patientResponse] = await Promise.all([
      fetchAdminStats(),
      fetchPatients({ page: patientPage, page_size: 6, search: patientSearch || undefined })
    ]);
    setStats(statsResponse);
    setPatients(patientResponse.items);
    setPatientTotal(patientResponse.total);
  };

  const handleDeploy = async () => {
    if (!modelFile) {
      setMessage("Choose a .joblib file before deploying.");
      return;
    }
    try {
      const response = await deployModel({ modelVersion, modelFile });
      setMessage(`Model ${response.model_version} deployed successfully.`);
      await refreshDashboard();
    } catch (error) {
      setMessage(error.response?.data?.error || "Model deployment failed.");
    }
  };

  const handleAssignPatient = async (patientId) => {
    const doctorUserId = selectedDoctors[patientId];
    if (!doctorUserId) {
      setMessage("Choose a doctor before assigning a patient.");
      return;
    }
    try {
      await assignPatient(patientId, doctorUserId);
      setMessage("Patient assignment updated.");
      await refreshDashboard();
    } catch (error) {
      setMessage(error.response?.data?.error || "Unable to update patient assignment.");
    }
  };

  const handleCreateDoctor = async () => {
    if (!doctorForm.full_name || !doctorForm.email || !doctorForm.password) {
      setMessage("Fill in full name, email, and password to create a doctor account.");
      return;
    }
    setDoctorBusy(true);
    try {
      const response = await createDoctor(doctorForm);
      setMessage(`Doctor account created for ${response.full_name}.`);
      setDoctorForm({
        full_name: "",
        email: "",
        password: ""
      });
      const [statsResponse, doctorsResponse] = await Promise.all([fetchAdminStats(), fetchDoctors()]);
      setStats(statsResponse);
      setDoctors(doctorsResponse);
    } catch (error) {
      setMessage(error.response?.data?.error || "Unable to create doctor account.");
    } finally {
      setDoctorBusy(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <WorkspaceShell
      title="Admin Panel"
      subtitle="Monitor adoption, review model readiness, and manage the doctor assignment workflow for the clinic."
    >
      <div className="grid gap-6">
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <div className="metric-card">
            <p className="text-sm uppercase tracking-[0.25em] text-slate-500">Active Users</p>
            <p className="mt-3 text-4xl font-extrabold text-pine">{stats?.active_users ?? "--"}</p>
          </div>
          <div className="metric-card">
            <p className="text-sm uppercase tracking-[0.25em] text-slate-500">Predictions Today</p>
            <p className="mt-3 text-4xl font-extrabold text-pine">{stats?.total_predictions_today ?? "--"}</p>
          </div>
          <div className="metric-card">
            <p className="text-sm uppercase tracking-[0.25em] text-slate-500">Predictions This Week</p>
            <p className="mt-3 text-4xl font-extrabold text-pine">{stats?.total_predictions_week ?? "--"}</p>
          </div>
          <div className="metric-card">
            <p className="text-sm uppercase tracking-[0.25em] text-slate-500">Model Version</p>
            <p className="mt-3 text-4xl font-extrabold text-pine">{stats?.model_version_deployed ?? "--"}</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {modelCards.map((card) => (
            <div key={card.label} className="metric-card">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">{card.label}</p>
              <p className="mt-3 text-2xl font-bold text-slate-800">{card.value}</p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="grid gap-6">
            <div className="metric-card">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">User Management</p>
              <h2 className="mt-2 text-2xl">Create Doctor Account</h2>
              <div className="mt-5 space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">Full Name</span>
                  <input
                    type="text"
                    value={doctorForm.full_name}
                    onChange={(event) =>
                      setDoctorForm((current) => ({
                        ...current,
                        full_name: event.target.value
                      }))
                    }
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">Email</span>
                  <input
                    type="email"
                    value={doctorForm.email}
                    onChange={(event) =>
                      setDoctorForm((current) => ({
                        ...current,
                        email: event.target.value
                      }))
                    }
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">Password</span>
                  <input
                    type="password"
                    value={doctorForm.password}
                    onChange={(event) =>
                      setDoctorForm((current) => ({
                        ...current,
                        password: event.target.value
                      }))
                    }
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                  />
                </label>
                <button
                  type="button"
                  onClick={handleCreateDoctor}
                  disabled={doctorBusy}
                  className="rounded-full bg-pine px-5 py-3 font-semibold text-white disabled:opacity-60"
                >
                  {doctorBusy ? "Creating..." : "Create Doctor"}
                </button>
              </div>
            </div>

            <div className="metric-card">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Deployment</p>
              <h2 className="mt-2 text-2xl">Hot-Swap Model</h2>
              <div className="mt-5 space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">Model Version</span>
                  <input
                    type="text"
                    value={modelVersion}
                    onChange={(event) => setModelVersion(event.target.value)}
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">Artifact File</span>
                  <input
                    type="file"
                    accept=".joblib"
                    onChange={(event) => setModelFile(event.target.files?.[0] || null)}
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                  />
                </label>
                <p className="text-sm text-slate-500">
                  Current artifact path: {stats?.model_governance?.artifact_path || "--"}
                </p>
                <button type="button" onClick={handleDeploy} className="rounded-full bg-ember px-5 py-3 font-semibold text-white">
                  Deploy Model
                </button>
              </div>
            </div>

            <div className="metric-card">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Care Team</p>
              <h2 className="mt-2 text-2xl">Doctor Directory</h2>
              <div className="mt-4 space-y-3">
                {doctors.map((doctor) => (
                  <div key={doctor.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="font-semibold text-slate-800">{doctor.full_name}</div>
                    <div className="text-sm text-slate-500">{doctor.email}</div>
                    <div className="mt-2 text-xs uppercase tracking-[0.25em] text-slate-500">
                      {doctor.assigned_patient_count} assigned patients
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="metric-card">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Workflow</p>
                  <h2 className="mt-2 text-2xl">Patient Assignment Queue</h2>
                </div>
                <input
                  type="text"
                  value={patientSearch}
                  onChange={(event) => {
                    setPatientSearch(event.target.value);
                    setPatientPage(1);
                  }}
                  placeholder="Search patient name or email"
                  className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                />
              </div>

              <div className="space-y-4">
                {patients.map((patient) => (
                  <div key={patient.patient_id} className="rounded-3xl border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-lg font-semibold text-slate-800">{patient.full_name}</div>
                        <div className="text-sm text-slate-500">{patient.email}</div>
                      </div>
                      <div className="rounded-full bg-clay px-4 py-2 text-sm font-semibold text-pine">
                        {patient.latest_risk_label || "Unscreened"}
                      </div>
                    </div>
                    <div className="mt-4 grid gap-3 md:grid-cols-[1fr_140px]">
                      <select
                        value={selectedDoctors[patient.patient_id] || ""}
                        onChange={(event) =>
                          setSelectedDoctors((current) => ({
                            ...current,
                            [patient.patient_id]: event.target.value
                          }))
                        }
                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                      >
                        <option value="">Select doctor</option>
                        {doctors.map((doctor) => (
                          <option key={doctor.id} value={doctor.id}>
                            {doctor.full_name}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => handleAssignPatient(patient.patient_id)}
                        className="rounded-full bg-pine px-4 py-3 text-sm font-semibold text-white"
                      >
                        Assign
                      </button>
                    </div>
                    <p className="mt-3 text-sm text-slate-500">
                      Current doctor: {patient.assigned_doctor_name || "Not assigned"}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
                <span>
                  Page {patientPage} of {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setPatientPage((current) => Math.max(current - 1, 1))}
                    disabled={patientPage === 1}
                    className="rounded-full border border-slate-200 px-4 py-2 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    onClick={() => setPatientPage((current) => Math.min(current + 1, totalPages))}
                    disabled={patientPage >= totalPages}
                    className="rounded-full border border-slate-200 px-4 py-2 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Audit Log</p>
              <h2 className="mt-2 text-2xl">Recent Activity</h2>
              <div className="mt-5 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-200 text-slate-500">
                    <tr>
                      <th className="py-3">Action</th>
                      <th className="py-3">Actor</th>
                      <th className="py-3">Resource</th>
                      <th className="py-3">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats?.recent_audit_log?.map((entry) => (
                      <tr key={entry.id} className="border-b border-slate-100">
                        <td className="py-4 font-semibold text-slate-800">{entry.action}</td>
                        <td className="py-4">
                          <div>{entry.user_name || entry.user_id}</div>
                          <div className="text-xs text-slate-500">{entry.user_email || ""}</div>
                        </td>
                        <td className="py-4">{entry.resource}</td>
                        <td className="py-4">{new Date(entry.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        {message ? <div className="rounded-2xl bg-clay/60 p-4 text-sm text-slate-700">{message}</div> : null}
      </div>
    </WorkspaceShell>
  );
}
