import type { ActionPlanResponse } from "../types";

export function ActionPlanPreview({ result }: { result: ActionPlanResponse | null }) {
  if (!result) {
    return <div className="panel">Cleaning plan will appear here.</div>;
  }

  return (
    <div className="panel">
      <h3>Cleaning Plan</h3>
      <p>{result.plan_summary}</p>
      <ul>
        {result.actions.map((action) => (
          <li key={action.id}>{action.type}: {action.description}</li>
        ))}
      </ul>
      {result.blocked_actions.length > 0 && (
        <ul>
          {result.blocked_actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      )}
      {result.warnings && result.warnings.length > 0 && (
        <ul>
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
