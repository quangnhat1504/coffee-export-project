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
  document.getElementById("exportLimit")?.addEventListener("change", async (event) => {
    await loadCountries(Number(event.target.value));
  });

  document.getElementById("provinceSelect")?.addEventListener("change", async (event) => {
    await loadWeatherPanel(event.target.value);
  });

  document.getElementById("generateInsightButton")?.addEventListener("click", generateDashboardInsight);
}

async function loadDashboard() {
  await loadHealth();

  await Promise.allSettled([
    loadMarketData(),
    loadCountries(Number(document.getElementById("exportLimit")?.value || 9)),
    loadPrices(),
    loadWeatherPanel(document.getElementById("provinceSelect")?.value || "DakLak"),
  ]);

  renderInsightSeed();
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
  try {
    const [production, exportOverview] = await Promise.all([getProduction(), getExportOverview()]);
    state.production = production;
    state.exportOverview = exportOverview;
    renderKpis();
    renderMarketChart(production.data || [], exportOverview.data || []);
  } catch (error) {
    setEmptyChart("marketChart", error.message);
  }
}

async function loadCountries(limit) {
  try {
    state.countries = await getExportCountries(limit);
    document.getElementById("exportYearLabel").textContent = `Year ${state.countries.year || "--"}`;
    renderExportChart(state.countries.countries || []);
    renderCountryList(state.countries.countries || []);
  } catch (error) {
    setEmptyChart("exportChart", error.message);
    document.getElementById("countryList").innerHTML = "";
  }
}

async function loadPrices() {
  try {
    state.prices = await getRecentPrices(7);
    renderPriceChart(state.prices.provinces || []);
    renderPriceKpi();
  } catch (error) {
    setEmptyChart("priceChart", error.message);
  }
}

async function loadWeatherPanel(province) {
  try {
    state.weather = await getWeather(province);
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
  const latestExport = exportRows.at(-1) || {};

  setText("kpiProduction", fmt.tons(latestProduction.output_tons || latestExport.production_tons));
  setText("kpiProductionMeta", latestProduction.year ? `Year ${latestProduction.year}` : "Latest year");
  setText("kpiExportValue", fmt.usdB(latestExport.export_value_million_usd));
  setText("kpiExportMeta", latestExport.year ? `Year ${latestExport.year}` : "Annual value");
  setText("kpiWorldPrice", fmt.usdTon(latestExport.price_world_usd_per_ton));
  setText("kpiWorldPriceMeta", latestExport.year ? `Year ${latestExport.year}` : "USD per ton");
}

function renderPriceKpi() {
  const provinces = state.prices?.provinces || [];
  const top = provinces
    .filter((province) => province.current_price != null)
    .sort((a, b) => b.current_price - a.current_price)[0];

  setText("kpiProvincePrice", fmt.vndKg(top?.current_price));
  setText("kpiProvincePriceMeta", top ? top.display_name || top.name : "Latest province price");
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
  box.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
