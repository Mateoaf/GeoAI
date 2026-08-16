import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(import.meta.dirname, "..");
const inputPath = path.join(
  projectRoot,
  "data",
  "raw",
  "oxrep-mines-3.0-20250408.xlsx",
);
const auditDir = path.join(projectRoot, "reports", "audit");
const renderDir = path.join(auditDir, "workbook_renders");

await fs.mkdir(renderDir, { recursive: true });

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const inspection = await workbook.inspect({
  kind: "workbook,sheet,table,definedName,drawing",
  include: "id,name,range,values,formulas",
  maxChars: 50000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 120,
});
await fs.writeFile(
  path.join(auditDir, "artifact_workbook_inspection.ndjson"),
  inspection.ndjson,
  "utf8",
);

const renderJobs = [
  { sheet: "OxREP Mines 3 0 - 20250408", range: "A1:P35" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "Q1:AF35" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "AG1:AU35" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "A683:P718" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "Q683:AF718" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "AG683:AU718" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "A1365:P1400" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "Q1365:AF1400" },
  { sheet: "OxREP Mines 3 0 - 20250408", range: "AG1365:AU1400" },
  { sheet: "Sheet1", range: "A1:C10" },
];

const rendered = [];
for (const job of renderJobs) {
  const safeName = `${job.sheet}_${job.range}`.replaceAll(
    /[^A-Za-z0-9._-]+/g,
    "_",
  );
  const preview = await workbook.render({
    sheetName: job.sheet,
    range: job.range,
    scale: 1,
    format: "png",
  });
  const outputPath = path.join(renderDir, `${safeName}.png`);
  await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
  rendered.push({ ...job, outputPath });
}

console.log(JSON.stringify({ inputPath, rendered }, null, 2));
