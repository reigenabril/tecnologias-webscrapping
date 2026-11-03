/*
 * Tests de paridad numérica del dashboard (totales, filtros, FODA y CSV).
 * Ejecutar con: node --test tests/metrics.test.js
 */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const data = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "..", "docs", "data", "resenas.json"),
    "utf8"
  )
);
require("../docs/assets/metrics.js");
const M = globalThis.DashboardMetrics;

const rows = data.rows;
const allCategories = Array.from(
  new Set(rows.map((r) => r.categoria_principal))
).sort((a, b) => a.localeCompare(b, "es"));

const defaults = {
  sucursal: "Todas las sucursales",
  yearFrom: 2016,
  yearTo: 2026,
  stars: new Set([1, 2, 3, 4, 5]),
  categories: new Set(allCategories),
  response: "Todas",
};

function round(value, digits) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

test("payload: 1075 filas y 17 columnas", () => {
  assert.equal(data.meta.count, 1075);
  assert.equal(rows.length, 1075);
  assert.equal(data.columns.length, 17);
});

test("default: métricas de la sección 2", () => {
  const o = M.overview(M.filterAll(rows, defaults));
  assert.equal(o.total, 1075);
  assert.equal(o.withText, 608);
  assert.equal(o.withResponse, 307);
  assert.equal(round(o.avg, 2), 4.07);
  assert.equal(round(o.pctText, 1), 56.6);
  assert.equal(round(o.pctResponse, 1), 28.6);
});

test("default: balance positivas vs críticas", () => {
  const b = M.balance(M.filterPeriod(rows, defaults));
  assert.equal(b.pos, 817);
  assert.equal(b.neg, 258);
  assert.equal(round(b.pctPos, 1), 76.0);
  assert.equal(round(b.pctNeg, 1), 24.0);
});

test("2024-2026: métricas y balance", () => {
  const filters = { ...defaults, yearFrom: 2024, yearTo: 2026 };
  const o = M.overview(M.filterAll(rows, filters));
  const b = M.balance(M.filterPeriod(rows, filters));
  assert.equal(o.total, 296);
  assert.equal(o.withText, 212);
  assert.equal(o.withResponse, 215);
  assert.equal(round(o.avg, 3), 4.345);
  assert.equal(b.pos, 247);
  assert.equal(b.neg, 49);
  assert.equal(round(b.pctPos, 1), 83.4);
});

test("EGGER HAUS: métricas y balance", () => {
  const filters = { ...defaults, sucursal: "EGGER HAUS (Av. 44)" };
  const o = M.overview(M.filterAll(rows, filters));
  const b = M.balance(M.filterPeriod(rows, filters));
  assert.equal(o.total, 328);
  assert.equal(round(o.avg, 3), 4.226);
  assert.equal(b.neg, 59);
  assert.equal(o.withResponse, 93);
});

test("filtro de categoría conserva filas sin texto (OR de la versión original)", () => {
  const filters = {
    ...defaults,
    categories: new Set(["Atención y Trato del Personal"]),
  };
  const filtered = M.filterAll(rows, filters);
  const withText = filtered.filter(M.hasText);
  assert.equal(filtered.length, 850);
  assert.equal(withText.length, 383);
  assert.equal(round(M.overview(filtered).avg, 2), 4.16);
});

test("sin categorías seleccionadas no filtra (paridad)", () => {
  const filters = { ...defaults, categories: new Set() };
  assert.equal(M.filterAll(rows, filters).length, 1075);
});

test("2017 sin datos: agregados en cero, sin NaN", () => {
  const filters = { ...defaults, yearFrom: 2017, yearTo: 2017 };
  const filtered = M.filterAll(rows, filters);
  const period = M.filterPeriod(rows, filters);
  const o = M.overview(filtered);
  const b = M.balance(period);
  assert.equal(o.total, 0);
  assert.equal(o.withText, 0);
  assert.equal(o.withResponse, 0);
  assert.equal(o.avg, 0);
  assert.equal(o.pctText, 0);
  assert.equal(o.pctResponse, 0);
  assert.equal(b.pos, 0);
  assert.equal(b.neg, 0);
  assert.equal(b.pctPos, 0);
  assert.deepEqual(M.nlp(filtered), []);
  assert.deepEqual(M.temporal(filtered), []);
  assert.equal(
    M.stars(filtered).reduce((acc, s) => acc + s.count, 0),
    0
  );
  assert.equal(M.fodaCounts(period).negSinRespuesta, 0);
});

