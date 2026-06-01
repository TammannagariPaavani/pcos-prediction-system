export default function RiskCard({ result }) {
  if (!result) {
    return (
      <div className="metric-card flex min-h-[280px] items-center justify-center">
        <p className="max-w-sm text-center text-slate-500">
          Submit a patient profile to generate a calibrated PCOS risk score, risk tier, and personalized recommendation.
        </p>
      </div>
    );
  }

  const percent = Math.round((result?.risk_score || 0) * 100);

  const missingFields = result?.missing_clinical_fields || [];
  const missingPreview = missingFields.slice(0, 4).join(", ");
  const hiddenMissingCount = Math.max(missingFields.length - 4, 0);

  const clinicalStatus = result?.clinical_data_status
    ? result.clinical_data_status.replace(/_/g, " ")
    : "N/A";

  return (
    <div className="metric-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">
            Risk Output
          </p>
          <h3 className="mt-2 text-2xl">Prediction Summary</h3>
        </div>
        <span
          className="rounded-full px-4 py-2 text-sm font-bold text-white"
          style={{ backgroundColor: result?.risk_color || "#999" }}
        >
          {result?.risk_label || "Unknown"}
        </span>
      </div>

      <div className="mt-8 flex flex-col items-center gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div
          className="grid h-44 w-44 place-items-center rounded-full"
          style={{
            background: `conic-gradient(${result?.risk_color || "#999"} ${
              percent * 3.6
            }deg, rgba(15,76,92,0.12) 0deg)`
          }}
        >
          <div className="grid h-32 w-32 place-items-center rounded-full bg-white shadow-inner">
            <div className="text-center">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
                Risk
              </p>
              <p className="text-4xl font-extrabold text-pine">
                {percent}%
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-md space-y-3">
          <div className="rounded-3xl bg-clay/70 p-4">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
              Recommendation
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {result?.recommendation || "No recommendation available"}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-3xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Assessment Type</p>
              <p className="mt-1 font-bold text-pine">
                {result?.assessment_type || "N/A"}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Clinical Data</p>
              <p className="mt-1 font-bold capitalize text-pine">
                {clinicalStatus}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Model Version</p>
              <p className="mt-1 font-bold text-pine">
                {result?.model_version || "N/A"}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Prediction ID</p>
              <p className="mt-1 truncate font-bold text-pine">
                {result?.prediction_id || "N/A"}
              </p>
            </div>
          </div>

          {missingFields.length > 0 && (
            <div className="rounded-3xl bg-white p-4 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
                Still Missing
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                {missingPreview}
                {hiddenMissingCount
                  ? ` and ${hiddenMissingCount} more clinical fields`
                  : ""}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}