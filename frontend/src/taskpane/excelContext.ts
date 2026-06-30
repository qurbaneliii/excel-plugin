import type { RangeContext } from "./types";

const MAX_SAMPLE_ROWS = 10;
const LARGE_RANGE_WARNING_THRESHOLD = 5000;
export const MAX_CELLS_FOR_FULL_APPLY = 10000;

function normalizeValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value).trim();
}

function typeHint(values: unknown[]): RangeContext["metadata"][string]["typeHint"] {
  const nonBlank = values.map(normalizeValue).filter(Boolean);
  if (nonBlank.length === 0) {
    return "empty";
  }
  const matches = {
    number: 0,
    currency: 0,
    date: 0,
    formula: 0,
    text: 0,
  };
  for (const raw of values) {
    const value = normalizeValue(raw);
    if (!value) {
      continue;
    }
    if (value.startsWith("=")) {
      matches.formula += 1;
    } else if (/^\s*(?:AZN|₼)?\s*[-+]?\d[\d,\s]*(?:\.\d+)?\s*(?:AZN|₼)?\s*$/i.test(value)) {
      matches.currency += 1;
    } else if (/^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}$/.test(value)) {
      matches.date += 1;
    } else if (!Number.isNaN(Number(value.replace(/,/g, "").replace(/ /g, "")))) {
      matches.number += 1;
    } else {
      matches.text += 1;
    }
  }
  const entries = Object.entries(matches).sort((a, b) => b[1] - a[1]);
  if (entries.length > 1 && entries[0][1] > 0 && entries[1][1] > 0) {
    const topTwo = entries[0][1] + entries[1][1];
    if (topTwo >= nonBlank.length && entries[1][1] / nonBlank.length > 0.25) {
      return "mixed";
    }
  }
  switch (entries[0][0]) {
    case "number":
      return "number";
    case "currency":
      return "currency-like";
    case "date":
      return "date-like";
    case "formula":
      return "formula-like";
    case "text":
      return "text";
    default:
      return "mixed";
  }
}

function buildMetadata(headers: string[], rows: unknown[][]) {
  const metadata: RangeContext["metadata"] = {};
  headers.forEach((header, index) => {
    const values = rows.map((row) => row[index]);
    metadata[header] = {
      emptyCount: values.filter((value) => {
        const text = normalizeValue(value).toLowerCase();
        return ["", "na", "n/a", "null", "none", "-"].includes(text);
      }).length,
      typeHint: typeHint(values),
      distinctSampleValues: [...new Set(values.map(normalizeValue).filter(Boolean))].slice(0, 5),
    };
  });
  return metadata;
}

export async function getSelectedRangeContext(): Promise<RangeContext> {
  return Excel.run(async (context) => {
    const range = context.workbook.getSelectedRange();
    range.load(["address", "values", "rowCount", "columnCount", "worksheet/name"]);
    await context.sync();

    const values = (range.values || []) as unknown[][];
    const headers = (values[0] || []).map((value, index) => normalizeValue(value) || `Column_${index + 1}`);
    const sampleRows = values.slice(1, 1 + MAX_SAMPLE_ROWS);
    const warnings: string[] = [];
    const totalCells = range.rowCount * range.columnCount;
    if (totalCells > LARGE_RANGE_WARNING_THRESHOLD) {
      warnings.push(`Large selection detected (${totalCells} cells). Only sampled rows are sent to the backend.`);
    }

    return {
      worksheetName: range.worksheet.name,
      rangeAddress: range.address,
      rowCount: range.rowCount,
      columnCount: range.columnCount,
      valuesPreview: values.slice(0, Math.min(values.length, MAX_SAMPLE_ROWS + 1)),
      headers,
      sampleRows,
      metadata: buildMetadata(headers, sampleRows),
      warnings,
    };
  });
}

export async function getSelectedFormulaContext(): Promise<{ formula: string; address: string; worksheetName: string }> {
  return Excel.run(async (context) => {
    const range = context.workbook.getSelectedRange();
    range.load(["address", "formulas", "rowCount", "columnCount", "worksheet/name"]);
    await context.sync();

    if (range.rowCount !== 1 || range.columnCount !== 1) {
      throw new Error("Select a single cell to inspect a formula.");
    }

    const formula = String(range.formulas?.[0]?.[0] ?? "");
    return {
      formula,
      address: range.address,
      worksheetName: range.worksheet.name,
    };
  });
}

export async function getFullSelectedRangeValuesForApply(): Promise<{ worksheetName: string; values: unknown[][]; address: string }> {
  return Excel.run(async (context) => {
    const range = context.workbook.getSelectedRange();
    range.load(["address", "values", "rowCount", "columnCount", "worksheet/name"]);
    await context.sync();

    const totalCells = range.rowCount * range.columnCount;
    if (totalCells > MAX_CELLS_FOR_FULL_APPLY) {
      throw new Error(`Selection exceeds safe apply limit of ${MAX_CELLS_FOR_FULL_APPLY} cells.`);
    }

    return {
      worksheetName: range.worksheet.name,
      values: (range.values || []) as unknown[][],
      address: range.address,
    };
  });
}
