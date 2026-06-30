import type { AnalyzeRangeResponse } from "../types";

export function AnalysisPanel({ result }: { result: AnalyzeRangeResponse | null }) {
  if (!result) {
    return <div className="panel">Analysis results will appear here.</div>;
  }

  return (
    <div className="panel">
      <h3>Analysis Summary</h3>
      <p>{result.summary}</p>
      <p>Table Type: {result.table_type_guess}</p>
      <h4>Detected Columns</h4>
      <ul>
        {result.detected_columns.map((column) => (
          <li key={column.name}>{column.name}: {column.type} ({Math.round(column.confidence * 100)}%)</li>
        ))}
      </ul>
      <h4>Data Quality Issues</h4>
      <ul>
        {result.data_quality_issues.map((issue, index) => (
          <li key={`${issue.target_column}-${index}`}>{issue.severity}: {issue.issue} [{issue.target_column}]</li>
        ))}
      </ul>
      <h4>Recommended Actions</h4>
      <ul>
        {result.recommended_actions.map((action, index) => (
          <li key={`${action.action_type}-${index}`}>{action.description}</li>
        ))}
      </ul>
      {result.warnings && result.warnings.length > 0 && (
        <>
          <h4>Warnings</h4>
          <ul>
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
