import {
  generateInsight,
  getExportCountries,
  getExportOverview,
  getHealth,
  getProduction,
  getRecentPrices,
  getWeather,
} from "./api.js";

import {
  renderExportChart,
  renderMarketChart,
  renderPriceChart,
  renderWeatherChart,
} from "./charts.js";

const state = {
  health: null,
  production: null,
  exportOverview: null,
  countries: null,
  prices: null,
  weather: null,
};

const fmt = {
  tons(value) {
    if (value == null) return "--";
    return `${(Number(value) / 1_000_000).toFixed(2)}M t`;
  },
  usdB(value) {
    if (value == null) return "--";
    return `$${(Number(value) / 1000).toFixed(2)}B`;
  },
  usdTon(value) {
    if (value == null) return "--";
    return `$${Math.round(Number(value)).toLocaleString("en-US")}`;
  },
  vndKg(value) {
    if (value == null) return "--";
    return `${Math.round(Number(value)).toLocaleString("vi-VN")} đ/kg`;
  },
};

document.addEventListener("DOMContentLoaded", () => {
  bindControls();
  loadDashboard();
});

function bindControls() {
  document.getElementById("refreshDashboardButton")?.addEventListener("click", loadDashboard);

  document.getElementById("exportLimit")?.addEventListener("change", async (event) => {
    await loadCountries(Number(event.target.value));
  });

  document.getElementById("provinceSelect")?.addEventListener("change", async (event) => {
    await loadWeatherPanel(event.target.value);
  });

  document.getElementById("generateInsightButton")?.addEventListener("click", generateDashboardInsight);
}

async function loadDashboard() {
  setDashboardBusy(true);
  await loadHealth();

  await Promise.allSettled([
    loadMarketData(),
    loadCountries(Number(document.getElementById("exportLimit")?.value || 9)),
    loadPrices(),
    loadWeatherPanel(document.getElementById("provinceSelect")?.value || "DakLak"),
  ]);

  renderInsightSeed();
  setDashboardBusy(false);
}

async function loadHealth() {
  try {
    state.health = await getHealth();
  } catch (error) {
    state.health = error.data || { status: "offline", database: { connected: false }, ai: { configured: false } };
  }
  renderHealth();
}

async function loadMarketData() {
  setChartLoading("marketChart", "Loading market data...");
  try {
    const [production, exportOverview] = await Promise.all([getProduction(), getExportOverview()]);
    state.production = production;
    state.exportOverview = exportOverview;
    clearChartState("marketChart");
    renderKpis();
    renderMarketChart(production.data || [], exportOverview.data || []);
  } catch (error) {
    setEmptyChart("marketChart", error.message);
    clearKpiLoading(["kpiProduction", "kpiExportValue", "kpiWorldPrice"]);
  }
}

async function loadCountries(limit) {
  setChartLoading("exportChart", "Loading importer ranking...");
  try {
    state.countries = await getExportCountries(limit);
    document.getElementById("exportYearLabel").textContent = `Year ${state.countries.year || "--"}`;
    clearChartState("exportChart");
    renderExportChart(state.countries.countries || []);
    renderCountryList(state.countries.countries || []);
  } catch (error) {
    setEmptyChart("exportChart", error.message);
    document.getElementById("countryList").innerHTML = "";
  }
}

async function loadPrices() {
  setChartLoading("priceChart", "Loading province prices...");
  try {
    state.prices = await getRecentPrices(7);
    clearChartState("priceChart");
    renderPriceChart(state.prices.provinces || []);
    renderPriceKpi();
  } catch (error) {
    setEmptyChart("priceChart", error.message);
    clearKpiLoading(["kpiProvincePrice"]);
  }
}

async function loadWeatherPanel(province) {
  setChartLoading("weatherChart", "Loading weather data...");
  try {
    state.weather = await getWeather(province);
    clearChartState("weatherChart");
    renderWeatherChart(state.weather.data || []);
  } catch (error) {
    setEmptyChart("weatherChart", error.message);
  }
}

function renderHealth() {
  const health = state.health || {};
  const apiOk = health.api === "running" || health.success;
  const dbOk = Boolean(health.database?.connected);
  const aiOk = Boolean(health.ai?.configured);

  setPill("apiStatus", "API", apiOk ? "ok" : "error");
  setPill("dbStatus", "Database", dbOk ? "ok" : "warn");
  setPill("aiStatus", health.ai?.model || "AI", aiOk ? "ok" : "warn");

  const summary = document.getElementById("statusSummary");
  if (summary) {
    summary.textContent = dbOk
      ? "Backend and database are available."
      : `Backend is running. Database is degraded: ${health.database?.message || "unavailable"}`;
  }
}

function setPill(id, label, status) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = label;
  el.className = `status-pill ${status}`;
}