test("resumen por sucursal (solo filtro de año)", () => {
  const summary = M.sucursalSummary(M.filterYear(rows, defaults));
  assert.equal(summary.length, 3);
  const casa = summary.find((s) => s.name === "Casa Central (Calle 31)");
  assert.equal(casa.total, 719);
  assert.equal(round(casa.avg, 2), 3.96);
  assert.equal(casa.neg, 197);
  assert.equal(casa.resp, 188);
});

test("temporal: suma total y años", () => {
  const points = M.temporal(M.filterAll(rows, defaults));
  assert.equal(
    points.reduce((acc, p) => acc + p.count, 0),
    1075
  );
  assert.equal(new Set(points.map((p) => p.year)).size, 10);
});

test("yearly: volumen y promedio por año", () => {
  const points = M.yearly(M.filterAll(rows, defaults));
  assert.equal(points.length, 10);
  assert.equal(
    points.reduce((acc, p) => acc + p.count, 0),
    1075
  );
  const y2019 = points.find((p) => p.year === 2019);
  assert.equal(y2019.count, 319);
  assert.equal(round(y2019.avg, 2), 3.92);
  assert.equal(round(y2019.pctPos, 1), 72.4);
  const y2024 = points.find((p) => p.year === 2024);
  assert.equal(y2024.count, 94);
  assert.equal(round(y2024.avg, 2), 4.49);
  assert.equal(round(y2024.pctPos, 1), 87.2);
  assert.equal(points.find((p) => p.year === 2026).count, 164);
  assert.equal(points.find((p) => p.year === 2017), undefined);
  assert.deepEqual(M.yearly([]), []);
});

test("FODA: conteos del período por defecto", () => {
  const f = M.fodaCounts(M.filterPeriod(rows, defaults));
  assert.equal(f.pos, 817);
  assert.equal(f.neg, 258);
  assert.equal(f.posAtencion, 293);
  assert.equal(f.posCortes, 22);
  assert.equal(f.negAtencion, 90);
  assert.equal(f.negEspera, 32);
  assert.equal(f.negCanales, 11);
  assert.equal(f.negCortes, 6);
  assert.equal(f.negStock, 3);
  assert.equal(round(f.negSinRespuesta, 1), 70.9);
});

test("búsqueda literal e insensible a mayúsculas", () => {
  const hits = M.search(rows, "corte");
  assert.ok(hits.length > 0);
  assert.equal(M.search(rows, "CORTE").length, hits.length);
  assert.ok(M.search(rows, "(").length > 0);
  assert.equal(M.search(rows, "").length, 1075);
  assert.equal(M.search(rows, "zzzz-no-existe").length, 0);
});

test("CSV: BOM, encabezado, nulos, booleanos y quoting", () => {
  const cols = ["a", "b", "c", "d"];
  const rowsCsv = [{ a: "x,y", b: null, c: true, d: 'he said "hi"' }];
  assert.equal(
    M.toCsv(rowsCsv, cols),
    '\uFEFFa,b,c,d\n"x,y",,True,"he said ""hi"""\n'
  );
  assert.equal(M.toCsv([], cols), "\uFEFFa,b,c,d\n");
});

test("CSV real: encabezado completo y filas filtradas", () => {
  const filtered = M.filterAll(rows, defaults).slice(0, 10);
  const csv = M.toCsv(filtered, data.columns);
  assert.ok(csv.startsWith("\uFEFFid_resena,sucursal,autor,estrellas,"));
  assert.ok(csv.includes('"cat_Calidad, Entregas y Flete"'));
  assert.ok(csv.endsWith("\n"));
  filtered.forEach((r) => assert.ok(csv.includes(r.id_resena)));
});
