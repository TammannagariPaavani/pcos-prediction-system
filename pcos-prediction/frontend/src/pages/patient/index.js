import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import InputForm, { createEmptyPredictionValues } from "@/components/InputForm";
import ReportViewer from "@/components/ReportViewer";
import RiskCard from "@/components/RiskCard";
import SHAPChart from "@/components/SHAPChart";
import WorkspaceShell from "@/components/WorkspaceShell";
import { submitPrediction } from "@/api/predict";
import { fetchReport } from "@/api/reports";
import { deletePatientDraft, fetchMyPatientHistory, fetchPatientDraft, savePatientDraft } from "@/api/patients";
import { useAuth } from "@/context/AuthContext";

export default function PatientPortalPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [result, setResult] = useState(null);
  const [report, setReport] = useState(null);
  const [historyPayload, setHistoryPayload] = useState(null);
  const [busy, setBusy] = useState(false);
  const [draftBusy, setDraftBusy] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);
  const [loadDraftBusy, setLoadDraftBusy] = useState(false);
  const [error, setError] = useState("");
  const [draftFeedback, setDraftFeedback] = useState("");
  const [formState, setFormState] = useState({
    key: Date.now(),
    values: createEmptyPredictionValues(),
    step: 0,
    lastSavedAt: null
  });

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
      return;
    }
    if (user && user.role !== "patient") {
      router.replace(user.role === "doctor" ? "/doctor" : "/admin");
    }
  }, [loading, router, user]);

  useEffect(() => {
    setFormState({
      key: Date.now(),
      values: createEmptyPredictionValues(),
      step: 0,
      lastSavedAt: null
    });
  }, []);

  useEffect(() => {
    const loadHistory = async () => {
      if (user?.role !== "patient") {
        return;
      }
      try {
        const response = await fetchMyPatientHistory();
        setHistoryPayload(response);
      } catch (requestError) {
        if (requestError.response?.data?.code !== "PATIENT_NOT_FOUND") {
          setDraftFeedback(requestError.response?.data?.error || "Unable to load doctor updates.");
        }
      }
    };

    loadHistory();
  }, [user]);

  const handleSaveDraft = async (payload) => {
    setDraftBusy(true);
    setDraftFeedback("");
    try {
      const draft = await savePatientDraft(payload);
      setFormState((current) => ({
        ...current,
        lastSavedAt: draft.updated_at
      }));
      setDraftFeedback("Draft saved successfully.");
    } catch (requestError) {
      setDraftFeedback(requestError.response?.data?.error || "Unable to save draft.");
    } finally {
      setDraftBusy(false);
    }
  };

  const handlePrediction = async (payload) => {
    setBusy(true);
    setError("");
    try {
      const response = await submitPrediction(payload);
      setResult(response);
      const reportResponse = await fetchReport(response.prediction_id);
      setReport(reportResponse);
      const refreshedHistory = await fetchMyPatientHistory();
      setHistoryPayload(refreshedHistory);
      await deletePatientDraft();
      setFormState((current) => ({
        ...current,
        lastSavedAt: null
      }));
      setDraftFeedback("Prediction submitted. Saved draft cleared.");
    } catch (requestError) {
      setError(requestError.response?.data?.error || "Prediction failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleResetForm = async () => {
    setResetBusy(true);
    setError("");
    try {
      await deletePatientDraft();
      setFormState({
        key: Date.now(),
        values: createEmptyPredictionValues(),
        step: 0,
        lastSavedAt: null
      });
      setResult(null);
      setReport(null);
      setDraftFeedback("Form cleared. Saved draft removed.");
    } catch (requestError) {
      setDraftFeedback(requestError.response?.data?.error || "Unable to clear saved draft.");
    } finally {
      setResetBusy(false);
    }
  };

  const handleLoadDraft = async () => {
    setLoadDraftBusy(true);
    setError("");
    try {
      const draft = await fetchPatientDraft();
      setFormState({
        key: Date.now(),
        values: { ...createEmptyPredictionValues(), ...draft.draft_payload },
        step: draft.current_step,
        lastSavedAt: draft.updated_at
      });
      setResult(null);
      setReport(null);
      setDraftFeedback("Saved draft restored.");
    } catch (requestError) {
      setDraftFeedback(requestError.response?.data?.error || "No saved draft found.");
    } finally {
      setLoadDraftBusy(false);
    }
  };

  if (!user) {
    return null;
  }

  const recommendedTestsNotes = (historyPayload?.notes || []).filter((note) => note.note_type === "recommended_tests");
  const assignedDoctor = historyPayload?.patient?.assignment?.doctor || null;
  const assignedBy = historyPayload?.patient?.assignment?.assigned_by || null;

  return (
    <WorkspaceShell
      title="Patient Portal"
      subtitle="Start with your basic details and symptoms, get a PCOS risk result, and receive doctor-recommended next tests in the same portal."
    >
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            <Link href="/logout" prefetch={false} className="rounded-full bg-ember px-5 py-3 font-semibold text-white">
              Log Out
            </Link>
            <button
              type="button"
              onClick={handleLoadDraft}
              disabled={loadDraftBusy}
              className="rounded-full border border-slate-200 bg-white px-5 py-3 font-semibold text-slate-700 disabled:opacity-60"
            >
              {loadDraftBusy ? "Loading Draft..." : "Load Saved Draft"}
            </button>
          </div>

          <InputForm
            key={formState.key}
            onSubmit={handlePrediction}
            loading={busy}
            initialValues={formState.values}
            initialStep={formState.step}
            onSaveDraft={handleSaveDraft}
            onReset={handleResetForm}
            savingDraft={draftBusy}
            resetting={resetBusy}
            lastSavedAt={formState.lastSavedAt}
          />

          <div className="rounded-3xl bg-white p-4 text-sm text-slate-600 shadow-sm">
            Enter the basic details you know, like age, weight, cycle pattern, and symptoms. If your screening shows
            meaningful risk, your doctor can suggest the next tests such as hormone testing, insulin testing, or pelvic
            ultrasound, and those suggestions will appear below.
          </div>

          {draftFeedback ? <div className="rounded-3xl bg-clay/60 p-4 text-sm text-slate-700">{draftFeedback}</div> : null}
          {error ? <div className="rounded-3xl bg-red-50 p-4 text-sm text-red-600">{error}</div> : null}
          <ReportViewer report={report} />
        </div>

        <div className="space-y-6">
          <RiskCard result={result} />

          <div className="metric-card">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Care Team</p>
              <h3 className="mt-2 text-2xl">Assigned Doctor</h3>
              <p className="mt-2 text-sm text-slate-500">
                This is the doctor assigned to you by admin for review and follow-up.
              </p>
            </div>
            {assignedDoctor ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="text-lg font-semibold text-slate-800">{assignedDoctor.full_name}</div>
                <div className="mt-1 text-sm text-slate-500">{assignedDoctor.email}</div>
                {assignedBy ? (
                  <div className="mt-3 text-xs uppercase tracking-[0.25em] text-slate-500">
                    Assigned by {assignedBy.full_name}
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="rounded-2xl bg-clay/50 p-4 text-sm text-slate-600">
                No doctor has been assigned yet. Once admin assigns a doctor, the doctor details will appear here.
              </div>
            )}
          </div>

          <div className="metric-card">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Doctor Suggestions</p>
              <h3 className="mt-2 text-2xl">Recommended Tests</h3>
              <p className="mt-2 text-sm text-slate-500">
                Your doctor can send follow-up tests here after reviewing your screening result.
              </p>
            </div>
            <div className="space-y-3">
              {recommendedTestsNotes.map((note) => (
                <div key={note.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-500">
                    {new Date(note.created_at).toLocaleString()}
                  </div>
                  <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-700">{note.note_text}</p>
                  <p className="mt-3 text-xs text-slate-500">Shared by {note.author.full_name}</p>
                </div>
              ))}
              {recommendedTestsNotes.length === 0 ? (
                <div className="rounded-2xl bg-clay/50 p-4 text-sm text-slate-600">
                  No doctor test recommendations yet. After the doctor reviews your risk, suggested tests will appear
                  here.
                </div>
              ) : null}
            </div>
          </div>

          <SHAPChart features={result?.top_features || []} />
        </div>
      </div>
    </WorkspaceShell>
  );
}
