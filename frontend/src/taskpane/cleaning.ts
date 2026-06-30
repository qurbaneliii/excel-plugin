export type CleaningIssue = {
  row: number;
  column: string;
  originalValue: unknown;
  newValue: unknown;
  reason: string;
};

const BLANK_LIKE = new Set(["", "na", "n/a", "null", "none", "-"]);

function normalizeBlank(value: unknown): unknown {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string" && BLANK_LIKE.has(value.trim().toLowerCase())) {
    return "";
  }
  return value;
}

function trimText(value: unknown): unknown {
  return typeof value === "string" ? value.trim() : value;
}

function convertCurrency(value: unknown): unknown {
  if (typeof value !== "string") {
    return value;
  }
  const stripped = value.replace(/[^\d.\-,]/g, "").replace(/ /g, "").replace(/,/g, "");
  if (!stripped) {
    return value;
  }
  const numeric = Number(stripped);
  return Number.isFinite(numeric) ? numeric : value;
}

function convertNumericText(value: unknown): unknown {
  if (typeof value !== "string") {
    return value;
  }
  const stripped = value.trim().replace(/,/g, "").replace(/ /g, "");
  if (!stripped) {
    return value;
  }
  const numeric = Number(stripped);
  return Number.isFinite(numeric) ? numeric : value;
}

export function applySafeCleaning(values: unknown[][]) {
  if (!values.length) {
    return { cleanedValues: values, issues: [] as CleaningIssue[] };
  }

  const headers = values[0].map((header, index) => String(header || `Column_${index + 1}`));
  const issues: CleaningIssue[] = [];
  const seenRows = new Set<string>();
  const cleanedRows = [values[0]];

  for (let rowIndex = 1; rowIndex < values.length; rowIndex += 1) {
    const row = values[rowIndex];
    const cleanedRow = row.map((cell, columnIndex) => {
      const steps = [normalizeBlank, trimText, convertCurrency, convertNumericText];
      let nextValue = cell;
      for (const step of steps) {
        nextValue = step(nextValue);
      }
      if (JSON.stringify(nextValue) !== JSON.stringify(cell)) {
        issues.push({
          row: rowIndex + 1,
          column: headers[columnIndex],
          originalValue: cell,
          newValue: nextValue,
          reason: "Normalized blank/text/currency/numeric value.",
        });
      }
      return nextValue;
    });

    const rowKey = JSON.stringify(cleanedRow);
    if (seenRows.has(rowKey)) {
      issues.push({
        row: rowIndex + 1,
        column: "*row*",
        originalValue: row,
        newValue: "",
        reason: "Removed exact duplicate row.",
      });
      continue;
    }
    seenRows.add(rowKey);
    cleanedRows.push(cleanedRow);
  }

  return { cleanedValues: cleanedRows, issues };
}
