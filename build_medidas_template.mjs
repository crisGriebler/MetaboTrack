import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/modelo-medidas";
await fs.mkdir(outputDir, { recursive: true });

const wb = Workbook.create();
const medidas = wb.worksheets.add("Medidas");
const instrucoes = wb.worksheets.add("Instruções");

for (const sheet of [medidas, instrucoes]) {
  sheet.showGridLines = false;
}

medidas.getRange("A2").values = [["Registro de medidas corporais"]];
medidas.getRange("A2:N2").format = {
  font: { name: "Arial", size: 14, bold: true, color: "#1F2937" },
  verticalAlignment: "center"
};
medidas.getRange("A3").values = [["Uma linha representa uma avaliação. Registre apenas medidas que tenham sido coletadas."]];
medidas.getRange("A3:N3").format = {
  font: { name: "Arial", size: 10, italic: true, color: "#4B5563" }
};

const headers = [[
  "Data", "Peso (kg)", "Cintura (cm)", "Abdômen (cm)", "Quadril (cm)", "Busto (cm)",
  "Braço direito (cm)", "Braço esquerdo (cm)", "Coxa direita (cm)", "Coxa esquerda (cm)",
  "Panturrilha direita (cm)", "Panturrilha esquerda (cm)", "Observações"
]];
medidas.getRange("A5:M5").values = headers;

const entryRange = medidas.getRange("A5:M506");
entryRange.format.font = { name: "Arial", size: 10, color: "#1F2937" };
medidas.getRange("A5:M5").format = {
  fill: "#E5E7EB",
  font: { name: "Arial", size: 10, bold: true, color: "#111827" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#D1D5DB" }
};
medidas.getRange("A6:A506").format.numberFormat = "dd/mm/yyyy";
medidas.getRange("B6:L506").format.numberFormat = "0.0";
medidas.getRange("A5:M506").format.verticalAlignment = "center";
medidas.getRange("A5:M506").format.borders = { preset: "outside", style: "thin", color: "#E5E7EB" };
medidas.getRange("M6:M506").format.wrapText = true;
medidas.getRange("A5:M506").format.rowHeight = 20;
medidas.getRange("A5:M5").format.rowHeight = 34;
medidas.getRange("A:A").format.columnWidth = 13;
medidas.getRange("B:L").format.columnWidth = 16;
medidas.getRange("M:M").format.columnWidth = 38;
medidas.freezePanes.freezeRows(5);
medidas.freezePanes.freezeColumns(1);

instrucoes.getRange("A2").values = [["Como preencher e importar"]];
instrucoes.getRange("A2:B2").format = {
  font: { name: "Arial", size: 14, bold: true, color: "#1F2937" },
  verticalAlignment: "center"
};
instrucoes.getRange("A4:B4").values = [["Regra", "Orientação"]];
instrucoes.getRange("A5:B12").values = [
  ["Formato", "Preencha a aba Medidas. Cada linha representa uma data de avaliação."],
  ["Campo obrigatório", "Informe a data e pelo menos uma medida."],
  ["Unidades", "Peso em kg. Todas as circunferências em cm."],
  ["Campos vazios", "Deixe vazio quando a medida não tiver sido coletada. Não use zero como ausência de dado."],
  ["Decimais", "Use números com casas decimais quando necessário. Exemplo: 82,5 kg ou 82.5 kg."],
  ["Cintura e abdômen", "Registre como campos distintos, seguindo sempre o mesmo procedimento de medição."],
  ["Duplicidades", "Evite mais de uma linha para a mesma data, salvo se houver uma observação que justifique nova avaliação."],
  ["Importação", "A aba Medidas é o modelo padrão para importação pelo MetaboTrack."]
];
instrucoes.getRange("A4:B4").format = {
  fill: "#E5E7EB",
  font: { name: "Arial", size: 10, bold: true, color: "#111827" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#D1D5DB" }
};
instrucoes.getRange("A5:A12").format = { font: { name: "Arial", size: 10, bold: true, color: "#1F2937" } };
instrucoes.getRange("A5:B12").format = {
  font: { name: "Arial", size: 10, color: "#1F2937" },
  verticalAlignment: "top",
  wrapText: true,
  borders: { preset: "all", style: "thin", color: "#E5E7EB" }
};
instrucoes.getRange("A:A").format.columnWidth = 21;
instrucoes.getRange("B:B").format.columnWidth = 80;
instrucoes.getRange("A4:B12").format.autofitRows();

wb.recalculate();
const measuresPreview = await wb.render({ sheetName: "Medidas", range: "A1:N12", scale: 1.25, format: "png" });
await fs.writeFile(`${outputDir}/medidas-preview.png`, new Uint8Array(await measuresPreview.arrayBuffer()));
const instructionsPreview = await wb.render({ sheetName: "Instruções", range: "A1:B13", scale: 1.25, format: "png" });
await fs.writeFile(`${outputDir}/instrucoes-preview.png`, new Uint8Array(await instructionsPreview.arrayBuffer()));

const inspection = await wb.inspect({ kind: "table", range: "Medidas!A1:M8", include: "values,formulas", tableMaxRows: 8, tableMaxCols: 13 });
console.log(inspection.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 50 }, summary: "scan final de erros" });
console.log(errors.ndjson);

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${outputDir}/Modelo_de_medidas_MetaboTrack.xlsx`);
