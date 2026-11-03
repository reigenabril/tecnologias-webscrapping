/*
 * metrics.js — lógica pura del dashboard (sin DOM).
 *
 * Se carga como script clásico y expone globalThis.DashboardMetrics para que
 * app.js lo use en el navegador y los tests lo carguen con require() en Node.
 */
(function (global) {
  "use strict";

  function hasText(row) {
    return row.texto != null && String(row.texto).trim() !== "";
  }

  function hasResponse(row) {
    return (
      row.respuesta_dueno != null &&
      String(row.respuesta_dueno).trim() !== ""
    );
  }

  function filterYear(rows, filters) {
    return rows.filter(
      (r) =>
        r.anio_estimado >= filters.yearFrom &&
        r.anio_estimado <= filters.yearTo
    );
  }

  function filterPeriod(rows, filters) {
    return filterYear(rows, filters).filter(
      (r) =>
        filters.sucursal === "Todas las sucursales" ||
        r.sucursal === filters.sucursal
    );
  }

  function filterAll(rows, filters) {
    const categoryFilter = filters.categories.size > 0;
    return filterPeriod(rows, filters).filter((r) => {
      if (!filters.stars.has(r.estrellas)) return false;

      if (filters.response === "Solo con respuesta" && !hasResponse(r)) {
        return false;
      }
      if (filters.response === "Sin respuesta" && hasResponse(r)) {
        return false;
      }

      if (!categoryFilter) return true;
      // Igual que la versión original: las reseñas sin texto siempre entran.
      return filters.categories.has(r.categoria_principal) || r.texto == null;
    });
  }

  function overview(rows) {
    const total = rows.length;
    const withText = rows.filter(hasText).length;
    const withResponse = rows.filter(hasResponse).length;
    const sum = rows.reduce((acc, r) => acc + r.estrellas, 0);
    return {
      total,
      withText,
      withResponse,
      avg: total ? sum / total : 0,
      pctText: total ? (withText / total) * 100 : 0,
      pctResponse: total ? (withResponse / total) * 100 : 0,
    };
  }

  function balance(rows) {
    const total = rows.length;
    const pos = rows.filter((r) => r.estrellas >= 4).length;
    const neg = rows.filter((r) => r.estrellas <= 3).length;
    return {
      total,
      pos,
      neg,
      pctPos: total ? (pos / total) * 100 : 0,
      pctNeg: total ? (neg / total) * 100 : 0,
    };
  }

  function nlp(rows) {
    const total = rows.length;
    const counts = new Map();
    rows.forEach((r) => {
      counts.set(r.categoria_principal, (counts.get(r.categoria_principal) || 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([label, count]) => ({
        label,
        count,
        pct: total ? (count / total) * 100 : 0,
      }))
      .sort((a, b) => a.count - b.count || a.label.localeCompare(b.label, "es"));
  }

  function stars(rows) {
    return [1, 2, 3, 4, 5].map((star) => ({
      stars: star,
      count: rows.filter((r) => r.estrellas === star).length,
    }));
  }

  function sucursalSummary(rows) {
    const map = new Map();
    rows.forEach((r) => {
      if (!map.has(r.sucursal)) {
        map.set(r.sucursal, {
          name: r.sucursal,
          total: 0,
          sum: 0,
          neg: 0,
          resp: 0,
        });
      }
      const item = map.get(r.sucursal);
      item.total += 1;
      item.sum += r.estrellas;
      if (r.estrellas <= 3) item.neg += 1;
      if (hasResponse(r)) item.resp += 1;
    });
    return Array.from(map.values())
      .sort((a, b) => a.name.localeCompare(b.name, "es"))
      .map((item) => ({
        ...item,
        avg: item.total ? item.sum / item.total : 0,
        pctNeg: item.total ? (item.neg / item.total) * 100 : 0,
      }));
  }

  function temporal(rows) {
    const map = new Map();
    rows.forEach((r) => {
      const key = `${r.anio_estimado}|${r.estrellas}`;
      map.set(key, (map.get(key) || 0) + 1);
    });
    return Array.from(map.entries())
      .map(([key, count]) => {
        const [year, star] = key.split("|").map(Number);
        return { year, stars: star, count };
      })
      .sort((a, b) => a.year - b.year || a.stars - b.stars);
  }

  function yearly(rows) {
    const map = new Map();
    rows.forEach((r) => {
      if (!map.has(r.anio_estimado)) {
        map.set(r.anio_estimado, {
          year: r.anio_estimado,
          count: 0,
          sum: 0,
          pos: 0,
        });
      }
      const item = map.get(r.anio_estimado);
      item.count += 1;
      item.sum += r.estrellas;
      if (r.estrellas >= 4) item.pos += 1;
    });
    return Array.from(map.values())
      .sort((a, b) => a.year - b.year)
      .map((item) => ({
        ...item,
        avg: item.count ? item.sum / item.count : 0,
        pctPos: item.count ? (item.pos / item.count) * 100 : 0,
      }));
  }

  function fodaCounts(periodRows) {
    const pos = periodRows.filter((r) => r.estrellas >= 4);
    const neg = periodRows.filter((r) => r.estrellas <= 3);
    const posText = pos.filter(hasText);
    const negText = neg.filter(hasText);
    const countCat = (rows, category) =>
      rows.filter((r) => r.categoria_principal === category).length;

    return {
      pos: pos.length,
      neg: neg.length,
      pctPos: periodRows.length ? (pos.length / periodRows.length) * 100 : 0,
      pctNeg: periodRows.length ? (neg.length / periodRows.length) * 100 : 0,
      posCortes: countCat(posText, "Servicio de Cortes y Taller"),
      posAtencion: countCat(posText, "Atención y Trato del Personal"),
      posPrecios: countCat(posText, "Precios y Presupuestos"),
      negAtencion: countCat(negText, "Atención y Trato del Personal"),
      negEspera: countCat(negText, "Tiempos de Espera y Demoras"),
      negCanales: countCat(
        negText,
        "Canales de Contacto (Teléfono / WhatsApp)"
      ),
      negCortes: countCat(negText, "Servicio de Cortes y Taller"),
      negStock: countCat(negText, "Stock y Disponibilidad"),
      negSinRespuesta: neg.length
        ? (neg.filter((r) => !hasResponse(r)).length / neg.length) * 100
        : 0,
    };
  }

  function search(rows, query) {
    const needle = String(query || "").trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((r) =>
      [r.texto, r.autor, r.respuesta_dueno].some(
        (value) =>
          value != null && String(value).toLowerCase().includes(needle)
      )
    );
  }

  function escapeCsv(value) {
    if (value == null) return "";
    let text = typeof value === "boolean" ? (value ? "True" : "False") : String(value);
    if (/[",\n\r]/.test(text)) {
      text = `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  }

  function toCsv(rows, columns) {
    const header = columns.map(escapeCsv).join(",");
    if (!rows.length) return `\uFEFF${header}\n`;
    const body = rows
      .map((row) => columns.map((col) => escapeCsv(row[col])).join(","))
      .join("\n");
    return `\uFEFF${header}\n${body}\n`;
  }

  global.DashboardMetrics = {
    hasText,
    hasResponse,
    filterYear,
    filterPeriod,
    filterAll,
    overview,
    balance,
    nlp,
    stars,
    sucursalSummary,
    temporal,
    yearly,
    fodaCounts,
    search,
    toCsv,
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
