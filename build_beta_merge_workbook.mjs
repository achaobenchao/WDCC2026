import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = "/tmp/wdcc_beta_merge/beta_merge_data.json";
const outputPath = "/tmp/wdcc_beta_merge/视频文件检索总表_beta汇总版.xlsx";
const data = JSON.parse(await fs.readFile(inputPath, "utf8"));

const headerStyle = { fill: "#1F4E78", font: { name: "Arial", bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
const bodyStyle = { font: { name: "Arial", size: 10 }, verticalAlignment: "center", wrapText: true };
const border = { preset: "all", style: "thin", color: "#D9E2F3" };
const colLetter = (n) => { let s = ""; while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; };
const value = (obj, header) => (obj[header] ?? "");

function addTableSheet(workbook, name, headers, records, tableName, widths) {
  const sheet = workbook.worksheets.add(name);
  const matrix = [headers, ...records.map((record, i) => headers.map((header) => header === "序号" ? i + 1 : value(record, header)))];
  sheet.getRange("A1").write(matrix);
  const lastCol = colLetter(headers.length);
  const lastRow = matrix.length;
  const header = sheet.getRange(`A1:${lastCol}1`);
  header.format = headerStyle;
  header.format.rowHeight = 30;
  const used = sheet.getRange(`A1:${lastCol}${lastRow}`);
  used.format.font = bodyStyle.font;
  used.format.verticalAlignment = "center";
  used.format.wrapText = true;
  used.format.borders = border;
  if (lastRow > 1) sheet.getRange(`A2:${lastCol}${lastRow}`).format.rowHeight = 30;
  widths.forEach((width, idx) => { sheet.getRange(`${colLetter(idx + 1)}:${colLetter(idx + 1)}`).format.columnWidth = width; });
  sheet.freezePanes.freezeRows(1);
  const table = sheet.tables.add(`A1:${lastCol}${lastRow}`, true, tableName);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  return sheet;
}

const wb = Workbook.create();
addTableSheet(wb, "素材总览", data.overview_headers, data.overview, "MaterialsTable",
  [7, 28, 16, 24, 28, 38, 58, 26, 14, 13, 13, 10, 25, 25, 18, 30, 18, 50, 24, 24, 20, 16, 38, 38, 38, 12, 16, 14, 35]);
addTableSheet(wb, "人物索引", data.person_headers, data.persons, "PeopleTable",
  [25, 25, 28, 24, 38, 58, 16, 20, 32, 45, 12, 28, 16]);
addTableSheet(wb, "事件索引", data.event_headers, data.events, "EventsTable",
  [28, 24, 38, 58, 12, 18, 32, 28, 14, 14, 55, 45, 12, 28, 16]);
addTableSheet(wb, "处理质量", data.quality_headers, data.quality, "QualityTable",
  [28, 24, 58, 14, 16, 14, 14, 14, 16, 16, 14, 18, 36, 28, 16]);

const sourceHeaders = ["序号", "源Excel文件名", "完整路径", "包含Sheet", "读取行数", "成功导入行数", "跳过行数", "疑似重复数", "异常说明"];
const sourceRecords = data.sources.map((s, i) => ({
  "序号": i + 1, "源Excel文件名": s.source, "完整路径": s.path, "包含Sheet": s.sheets,
  "读取行数": s.read_rows, "成功导入行数": s.imported_rows, "跳过行数": s.skipped_rows,
  "疑似重复数": i === 0 ? data.duplicates.length : "", "异常说明": s.notes,
}));
addTableSheet(wb, "来源说明", sourceHeaders, sourceRecords, "SourcesTable", [7, 45, 80, 70, 45, 45, 30, 16, 65]);

const duplicateHeaders = ["文件名", "路径A", "来源表A", "来源SheetA", "路径B", "来源表B", "来源SheetB", "差异字段", "是否完全一致", "建议人工检查"];
addTableSheet(wb, "重复检查", duplicateHeaders, data.duplicates, "DuplicatesTable", [28, 65, 30, 18, 65, 30, 18, 55, 16, 35]);

wb.recalculate();
const check = await wb.inspect({kind: "sheet", include: "id,name", maxChars: 2000});
console.log(check.ndjson);
const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(outputPath);
console.log(JSON.stringify({outputPath, sheets: ["素材总览", "人物索引", "事件索引", "处理质量", "来源说明", "重复检查"]}));
