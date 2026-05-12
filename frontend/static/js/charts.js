const palette = {
  coffee: "#6f4e37",
  green: "#1f8a5f",
  blue: "#2563eb",
  amber: "#b7791f",
  red: "#c2410c",
  slate: "#475569",
  teal: "#0f766e",
  violet: "#7c3aed",
  rose: "#be123c",
  cyan: "#0891b2",
};

const chartInstances = new Map();

function mountChart(id, config) {
  const canvas = document.getElementById(id);
  if (!canvas || !window.Chart) return null;

  const existing = chartInstances.get(id);
  if (existing) existing.destroy();

  const chart = new Chart(canvas, config);
  chartInstances.set(id, chart);
  return chart;
}

function baseOptions(extra = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 450 },
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        labels: {
          usePointStyle: true,
          boxWidth: 8,
        },
      },
      tooltip: {
        padding: 12,
        callbacks: extra.tooltipCallbacks || {},
      },
    },
    scales: extra.scales || {},
  };
}

export function renderMarketChart(productionData = [], exportData = []) {
  const exportByYear = new Map(exportData.map((item) => [Number(item.year), item]));
  const rows = productionData.map((item) => ({
    ...item,
    ...(exportByYear.get(Number(item.year)) || {}),
  }));

  if (!rows.length) return null;

  return mountChart("marketChart", {
    type: "line",
    data: {
      labels: rows.map((row) => row.year),
      datasets: [
        {
          label: "Production (M tons)",
          data: rows.map((row) => Number(row.output_tons || row.production_tons || 0) / 1_000_000),
          borderColor: palette.green,
          backgroundColor: "rgba(31, 138, 95, 0.12)",
          tension: 0.32,
          fill: true,
          yAxisID: "volume",
        },
        {
          label: "Export value (B USD)",
          data: rows.map((row) => Number(row.export_value_million_usd || 0) / 1000),
          borderColor: palette.blue,
          backgroundColor: "rgba(37, 99, 235, 0.1)",
          tension: 0.32,
          fill: true,
          yAxisID: "value",
        },
        {
          label: "VN price (K USD/ton)",
          data: rows.map((row) => Number(row.price_vn_usd_per_ton || 0) / 1000),
          borderColor: palette.coffee,
          backgroundColor: "rgba(111, 78, 55, 0.08)",
          tension: 0.32,
          yAxisID: "value",
        },
      ],
    },
    options: baseOptions({
      scales: {
        volume: { type: "linear", position: "left", grid: { color: "rgba(148, 163, 184, 0.22)" } },
        value: { type: "linear", position: "right", grid: { drawOnChartArea: false } },
        x: { grid: { display: false } },
      },
    }),
  });
}

export function renderExportChart(countries = []) {
  if (!countries.length) return null;

  return mountChart("exportChart", {
    type: "doughnut",
    data: {
      labels: countries.map((country) => country.name),
      datasets: [
        {
          data: countries.map((country) => country.percentage),
          backgroundColor: [
            palette.blue,
            palette.green,
            palette.amber,
            palette.coffee,
            palette.teal,
            palette.violet,
            palette.rose,
            palette.cyan,
            palette.slate,
          ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(context) {
              return `${context.label}: ${context.parsed}%`;
            },
          },
        },
      },
    },
  });
}

export function renderPriceChart(provinces = []) {
  if (!provinces.length) return null;

  const dates = Array.from(new Set(provinces.flatMap((province) => province.prices.map((price) => price.date)))).sort();
  const colors = [palette.green, palette.blue, palette.amber, palette.coffee];

  return mountChart("priceChart", {
    type: "line",
    data: {
      labels: dates,
      datasets: provinces.map((province, index) => ({
        label: province.display_name || province.name,
        data: dates.map((date) => province.prices.find((price) => price.date === date)?.price ?? null),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length],
        tension: 0.28,
        spanGaps: true,
      })),
    },
    options: baseOptions({
      scales: {
        y: { grid: { color: "rgba(148, 163, 184, 0.22)" } },
        x: { grid: { display: false } },
      },
    }),
  });
}

export function renderWeatherChart(records = []) {
  if (!records.length) return null;

  const labels = records.map((row) => `${row.month || ""}/${row.year}`.replace(/^\//, ""));

  return mountChart("weatherChart", {
    data: {
      labels,
      datasets: [
        {
          type: "bar",
          label: "Rainfall (mm)",
          data: records.map((row) => row.precipitation_sum),
          backgroundColor: "rgba(37, 99, 235, 0.26)",
          borderColor: palette.blue,
          borderWidth: 1,
          yAxisID: "rain",
        },
        {
          type: "line",
          label: "Temperature (C)",
          data: records.map((row) => row.temperature_mean),
          borderColor: palette.red,
          backgroundColor: palette.red,
          tension: 0.25,
          yAxisID: "temp",
        },
      ],
    },
    options: baseOptions({
      scales: {
        rain: { type: "linear", position: "left", grid: { color: "rgba(148, 163, 184, 0.22)" } },
        temp: { type: "linear", position: "right", grid: { drawOnChartArea: false } },
        x: { grid: { display: false } },
      },
    }),
  });
}
