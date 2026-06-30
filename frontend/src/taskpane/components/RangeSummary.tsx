import type { RangeContext } from "../types";

export function RangeSummary({ context }: { context: RangeContext | null }) {
  if (!context) {
    return <div className="panel">No selection loaded yet.</div>;
  }

  return (
    <div className="panel">
      <h3>Selected Range Summary</h3>
      <p>{context.worksheetName} | {context.rangeAddress}</p>
      <p>{context.rowCount} rows x {context.columnCount} columns</p>
      <p>Headers: {context.headers.join(", ") || "None"}</p>
      {context.warnings.map((warning) => (
        <p key={warning} className="warning">{warning}</p>
      ))}
    </div>
  );
}