function renderKpis() {
  const productionRows = state.production?.data || [];
  const exportRows = state.exportOverview?.data || [];
  const latestProduction = productionRows.at(-1) || {};
  const previousProduction = productionRows.at(-2) || {};
  const latestExport = exportRows.at(-1) || {};
  const previousExport = exportRows.at(-2) || {};

  setText("kpiProduction", fmt.tons(latestProduction.output_tons || latestExport.production_tons));
  setText("kpiProductionMeta", latestProduction.year ? `Year ${latestProduction.year}` : "Latest year");
  setTrend("kpiProductionTrend", latestProduction.output_tons || latestExport.production_tons, previousProduction.output_tons || previousExport.production_tons, "YoY");
  setText("kpiExportValue", fmt.usdB(latestExport.export_value_million_usd));
  setText("kpiExportMeta", latestExport.year ? `Year ${latestExport.year}` : "Annual value");
  setTrend("kpiExportTrend", latestExport.export_value_million_usd, previousExport.export_value_million_usd, "YoY");
  setText("kpiWorldPrice", fmt.usdTon(latestExport.price_world_usd_per_ton));
  setText("kpiWorldPriceMeta", latestExport.year ? `Year ${latestExport.year}` : "USD per ton");
  setTrend("kpiWorldPriceTrend", latestExport.price_world_usd_per_ton, previousExport.price_world_usd_per_ton, "YoY");
  clearKpiLoading(["kpiProduction", "kpiExportValue", "kpiWorldPrice"]);
}

function renderPriceKpi() {
  const provinces = state.prices?.provinces || [];
  const top = provinces
    .filter((province) => province.current_price != null)
    .sort((a, b) => b.current_price - a.current_price)[0];

  setText("kpiProvincePrice", fmt.vndKg(top?.current_price));
  setText("kpiProvincePriceMeta", top ? top.display_name || top.name : "Latest province price");
  setTrend("kpiProvincePriceTrend", top?.price_change_percent, 0, "recent", { alreadyPercent: true });
  clearKpiLoading(["kpiProvincePrice"]);
}

function renderCountryList(countries) {
  const list = document.getElementById("countryList");
  if (!list) return;

  if (!countries.length) {
    list.innerHTML = `<div class="empty-state">No export country data available.</div>`;
    return;
  }

  list.innerHTML = countries
    .map((country) => `
      <div class="country-row">
        <strong>${escapeHtml(country.name)}</strong>
        <span>${Math.round(country.volume).toLocaleString("en-US")} t</span>
        <span>${Number(country.percentage).toFixed(1)}%</span>
      </div>
    `)
    .join("");
}

function renderInsightSeed() {
  const output = document.getElementById("insightOutput");
  if (!output) return;

  if (state.health?.ai?.configured) {
    output.textContent = "AI is ready.";
  } else {
    output.textContent = "AI is not configured.";
  }
}

function setDashboardBusy(isBusy) {
  const refreshButton = document.getElementById("refreshDashboardButton");
  if (refreshButton) {
    refreshButton.disabled = isBusy;
    refreshButton.textContent = isBusy ? "Refreshing..." : "Refresh";
  }

  if (isBusy) {
    document.querySelectorAll(".kpi-card").forEach((card) => card.classList.add("loading"));
  }
}

async function generateDashboardInsight() {
  const button = document.getElementById("generateInsightButton");
  const output = document.getElementById("insightOutput");
  if (!button || !output) return;

  button.disabled = true;
  output.textContent = "Generating insight...";

  try {
    const payload = {
      question: "Tóm tắt 3 insight quan trọng nhất từ dashboard cà phê hiện tại.",
      data: {
        production_latest: state.production?.data?.at(-1) || null,
        export_latest: state.exportOverview?.data?.at(-1) || null,
        top_importers: state.countries?.countries?.slice(0, 5) || [],
        province_prices: state.prices?.provinces?.map((province) => ({
          province: province.display_name || province.name,
          current_price: province.current_price,
          change_percent: province.price_change_percent,
        })) || [],
        weather_latest: state.weather?.data?.at(-1) || null,
      },
    };

    const result = await generateInsight(payload);
    output.textContent = result.insight || "No insight returned.";
  } catch (error) {
    output.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function setEmptyChart(canvasId, message) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const box = canvas.parentElement;
  if (!box) return;
  clearChartState(canvasId);
  box.classList.add("has-message");
  box.insertAdjacentHTML("beforeend", `<div class="empty-state chart-message">${escapeHtml(message)}</div>`);
}

function setChartLoading(canvasId, message) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const box = canvas.parentElement;
  if (!box) return;
  clearChartState(canvasId);
  box.classList.add("is-loading", "has-message");
  box.insertAdjacentHTML("beforeend", `<div class="empty-state chart-message">${escapeHtml(message)}</div>`);
}

function clearChartState(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas?.parentElement) return;
  const box = canvas.parentElement;
  box.classList.remove("is-loading", "has-message");
  box.querySelectorAll(".chart-message").forEach((element) => element.remove());
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setTrend(id, current, previous, suffix, options = {}) {
  const el = document.getElementById(id);
  if (!el) return;

  const currentValue = Number(current);
  const previousValue = Number(previous);
  if (!Number.isFinite(currentValue) || (!options.alreadyPercent && (!Number.isFinite(previousValue) || previousValue === 0))) {
    el.textContent = "No comparison";
    el.className = "kpi-trend flat";
    return;
  }

  const change = options.alreadyPercent ? currentValue : ((currentValue - previousValue) / Math.abs(previousValue)) * 100;
  const direction = change > 0.05 ? "up" : change < -0.05 ? "down" : "flat";
  const sign = change > 0 ? "+" : "";
  el.textContent = `${sign}${change.toFixed(1)}% ${suffix}`;
  el.className = `kpi-trend ${direction}`;
}

function clearKpiLoading(valueIds) {
  valueIds.forEach((id) => {
    document.getElementById(id)?.closest(".kpi-card")?.classList.remove("loading");
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
