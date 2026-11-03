/*
 * app.js — dashboard interactivo (DOM, router, filtros, gráficos).
 * Depende de: metrics.js (globalThis.DashboardMetrics) y Plotly.js.
 */
(function () {
  "use strict";

  const M = window.DashboardMetrics;
  const PAGE_SIZE = 50;
  const ALL_SUCURSALES = "Todas las sucursales";
  const ROUTES = [
    "diagnostico",
    "evidencia",
    "procesos",
    "foda",
    "resenas",
    "hoja-de-ruta",
  ];
  const ROUTE_TITLES = {
    diagnostico: "Diagnóstico Digital",
    evidencia: "Evidencia Empírica",
    procesos: "Procesos AS-IS",
    foda: "Matriz FODA",
    resenas: "Explorador de Reseñas",
    "hoja-de-ruta": "Hoja de Ruta",
  };
  const STAR_COLORS = {
    1: "#0072B2",
    2: "#E69F00",
    3: "#94A3B8",
    4: "#56B4E9",
    5: "#009E73",
  };
  const PALETTE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#64748B",
    "#94A3B8",
    "#CBD5E1",
    "#E2E8F0",
  ];
  const SHORT_SUCURSAL = {
    "Casa Central (Calle 31)": "Casa Central",
    "EGGER HAUS (Av. 44)": "EGGER HAUS",
    "Sucursal Centenario (Cno. Centenario)": "Centenario",
  };
  const BASE_LAYOUT = {
    font: { family: "Inter, system-ui, sans-serif", size: 11, color: "#334155" },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    hoverlabel: {
      font: { family: "Inter, system-ui, sans-serif", size: 11 },
      bgcolor: "#ffffff",
      bordercolor: "#E2E8F0",
    },
  };

  const state = {
    sucursal: ALL_SUCURSALES,
    yearFrom: null,
    yearTo: null,
    stars: new Set([1, 2, 3, 4, 5]),
    categories: new Set(),
    response: "Todas",
    search: "",
    page: 1,
  };

  let payload = null;
  let years = [];
  let categories = [];
  let sucursales = [];
  let cache = {};
  let currentRoute = "diagnostico";
  let selectedEvidenceTab = 0;
  let lastFocused = null;
  let closeNav = function () {};

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const one = (n) => `${Number(n).toFixed(1)}%`;
  const two = (n) => Number(n).toFixed(2);
  const fmtInt = (n) => Number(n).toLocaleString("es-AR");

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    if (!M) {
      showFatal(new Error("No se pudo cargar metrics.js"));
      return;
    }

    setupMobileNav();
    setupTabs();
    window.addEventListener("hashchange", () => showRoute(routeFromHash()));

    fetch("./data/resenas.json", { cache: "no-cache" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => {
        validate(data);
        payload = data;
        hydrateControls();
        bindControls();
        refresh();
        showRoute(routeFromHash());
      })
      .catch(showFatal);
  }

  /* ---------------- Datos y controles ---------------- */

  function validate(data) {
    if (!data || !Array.isArray(data.rows) || !Array.isArray(data.columns)) {
      throw new Error("El JSON de datos no tiene el formato esperado.");
    }
    if (!data.rows.length) throw new Error("El JSON de datos está vacío.");
    if (data.meta && data.meta.count !== data.rows.length) {
      throw new Error("El conteo del JSON no coincide con las filas.");
    }
  }

  function hydrateControls() {
    const rows = payload.rows;
    sucursales = Array.from(new Set(rows.map((r) => r.sucursal))).sort((a, b) =>
      a.localeCompare(b, "es")
    );
    categories = Array.from(
      new Set(rows.map((r) => r.categoria_principal))
    ).sort((a, b) => a.localeCompare(b, "es"));

    const minYear = Math.min(...rows.map((r) => r.anio_estimado));
    const maxYear = Math.max(...rows.map((r) => r.anio_estimado));
    years = [];
    for (let year = minYear; year <= maxYear; year += 1) years.push(year);

    state.yearFrom = minYear;
    state.yearTo = maxYear;
    state.categories = new Set(categories);

    const selectSucursal = $("#f-sucursal");
    [ALL_SUCURSALES, ...sucursales].forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      selectSucursal.appendChild(option);
    });

    [["#f-year-from", state.yearFrom], ["#f-year-to", state.yearTo]].forEach(
      ([selector, value]) => {
        const select = $(selector);
        years.forEach((year) => {
          const option = document.createElement("option");
          option.value = String(year);
          option.textContent = String(year);
          select.appendChild(option);
        });
        select.value = String(value);
      }
    );

    const categoriesBox = $("#f-cats");
    categories.forEach((category) => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = category;
      input.checked = true;
      const text = document.createElement("span");
      text.textContent = category;
      label.append(input, text);
      categoriesBox.appendChild(label);
    });
  }

  function bindControls() {
    $("#f-sucursal").addEventListener("change", (event) => {
      state.sucursal = event.target.value;
      refresh();
    });

    $("#f-year-from").addEventListener("change", (event) => {
      state.yearFrom = Number(event.target.value);
      if (state.yearFrom > state.yearTo) {
        state.yearTo = state.yearFrom;
        $("#f-year-to").value = String(state.yearTo);
      }
      refresh();
    });

    $("#f-year-to").addEventListener("change", (event) => {
      state.yearTo = Number(event.target.value);
      if (state.yearTo < state.yearFrom) {
        state.yearFrom = state.yearTo;
        $("#f-year-from").value = String(state.yearFrom);
      }
      refresh();
    });

    $("#f-stars").addEventListener("change", () => {
      state.stars = new Set(
        $$("#f-stars input:checked").map((input) => Number(input.value))
      );
      refresh();
    });

    $("#f-cats").addEventListener("change", () => {
      state.categories = new Set(
        $$("#f-cats input:checked").map((input) => input.value)
      );
      refresh();
    });

    $("#cats-all").addEventListener("click", () => setAllCategories(true));
    $("#cats-none").addEventListener("click", () => setAllCategories(false));

    $$('input[name="f-response"]').forEach((radio) => {
      radio.addEventListener("change", (event) => {
        state.response = event.target.value;
        refresh();
      });
    });

    $("#f-reset").addEventListener("click", () => {
      state.sucursal = ALL_SUCURSALES;
      state.yearFrom = years[0];
      state.yearTo = years[years.length - 1];
      state.stars = new Set([1, 2, 3, 4, 5]);
      state.categories = new Set(categories);
      state.response = "Todas";
      state.search = "";
      $("#review-search").value = "";
      syncControls();
      refresh();
    });

    let debounce;
    $("#review-search").addEventListener("input", (event) => {
      clearTimeout(debounce);
      const value = event.target.value;
      debounce = setTimeout(() => {
        state.search = value;
        state.page = 1;
        updateExplorer();
      }, 150);
    });

    $("#review-more").addEventListener("click", () => {
      state.page += 1;
      updateExplorer();
    });

    $("#download-csv").addEventListener("click", downloadCsv);
  }

  function setAllCategories(checked) {
    $$("#f-cats input").forEach((input) => {
      input.checked = checked;
    });
    state.categories = checked ? new Set(categories) : new Set();
    refresh();
  }

  function syncControls() {
    $("#f-sucursal").value = state.sucursal;
    $("#f-year-from").value = String(state.yearFrom);
    $("#f-year-to").value = String(state.yearTo);
    $$("#f-stars input").forEach((input) => {
      input.checked = state.stars.has(Number(input.value));
    });
    $$("#f-cats input").forEach((input) => {
      input.checked = state.categories.has(input.value);
    });
    $$('input[name="f-response"]').forEach((radio) => {
      radio.checked = radio.value === state.response;
    });
  }

  /* ---------------- Filtros y render ---------------- */

  function refresh() {
    state.page = 1;
    const rows = payload.rows;
    const period = M.filterPeriod(rows, state);
    const filtered = M.filterAll(rows, state);
    const filteredText = filtered.filter(M.hasText);
    const yearRows = M.filterYear(rows, state);

    cache = {
      period,
      filtered,
      filteredText,
      yearRows,
      overview: M.overview(filtered),
      balance: M.balance(period),
      nlp: M.nlp(filteredText),
      stars: M.stars(filtered),
      sucursal: M.sucursalSummary(yearRows),
      temporal: M.temporal(filtered),
      foda: M.fodaCounts(period),
    };

    $("#cats-hint").hidden = state.categories.size !== 0;
    $("#stars-hint").hidden = state.stars.size !== 0;

    updateEvidence();
    updateExplorer();

    if (currentRoute === "evidencia") {
      plotEvidenceTab(selectedEvidenceTab);
    }
  }

  function setBindings() {
    const o = cache.overview;
    const f = cache.foda;
    const values = {
      range: `${state.yearFrom} - ${state.yearTo}`,
      sucursal: state.sucursal,
      "period-total": fmtInt(cache.period.length),
      total: fmtInt(o.total),
      "with-text": fmtInt(o.withText),
      "pct-text": one(o.pctText),
      avg: two(o.avg),
      "with-response": fmtInt(o.withResponse),
      "pct-response": one(o.pctResponse),
      "tab-pos": fmtInt(f.pos),
      "tab-neg": fmtInt(f.neg),
      "foda-pos": fmtInt(f.pos),
      "foda-neg": fmtInt(f.neg),
      "foda-pct-pos": one(f.pctPos),
      "foda-pct-neg": one(f.pctNeg),
      "foda-pos-cortes": fmtInt(f.posCortes),
      "foda-pos-atencion": fmtInt(f.posAtencion),
      "foda-pos-precios": fmtInt(f.posPrecios),
      "foda-neg-atencion": fmtInt(f.negAtencion),
      "foda-neg-espera": fmtInt(f.negEspera),
      "foda-neg-canales": fmtInt(f.negCanales),
      "foda-neg-cortes": fmtInt(f.negCortes),
      "foda-neg-stock": fmtInt(f.negStock),
      "foda-neg-sinrespuesta": one(f.negSinRespuesta),
      "suc-total": fmtInt(cache.yearRows.length),
    };

    $$("[data-bind]").forEach((element) => {
      const key = element.getAttribute("data-bind");
      if (Object.prototype.hasOwnProperty.call(values, key)) {
        element.textContent = values[key];
      }
    });
  }

  function updateEvidence() {
    setBindings();

    $("#ev-subtitle").innerHTML =
      `Período seleccionado: <b>${state.yearFrom} - ${state.yearTo}</b> | ` +
      `Sucursal: <b>${escapeHtml(state.sucursal)}</b> | ` +
      `Reseñas en período: <b>${fmtInt(cache.period.length)}</b> ` +
      `(Filtradas: <b>${fmtInt(cache.filtered.length)}</b>)`;

    renderSucursalTable();
  }

  function renderSucursalTable() {
    const tbody = $("#suc-tbody");
    tbody.replaceChildren();

    if (!cache.sucursal.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 6;
      td.className = "empty-cell";
      td.textContent = "Sin datos para el período seleccionado.";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    cache.sucursal.forEach((item) => {
      const tr = document.createElement("tr");
      [
        item.name,
        fmtInt(item.total),
        two(item.avg),
        fmtInt(item.neg),
        one(item.pctNeg),
        fmtInt(item.resp),
      ].forEach((value) => {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function updateExplorer() {
    const results = M.search(cache.filtered, state.search);
    cache.results = results;

    const total = results.length;
    const shown = Math.min(total, state.page * PAGE_SIZE);

    const list = $("#review-list");
    list.replaceChildren();
    for (let index = 0; index < shown; index += 1) {
      list.appendChild(reviewItem(results[index]));
    }

    $("#resenas-subtitle").innerHTML =
      `Mostrando <b>${fmtInt(cache.filtered.length)}</b> reseñas filtradas ` +
      `(${state.yearFrom} - ${state.yearTo})`;
    $("#review-visible").textContent = total
      ? `Mostrando ${fmtInt(shown)} de ${fmtInt(total)} reseñas.`
      : "";
    $("#review-empty").hidden = total !== 0;
    $("#review-more").hidden = shown >= total;
    $("#review-more").textContent = `Mostrar más (${fmtInt(total - shown)} restantes)`;

    const query = state.search.trim();
    $("#search-caption").hidden = !query;
    $("#search-caption").textContent = query
      ? `Coincidencias encontradas: ${fmtInt(total)}`
      : "";
  }

  function reviewItem(row) {
    const details = document.createElement("details");
    details.className = "review";

    const summary = document.createElement("summary");
    summary.appendChild(badge(`[${row.estrellas} ⭐]`, "badge badge-stars"));
    if (row.sucursal) summary.appendChild(badge(row.sucursal, "badge"));

    const author = document.createElement("strong");
    author.className = "author";
    author.textContent = row.autor || "Anónimo";
    summary.appendChild(author);

    summary.appendChild(badge(`Año: ${row.anio_estimado}`, "badge"));
    summary.appendChild(
      badge(row.categoria_principal || "Sin categoría", "badge")
    );

    const body = document.createElement("div");
    body.className = "review-body";

    if (M.hasText(row)) {
      const text = document.createElement("p");
      text.className = "review-text";
      text.textContent = row.texto;
      body.appendChild(text);
    } else {
      const empty = document.createElement("p");
      empty.className = "review-no-text";
      empty.textContent = "El usuario dejó solo calificación sin texto.";
      body.appendChild(empty);
    }

    if (M.hasResponse(row)) {
      const response = document.createElement("div");
      response.className = "owner-response";
      const label = document.createElement("b");
      label.textContent = "Respuesta oficial del comercio:";
      response.appendChild(label);
      response.appendChild(document.createTextNode(row.respuesta_dueno));
      body.appendChild(response);
    }

    details.append(summary, body);
    return details;
  }

  function badge(text, className) {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    return span;
  }

  function downloadCsv() {
    if (!cache.results) return;
    const csv = M.toCsv(cache.results, payload.columns);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `resenas_filtradas_${state.yearFrom}_${state.yearTo}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  /* ---------------- Router y navegación ---------------- */

  function routeFromHash() {
    const route = window.location.hash.replace(/^#\/?/, "");
    return ROUTES.includes(route) ? route : "diagnostico";
  }

  function showRoute(route) {
    currentRoute = route;
    $$(".page").forEach((section) => {
      section.hidden = section.id !== route;
    });
    $$(".nav a").forEach((link) => {
      if (link.dataset.route === route) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    document.title = `${ROUTE_TITLES[route]} — El Emporio del Terciado`;
    const topbarTitle = $("#topbar-title");
    if (topbarTitle) topbarTitle.textContent = ROUTE_TITLES[route];
    window.scrollTo(0, 0);
    closeNav();

    if (route === "diagnostico") {
      requestAnimationFrame(plotRadar);
    } else if (route === "evidencia" && cache.filtered) {
      requestAnimationFrame(() => plotEvidenceTab(selectedEvidenceTab));
    }
  }

  function setupMobileNav() {
    const body = document.body;
    const overlay = $("#overlay");
    const menuButton = $("#btn-menu");
    const filtersButton = $("#btn-filters");

    const open = () => {
      lastFocused = document.activeElement;
      body.classList.add("nav-open");
      overlay.hidden = false;
      menuButton.setAttribute("aria-expanded", "true");
      const first = $(".nav a");
      if (first) first.focus();
    };

    const close = () => {
      if (!body.classList.contains("nav-open")) return;
      body.classList.remove("nav-open");
      overlay.hidden = true;
      menuButton.setAttribute("aria-expanded", "false");
      if (lastFocused && typeof lastFocused.focus === "function") {
        lastFocused.focus();
      }
    };

    closeNav = close;

    menuButton.addEventListener("click", () => {
      if (body.classList.contains("nav-open")) close();
      else open();
    });

    filtersButton.addEventListener("click", () => {
      open();
      const filters = $(".filters");
      if (filters) filters.scrollIntoView({ block: "start" });
    });

    overlay.addEventListener("click", close);
    $("#btn-close").addEventListener("click", close);

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && body.classList.contains("nav-open")) {
        close();
      }
    });

    $$(".nav a").forEach((link) => link.addEventListener("click", close));
  }

  /* ---------------- Tabs ---------------- */

  function setupTabs() {
    $$("[data-tabs]").forEach((container) => {
      const tabs = $$('[role="tab"]', container);
      const panels = $$('[role="tabpanel"]', container);
      container.__tabs = tabs;
      container.__panels = panels;

      tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => selectTab(container, index, false));
        tab.addEventListener("keydown", (event) => {
          let target = null;
          if (event.key === "ArrowRight") target = (index + 1) % tabs.length;
          if (event.key === "ArrowLeft") {
            target = (index - 1 + tabs.length) % tabs.length;
          }
          if (event.key === "Home") target = 0;
          if (event.key === "End") target = tabs.length - 1;
          if (target !== null) {
            event.preventDefault();
            selectTab(container, target, true);
          }
        });
      });

      selectTab(container, 0, false);
    });
  }

  function selectTab(container, index, focus) {
    const tabs = container.__tabs;
    const panels = container.__panels;
    tabs.forEach((tab, position) => {
      const active = position === index;
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.tabIndex = active ? 0 : -1;
      panels[position].hidden = !active;
    });
    if (focus) tabs[index].focus();

    if (container.id === "tabs-evidencia") {
      selectedEvidenceTab = index;
      if (currentRoute === "evidencia" && cache.filtered) {
        plotEvidenceTab(index);
      }
    }
  }

  /* ---------------- Gráficos ---------------- */

  function plot(element, traces, layout) {
    if (!element) return;
    if (typeof window.Plotly === "undefined") {
      showChartMessage(
        element,
        "No se pudo cargar la librería de gráficos (Plotly)."
      );
      return;
    }
    const config = {
      responsive: true,
      displayModeBar: false,
      displaylogo: false,
    };
    const fullLayout = Object.assign({}, BASE_LAYOUT, layout);

    if (!traces.length) {
      showChartMessage(element, "Sin datos para los filtros seleccionados.");
      return;
    }

    if (element.__plotted) {
      window.Plotly.react(element, traces, fullLayout, config);
    } else {
      element.replaceChildren();
      window.Plotly.newPlot(element, traces, fullLayout, config);
      element.__plotted = true;
    }

    requestAnimationFrame(() => {
      if (!element.__plotted || !window.Plotly) return;
      try {
        window.Plotly.Plots.resize(element);
      } catch (error) {
        /* el contenedor puede estar oculto; se reintenta al mostrarlo */
      }
    });
  }

  function showChartMessage(element, message) {
    if (element.__plotted && typeof window.Plotly !== "undefined") {
      window.Plotly.purge(element);
      element.__plotted = false;
    }
    const paragraph = document.createElement("p");
    paragraph.className = "chart-empty";
    paragraph.textContent = message;
    element.replaceChildren(paragraph);
  }

  function plotRadar() {
    const element = $("#chart-radar");
    if (!element) return;

    const categoriesRadar = [
      "1. Estrategia",
      "2. Tecnología",
      "3. Datos",
      "4. Procesos",
      "5. Personas",
      "6. Clientes",
    ];
    const asis = [1.5, 1.8, 1.2, 1.5, 2.0, 1.6];
    const tobe = [4.0, 4.0, 3.8, 4.2, 3.9, 4.5];

    plot(
      element,
      [
        {
          type: "scatterpolar",
          r: [...asis, asis[0]],
          theta: [...categoriesRadar, categoriesRadar[0]],
          fill: "toself",
          name: "Madurez Actual (AS-IS) [1.6/5.0]",
          line: { color: "#0072B2", width: 2.5 },
          fillcolor: "rgba(0, 114, 178, 0.25)",
          marker: { size: 7, symbol: "circle" },
        },
        {
          type: "scatterpolar",
          r: [...tobe, tobe[0]],
          theta: [...categoriesRadar, categoriesRadar[0]],
          fill: "toself",
          name: "Objetivo Estratégico (TO-BE) [4.1/5.0]",
          line: { color: "#009E73", width: 2, dash: "dash" },
          fillcolor: "rgba(0, 158, 115, 0.15)",
          marker: { size: 6, symbol: "diamond" },
        },
      ],
      {
        height: 400,
        margin: { l: 40, r: 40, t: 15, b: 65 },
        polar: {
          radialaxis: {
            visible: true,
            range: [0, 5],
            tickvals: [1, 2, 3, 4, 5],
            showticklabels: false,
            tickfont: { size: 9, color: "#64748B" },
            gridcolor: "#E2E8F0",
            linecolor: "#E2E8F0",
          },
          angularaxis: {
            tickfont: { size: 10, color: "#1E293B" },
            rotation: 90,
            direction: "clockwise",
            gridcolor: "#E2E8F0",
          },
        },
        showlegend: true,
        legend: {
          orientation: "h",
          y: -0.18,
          x: 0.5,
          xanchor: "center",
          font: { size: 10 },
        },
      }
    );
  }

  function plotEvidenceTab(index) {
    if (!cache.filtered) return;
    if (index === 0) plotBalance();
    else if (index === 1) {
      plotNlp();
      plotStars();
    } else if (index === 2) plotSucursal();
    else if (index === 3) plotTemporal();
  }

  function plotBalance() {
    const element = $("#chart-balance");
    if (!element) return;
    if (!cache.balance.total) {
      showChartMessage(element, "Sin datos para los filtros seleccionados.");
      return;
    }

    const balance = cache.balance;
    plot(
      element,
      [
        {
          type: "bar",
          x: [
            "Opiniones Positivas<br>(Fortalezas ⭐4-5)",
            "Opiniones Críticas<br>(Debilidades ⭐1-3)",
          ],
          y: [balance.pos, balance.neg],
          text: [
            `${balance.pos} (${one(balance.pctPos)})`,
            `${balance.neg} (${one(balance.pctNeg)})`,
          ],
          textposition: "outside",
          cliponaxis: false,
          marker: { color: ["#009E73", "#0072B2"] },
          hovertemplate: "%{y} reseñas<extra></extra>",
        },
      ],
      {
        height: 340,
        margin: { l: 55, r: 20, t: 40, b: 60 },
        xaxis: { tickfont: { size: 10 } },
        yaxis: {
          gridcolor: "#E2E8F0",
          zeroline: false,
          rangemode: "tozero",
        },
        bargap: 0.45,
        showlegend: false,
      }
    );
  }

  function plotNlp() {
    const element = $("#chart-nlp");
    if (!element) return;
    if (!cache.filteredText.length) {
      showChartMessage(element, "No hay comentarios de texto para los filtros seleccionados.");
      return;
    }

    const ranked = [...cache.nlp].sort((a, b) => b.count - a.count);
    const colorByLabel = new Map(
      ranked.map((item, index) => [
        item.label,
        PALETTE[Math.min(index, PALETTE.length - 1)],
      ])
    );

    plot(
      element,
      [
        {
          type: "bar",
          orientation: "h",
          x: cache.nlp.map((item) => item.count),
          y: cache.nlp.map((item) => item.label),
          text: cache.nlp.map((item) => `${fmtInt(item.count)} (${one(item.pct)})`),
          textposition: "outside",
          cliponaxis: false,
          marker: {
            color: cache.nlp.map((item) => colorByLabel.get(item.label)),
          },
          hovertemplate: "%{y}: %{x} menciones<extra></extra>",
        },
      ],
      {
        height: 380,
        margin: { l: 10, r: 70, t: 10, b: 45 },
        xaxis: {
          title: { text: "Cantidad de menciones", font: { size: 11 } },
          gridcolor: "#E2E8F0",
          zeroline: false,
        },
        yaxis: { automargin: true, tickfont: { size: 10 } },
        bargap: 0.3,
        showlegend: false,
      }
    );
  }

  function plotStars() {
    const element = $("#chart-stars");
    if (!element) return;
    if (!cache.overview.total) {
      showChartMessage(element, "Sin datos para los filtros seleccionados.");
      return;
    }

    plot(
      element,
      [
        {
          type: "pie",
          labels: cache.stars.map(
            (item) =>
              `${item.stars} Estrella${item.stars > 1 ? "s" : ""}`
          ),
          values: cache.stars.map((item) => item.count),
          hole: 0.45,
          marker: {
            colors: cache.stars.map((item) => STAR_COLORS[item.stars]),
          },
          text: cache.stars.map((item) =>
            one((item.count / cache.overview.total) * 100)
          ),
          textinfo: "label+text",
          textfont: { size: 9 },
          sort: false,
          hovertemplate: "%{label}: %{value} (%{percent})<extra></extra>",
        },
      ],
      {
        height: 380,
        margin: { l: 10, r: 10, t: 10, b: 10 },
        showlegend: false,
      }
    );
  }

  function plotSucursal() {
    const element = $("#chart-sucursal");
    if (!element) return;
    if (!cache.yearRows.length) {
      showChartMessage(element, "Sin datos para el período seleccionado.");
      return;
    }

    const counts = new Map();
    cache.yearRows.forEach((row) => {
      const key = `${row.sucursal}|${row.estrellas}`;
      counts.set(key, (counts.get(key) || 0) + 1);
    });

    const names = cache.sucursal.map(
      (item) => SHORT_SUCURSAL[item.name] || item.name
    );

    const traces = [1, 2, 3, 4, 5].map((star) => ({
      type: "bar",
      name: `${star} Estrella${star > 1 ? "s" : ""}`,
      x: names,
      y: cache.sucursal.map(
        (item) => counts.get(`${item.name}|${star}`) || 0
      ),
      marker: { color: STAR_COLORS[star] },
      hovertemplate: "%{x}: %{y} reseñas<extra></extra>",
    }));

    plot(element, traces, {
      height: 380,
      barmode: "group",
      bargap: 0.25,
      margin: { l: 45, r: 15, t: 15, b: 70 },
      xaxis: { tickfont: { size: 10 }, automargin: true },
      yaxis: {
        title: { text: "Cantidad", font: { size: 11 } },
        gridcolor: "#E2E8F0",
        zeroline: false,
      },
      legend: {
        orientation: "h",
        y: -0.28,
        x: 0.5,
        xanchor: "center",
        font: { size: 10 },
      },
    });
  }

  function plotTemporal() {
    const element = $("#chart-temporal");
    if (!element) return;
    if (!cache.temporal.length) {
      showChartMessage(element, "Sin datos para los filtros seleccionados.");
      return;
    }

    const yearsList = Array.from(
      new Set(cache.temporal.map((item) => item.year))
    ).sort((a, b) => a - b);
    const counts = new Map(
      cache.temporal.map((item) => [`${item.year}|${item.stars}`, item.count])
    );

    const traces = [1, 2, 3, 4, 5].map((star) => ({
      type: "bar",
      name: `${star} Estrella${star > 1 ? "s" : ""}`,
      x: yearsList,
      y: yearsList.map((year) => counts.get(`${year}|${star}`) || 0),
      marker: { color: STAR_COLORS[star] },
      hovertemplate: "%{x}: %{y} reseñas<extra></extra>",
    }));

    plot(element, traces, {
      height: 400,
      barmode: "stack",
      margin: { l: 50, r: 20, t: 15, b: 70 },
      xaxis: {
        dtick: 1,
        title: { text: "Año", font: { size: 11 } },
        tickfont: { size: 10 },
      },
      yaxis: {
        title: { text: "Cantidad de reseñas", font: { size: 11 } },
        gridcolor: "#E2E8F0",
        zeroline: false,
      },
      legend: {
        orientation: "h",
        y: -0.25,
        x: 0.5,
        xanchor: "center",
        font: { size: 10 },
      },
    });
  }

  /* ---------------- Utilidades ---------------- */

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => {
      const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return map[character];
    });
  }

  function showFatal(error) {
    if (window.console && console.error) console.error(error);
    const main = document.getElementById("main");
    if (!main) return;

    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("h2");
    title.textContent = "No se pudieron cargar los datos";
    const message = document.createElement("p");
    message.textContent =
      "Verificá que docs/data/resenas.json exista y que el sitio se sirva por HTTP " +
      "(no como archivo local). Detalle: " +
      (error && error.message ? error.message : String(error));
    card.append(title, message);
    main.replaceChildren(card);
  }
})();
