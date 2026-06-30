import type { FormulaExplainResponse, FormulaFixResponse, FormulaGenerateResponse } from "../types";

type Props = {
  generated: FormulaGenerateResponse | null;
  explained: FormulaExplainResponse | null;
  fixed: FormulaFixResponse | null;
};

export function FormulaAssistant({ generated, explained, fixed }: Props) {
  return (
    <div className="panel">
      <h3>Formula Assistant</h3>
      {generated && (
        <>
          <p><strong>Generated:</strong> {generated.formula}</p>
          <p>{generated.explanation}</p>
          {generated.warnings && generated.warnings.length > 0 && <p>{generated.warnings.join(" ")}</p>}
        </>
      )}
      {explained && (
        <>
          <p><strong>Explanation:</strong> {explained.plain_english_explanation}</p>
          <p><strong>Simplified:</strong> {explained.simplified_formula}</p>
          {explained.warnings && explained.warnings.length > 0 && <p>{explained.warnings.join(" ")}</p>}
        </>
      )}
      {fixed && (
        <>
          <p><strong>Fixed:</strong> {fixed.fixed_formula}</p>
          <p>{fixed.what_was_wrong}</p>
          {fixed.warnings && fixed.warnings.length > 0 && <p>{fixed.warnings.join(" ")}</p>}
        </>
      )}
      {!generated && !explained && !fixed && <p>Formula outputs will appear here.</p>}
    </div>
  );
}
