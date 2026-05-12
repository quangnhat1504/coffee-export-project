const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const message = data.error || data.message || `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export function getHealth() {
  return request("/health");
}

export function getProduction() {
  return request("/production");
}

export function getExportOverview() {
  return request("/export/overview");
}

export function getExportCountries(limit = 9) {
  return request(`/export/countries?limit=${encodeURIComponent(limit)}`);
}

export function getRecentPrices(days = 7) {
  return request(`/prices/recent?days=${encodeURIComponent(days)}`);
}

export function getWeather(province = "DakLak") {
  return request(`/weather/province/${encodeURIComponent(province)}?aggregate=recent12`);
}

export function generateInsight(payload) {
  return request("/ai/insight", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
