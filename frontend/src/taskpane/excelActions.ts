import type { CleaningIssue } from "./cleaning";

export function safeWorksheetName(prefix: string, originalName: string): string {
  const sanitized = `${prefix}_${originalName}`.replace(/[\\\/\?\*\[\]:]/g, "_");
  return sanitized.slice(0, 31);
}

async function ensureUniqueWorksheetNameInContext(context: Excel.RequestContext, name: string): Promise<string> {
  const worksheets = context.workbook.worksheets;
  worksheets.load("items/name");
  await context.sync();

  const existing = new Set(worksheets.items.map((sheet) => sheet.name));
  if (!existing.has(name)) {
    return name;
  }
  let candidate = name;
  let index = 2;
  while (existing.has(candidate)) {
    candidate = `${name.slice(0, Math.max(0, 28))}_${index}`.slice(0, 31);
    index += 1;
  }
  return candidate;
}

export async function ensureUniqueWorksheetName(name: string): Promise<string> {
  return Excel.run(async (context) => {
    return ensureUniqueWorksheetNameInContext(context, name);
  });
}

export async function insertFormulaIntoSelectedCell(formula: string): Promise<void> {
  return Excel.run(async (context) => {
    const range = context.workbook.getSelectedRange();
    range.load(["rowCount", "columnCount"]);
    await context.sync();

    if (range.rowCount !== 1 || range.columnCount !== 1) {
      throw new Error("Select a single cell before inserting a formula.");
    }

    range.formulas = [[formula]];
    await context.sync();
  });
}

export async function writeCleanedDataToNewSheet(originalSheetName: string, cleanedValues: unknown[][], issues: CleaningIssue[]): Promise<void> {
  return Excel.run(async (context) => {
    const cleanedName = await ensureUniqueWorksheetNameInContext(context, safeWorksheetName("AI_Cleaned", originalSheetName));
    const cleanedSheet = context.workbook.worksheets.add(cleanedName);
    const cleanedRange = cleanedSheet.getRangeByIndexes(0, 0, cleanedValues.length, cleanedValues[0]?.length || 1);
    cleanedRange.values = cleanedValues as (string | number | boolean)[][];
    cleanedRange.format.autofitColumns();
    cleanedRange.format.autofitRows();

    if (issues.length > 0) {
      const issuesName = await ensureUniqueWorksheetNameInContext(context, safeWorksheetName("AI_Issues", originalSheetName));
      const issuesSheet = context.workbook.worksheets.add(issuesName);
      const table = [
        ["Row", "Column", "Original Value", "New Value", "Reason"],
        ...issues.map((issue) => [issue.row, issue.column, String(issue.originalValue ?? ""), String(issue.newValue ?? ""), issue.reason]),
      ];
      const issuesRange = issuesSheet.getRangeByIndexes(0, 0, table.length, table[0].length);
      issuesRange.values = table;
      issuesRange.format.autofitColumns();
    }

    await context.sync();
  });
}

export async function writeReportToNewSheet(originalSheetName: string, report: {
  title: string;
  executive_summary: string;
  key_findings: string[];
  data_quality_notes: string[];
  suggested_charts: string[];
  recommended_next_actions: string[];
}): Promise<void> {
  return Excel.run(async (context) => {
    const sheetName = await ensureUniqueWorksheetNameInContext(context, safeWorksheetName("AI_Report", originalSheetName));
    const sheet = context.workbook.worksheets.add(sheetName);
    const rows = [
      [report.title],
      ["Executive Summary", report.executive_summary],
      ["Key Findings", report.key_findings.join("\n")],
      ["Data Quality Notes", report.data_quality_notes.join("\n")],
      ["Suggested Charts", report.suggested_charts.join("\n")],
      ["Recommended Next Actions", report.recommended_next_actions.join("\n")],
    ];
    const range = sheet.getRangeByIndexes(0, 0, rows.length, 2);
    range.values = rows;
    range.format.autofitColumns();
    range.getCell(0, 0).format.font.bold = true;
    await context.sync();
  });
}

export async function createBasicSummarySheet(originalSheetName: string, values: unknown[][]): Promise<void> {
  if (values.length < 2) {
    throw new Error("Select a table with headers and data rows.");
  }

  const headers = values[0].map((value, index) => String(value || `Column_${index + 1}`));
  const rows = values.slice(1);
  const categoryIndex = headers.findIndex((_, index) =>
    rows.some((row) => typeof row[index] === "string" && String(row[index]).trim() !== "")
  );
  const numericIndex = headers.findIndex((_, index) =>
    rows.some((row) => Number.isFinite(Number(String(row[index] ?? "").replace(/,/g, "").replace(/ /g, ""))))
  );

  if (categoryIndex === -1 || numericIndex === -1) {
    throw new Error("Could not find a usable category-like and numeric-like column for summary creation.");
  }

  const grouped = new Map<string, { total: number; count: number }>();
  for (const row of rows) {
    const key = String(row[categoryIndex] ?? "").trim() || "(blank)";
    const numeric = Number(String(row[numericIndex] ?? "").replace(/,/g, "").replace(/ /g, ""));
    const current = grouped.get(key) ?? { total: 0, count: 0 };
    current.total += Number.isFinite(numeric) ? numeric : 0;
    current.count += 1;
    grouped.set(key, current);
  }

  return Excel.run(async (context) => {
    const sheetName = await ensureUniqueWorksheetNameInContext(context, safeWorksheetName("AI_Summary", originalSheetName));
    const sheet = context.workbook.worksheets.add(sheetName);
    const summaryRows: (string | number)[][] = [
      [headers[categoryIndex], "Count", `Total ${headers[numericIndex]}`],
      ...Array.from(grouped.entries()).map(([key, value]) => [key, value.count, value.total]),
    ];
    const range = sheet.getRangeByIndexes(0, 0, summaryRows.length, summaryRows[0].length);
    range.values = summaryRows;
    range.format.autofitColumns();
    await context.sync();
  });
}
