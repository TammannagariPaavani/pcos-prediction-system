export default function ReportViewer({ report }) {
  return (
    <div className="metric-card">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Report</p>
          <h3 className="mt-2 text-2xl">Clinical PDF</h3>
        </div>
        {report?.download_url ? (
          <a
            href={report.download_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-full bg-pine px-5 py-3 text-sm font-semibold text-white"
          >
            Download Report
          </a>
        ) : null}
      </div>
      {report?.download_url ? (
        <iframe
          title="Prediction report"
          src={report.download_url}
          className="pointer-events-none h-[420px] w-full rounded-3xl border border-slate-200"
        />
      ) : (
        <div className="grid h-[420px] place-items-center rounded-3xl border border-dashed border-slate-300 text-center text-slate-500">
          <p>Generate a report after a prediction to preview the PDF here.</p>
        </div>
      )}
    </div>
  );
}
