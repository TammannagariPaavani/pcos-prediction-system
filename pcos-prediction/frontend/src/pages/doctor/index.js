import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { addClinicianNote, fetchPatientHistory, fetchPatients } from "@/api/patients";
import WorkspaceShell from "@/components/WorkspaceShell";
import { useAuth } from "@/context/AuthContext";

const RECOMMENDED_TEST_OPTIONS = [
  "Hormone testing",
  "Insulin testing",
  "Pelvic ultrasound",
  "Thyroid profile",
  "Fasting glucose / HbA1c",
  "Follicular scanning",
  "Vitamin D3 test"
];

export default function DoctorDashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [historyPayload, setHistoryPayload] = useState(null);
  const [riskFilter, setRiskFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [noteText, setNoteText] = useState("");
  const [noteBusy, setNoteBusy] = useState(false);
  const [selectedTests, setSelectedTests] = useState([]);
  const [recommendationText, setRecommendationText] = useState("");
  const [recommendBusy, setRecommendBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
      return;
    }
    if (user && user.role === "patient") {
      router.replace("/patient");
    }
  }, [loading, router, user]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (user?.role !== "doctor" && user?.role !== "admin") {
        return;
      }

      try {
        const response = await fetchPatients({
          page,
          page_size: 8,
          search: search || undefined,
          risk_label: riskFilter === "all" ? undefined : riskFilter
        });
        setPatients(response.items);
        setTotal(response.total);
        setSelectedPatientId((current) => {
          if (current && response.items.some((item) => item.patient_id === current)) {
            return current;
          }
          return response.items[0]?.patient_id || null;
        });
      } catch (requestError) {
        setError(requestError.response?.data?.error || "Unable to load patients.");
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [page, riskFilter, search, user]);

  useEffect(() => {
    const loadHistory = async () => {
      if (!selectedPatientId) {
        setHistoryPayload(null);
        return;
      }
      try {
        const response = await fetchPatientHistory(selectedPatientId);
        setHistoryPayload(response);
      } catch (requestError) {
        setError(requestError.response?.data?.error || "Unable to load history.");
      }
    };

    loadHistory();
  }, [selectedPatientId]);

  const selectedPatient = useMemo(
    () => patients.find((patient) => patient.patient_id === selectedPatientId) || null,
    [patients, selectedPatientId]
  );

  const history = useMemo(
    () =>
      (historyPayload?.predictions || []).map((item) => ({
        created_at: new Date(item.created_at).toLocaleDateString(),
        risk_score: Number((item.risk_score * 100).toFixed(1)),
        risk_label: item.risk_label
      })),
    [historyPayload]
  );

  const recommendedTestsNotes = useMemo(
    () => (historyPayload?.notes || []).filter((note) => note.note_type === "recommended_tests"),
    [historyPayload]
  );

  const totalPages = Math.max(1, Math.ceil(total / 8));

  const exportCsv = () => {
    const rows = [
      ["Patient ID", "Patient Name", "Email", "BMI", "Risk Label", "Risk Score", "Assigned Doctor"],
      ...patients.map((patient) => [
        patient.patient_id,
        patient.full_name,
        patient.email,
        patient.bmi ?? "",
        patient.latest_risk_label ?? "Unscreened",
        patient.latest_risk_score ?? "",
        patient.assigned_doctor_name ?? ""
      ])
    ];
    const blob = new Blob([rows.map((row) => row.join(",")).join("\n")], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "pcos-patient-dashboard.csv";
    link.click();
  };

  const handleCreateNote = async () => {
    if (!selectedPatientId || !noteText.trim()) {
      return;
    }
    setNoteBusy(true);
    setError("");
    try {
      await addClinicianNote(selectedPatientId, {
        note_text: noteText,
        note_type: "clinical"
      });
      const refreshed = await fetchPatientHistory(selectedPatientId);
      setHistoryPayload(refreshed);
      setNoteText("");
    } catch (requestError) {
      setError(requestError.response?.data?.error || "Unable to save clinician note.");
    } finally {
      setNoteBusy(false);
    }
  };

  const toggleSuggestedTest = (label) => {
    setSelectedTests((current) =>
      current.includes(label) ? current.filter((item) => item !== label) : [...current, label]
    );
  };

  const handleRecommendTests = async () => {
    if (!selectedPatientId || selectedTests.length === 0) {
      setError("Select at least one recommended test for this patient.");
      return;
    }

    setRecommendBusy(true);
    setError("");
    try {
      const noteLines = ["Recommended tests:", ...selectedTests.map((item) => `- ${item}`)];
      if (recommendationText.trim()) {
        noteLines.push("", `Doctor note: ${recommendationText.trim()}`);
      }

      await addClinicianNote(selectedPatientId, {
        note_text: noteLines.join("\n"),
        note_type: "recommended_tests"
      });
      const refreshed = await fetchPatientHistory(selectedPatientId);
      setHistoryPayload(refreshed);
      setSelectedTests([]);
      setRecommendationText("");
    } catch (requestError) {
      setError(requestError.response?.data?.error || "Unable to save suggested tests.");
    } finally {
      setRecommendBusy(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <WorkspaceShell
      title="Doctor Dashboard"
      subtitle="Review patient-submitted screenings, suggest the right next tests, inspect risk trends, and document follow-up plans."
    >
      <div className="grid gap-6">
        <div className="rounded-3xl bg-white p-5 text-sm leading-6 text-slate-700 shadow-sm">
          <span className="font-semibold text-pine">Doctor role:</span> patients can complete basic screening details
          on their own, while doctors review the risk level, suggest the next tests like hormone panels or pelvic
          ultrasound, and add follow-up notes that appear in the patient&apos;s portal.
        </div>

        <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
          <div className="metric-card">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Care Queue</p>
                <h2 className="mt-2 text-2xl">Assigned Patients</h2>
              </div>
              <button type="button" onClick={exportCsv} className="rounded-full bg-ember px-4 py-2 text-sm font-semibold text-white">
                Export CSV
              </button>
            </div>

            <div className="mb-4 grid gap-3 md:grid-cols-[1fr_180px]">
              <input
                type="text"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search patient name or email"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              />
              <select
                value={riskFilter}
                onChange={(event) => {
                  setRiskFilter(event.target.value);
                  setPage(1);
                }}
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              >
                <option value="all">All Risk Bands</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
                <option value="Unscreened">Unscreened</option>
              </select>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-3">Patient</th>
                    <th className="py-3">Age</th>
                    <th className="py-3">BMI</th>
                    <th className="py-3">Risk</th>
                    <th className="py-3">Predictions</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.length ? (
                    patients.map((patient) => (
                      <tr
                        key={patient.patient_id}
                        className={`cursor-pointer border-b border-slate-100 transition hover:bg-clay/40 ${
                          selectedPatientId === patient.patient_id ? "bg-clay/50" : ""
                        }`}
                        onClick={() => setSelectedPatientId(patient.patient_id)}
                      >
                        <td className="py-4">
                          <div className="font-semibold text-slate-800">{patient.full_name}</div>
                          <div className="text-xs text-slate-500">{patient.email}</div>
                        </td>
                        <td className="py-4">{patient.age ?? "N/A"}</td>
                        <td className="py-4">{patient.bmi ?? "N/A"}</td>
                        <td className="py-4">
                          <div>{patient.latest_risk_label ?? "Unscreened"}</div>
                          <div className="text-xs text-slate-500">
                            {typeof patient.latest_risk_score === "number"
                              ? `${Math.round(patient.latest_risk_score * 100)}%`
                              : "No score yet"}
                          </div>
                        </td>
                        <td className="py-4">{patient.prediction_count}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-sm text-slate-500">
                        No patients are assigned to this doctor yet. Ask admin to assign patients first.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.max(current - 1, 1))}
                  disabled={page === 1}
                  className="rounded-full border border-slate-200 px-4 py-2 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.min(current + 1, totalPages))}
                  disabled={page >= totalPages}
                  className="rounded-full border border-slate-200 px-4 py-2 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="metric-card h-[360px]">
              <div className="mb-4">
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Trend View</p>
                <h2 className="mt-2 text-2xl">{selectedPatient ? selectedPatient.full_name : "Select a patient"}</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {historyPayload?.patient?.assignment?.doctor
                    ? `Assigned to ${historyPayload.patient.assignment.doctor.full_name}`
                    : "No doctor assignment is recorded yet."}
                </p>
              </div>
              <div className="pointer-events-none h-[80%]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#D9E4E8" />
                    <XAxis dataKey="created_at" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="risk_score" stroke="#0F4C5C" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="metric-card">
              <div className="mb-4">
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Test Suggestions</p>
                <h2 className="mt-2 text-2xl">Recommend Next Tests</h2>
                <p className="mt-2 text-sm text-slate-500">
                  Choose the investigations this patient should complete next. The same recommendation will appear in
                  the patient&apos;s portal.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {RECOMMENDED_TEST_OPTIONS.map((item) => (
                  <label key={item} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4">
                    <input
                      type="checkbox"
                      checked={selectedTests.includes(item)}
                      onChange={() => toggleSuggestedTest(item)}
                      className="h-4 w-4 rounded border-slate-300 text-pine focus:ring-pine"
                    />
                    <span className="text-sm text-slate-700">{item}</span>
                  </label>
                ))}
              </div>

              <label className="mt-4 block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">Doctor instruction</span>
                <textarea
                  value={recommendationText}
                  onChange={(event) => setRecommendationText(event.target.value)}
                  rows={3}
                  placeholder="Example: Complete these tests before the next follow-up visit."
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                />
              </label>
              <button
                type="button"
                onClick={handleRecommendTests}
                disabled={recommendBusy || !selectedPatientId}
                className="mt-4 rounded-full bg-ember px-5 py-3 font-semibold text-white disabled:opacity-60"
              >
                {recommendBusy ? "Saving..." : "Send Test Recommendation"}
              </button>

              <div className="mt-5 space-y-3">
                {recommendedTestsNotes.map((note) => (
                  <div key={note.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="text-xs uppercase tracking-[0.25em] text-slate-500">
                      {new Date(note.created_at).toLocaleString()}
                    </div>
                    <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-700">{note.note_text}</p>
                  </div>
                ))}
                {historyPayload && recommendedTestsNotes.length === 0 ? (
                  <div className="rounded-2xl bg-clay/50 p-4 text-sm text-slate-600">
                    No test recommendations have been sent for this patient yet.
                  </div>
                ) : null}
              </div>
            </div>

            <div className="metric-card">
              <div className="mb-4">
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Clinical Notes</p>
                <h2 className="mt-2 text-2xl">Follow-up Summary</h2>
              </div>

              <div className="mb-4 space-y-3">
                {(historyPayload?.notes || [])
                  .filter((note) => note.note_type !== "recommended_tests")
                  .map((note) => (
                    <div key={note.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs uppercase tracking-[0.25em] text-slate-500">
                        <span>{note.note_type}</span>
                        <span>{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                      <p className="mt-3 text-sm text-slate-700">{note.note_text}</p>
                      <p className="mt-3 text-xs text-slate-500">By {note.author.full_name}</p>
                    </div>
                  ))}
                {historyPayload &&
                historyPayload.notes.filter((note) => note.note_type !== "recommended_tests").length === 0 ? (
                  <div className="rounded-2xl bg-clay/50 p-4 text-sm text-slate-600">
                    No clinician notes yet for this patient.
                  </div>
                ) : null}
              </div>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">Add follow-up note</span>
                <textarea
                  value={noteText}
                  onChange={(event) => setNoteText(event.target.value)}
                  rows={4}
                  placeholder="Document the plan, referral, or follow-up discussion."
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                />
              </label>
              <button
                type="button"
                onClick={handleCreateNote}
                disabled={noteBusy || !selectedPatientId}
                className="mt-4 rounded-full bg-pine px-5 py-3 font-semibold text-white disabled:opacity-60"
              >
                {noteBusy ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>
        </div>

        {error ? <div className="rounded-2xl bg-red-50 p-4 text-sm text-red-600">{error}</div> : null}
      </div>
    </WorkspaceShell>
  );
}
