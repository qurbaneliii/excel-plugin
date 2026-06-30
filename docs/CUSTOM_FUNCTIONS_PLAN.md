# Custom Functions Plan

Custom functions are intentionally deferred to protect the working task-pane MVP.

## Candidate Functions

- `AI.CLEAN_TEXT`
- `AI.SUMMARIZE_TEXT`
- `AI.CLASSIFY`

## Why Deferred

- Office custom functions add scaffold and manifest complexity
- They are not required for the core task-pane workflow
- The current priority is stable task-pane analysis, formula help, cleaning, and reporting

## Safe Next Steps

1. Add a `functions/` scaffold and custom-functions manifest wiring
2. Keep all LLM requests backend-only
3. Restrict custom functions to pure return values with no workbook mutation
4. Start with `AI.CLEAN_TEXT` because it can have a deterministic fallback
