import type { ReportResponse } from "../types";

export function ReportPanel({ report }: { report: ReportResponse | null }) {
  if (!report) {
    return <div className="panel">Report output will appear here.</div>;
  }

  return (
    <div className="panel">
      <h3>{report.title}</h3>
      <p>{report.executive_summary}</p>
      <h4>Key Findings</h4>
      <ul>{report.key_findings.map((item) => <li key={item}>{item}</li>)}</ul>
      <h4>Recommended Next Actions</h4>
      <ul>{report.recommended_next_actions.map((item) => <li key={item}>{item}</li>)}</ul>
      {report.warnings && report.warnings.length > 0 && (
        <>
          <h4>Warnings</h4>
          <ul>{report.warnings.map((item) => <li key={item}>{item}</li>)}</ul>
        </>
      )}
    </div>
  );
}
