// === Configuration ===
const API_BASE = "http://127.0.0.1:8000";

// === State ===
let currentSymbol = null;
let currentDays = 30;
let chartInstance = null;

// === Utility ===
const fmt = {
  inr: (n) => n == null ? "—" : `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`,
  pct: (n) => n == null ? "—" : `${n > 0 ? "+" : ""}${n.toFixed(2)}%`,
};

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// === Initial load: companies list ===
async function loadCompanies() {
  try {
    const companies = await fetchJSON(`${API_BASE}/companies`);
    const list = document.getElementById("company-list");
    list.innerHTML = "";
    companies.forEach(c => {
      const li = document.createElement("li");
      li.dataset.symbol = c.symbol;
      li.innerHTML = `
        <span class="li-symbol">${c.symbol.replace(".NS", "")}</span>
        <span class="li-sector">${c.sector}</span>
      `;
      li.addEventListener("click", () => selectCompany(c.symbol));
      list.appendChild(li);
    });
  } catch (err) {
    document.getElementById("company-list").innerHTML =
      `<li class="loading">⚠️ Failed to load — is the API running?</li>`;
    console.error(err);
  }
}

// === When user clicks a company ===
async function selectCompany(symbol) {
  currentSymbol = symbol;

  // Update sidebar active state
  document.querySelectorAll("#company-list li").forEach(li => {
    li.classList.toggle("active", li.dataset.symbol === symbol);
  });

  // Show detail view
  document.getElementById("placeholder").classList.add("hidden");
  document.getElementById("stock-detail").classList.remove("hidden");

  // Load both data + summary in parallel
  await Promise.all([loadStockData(), loadSummary()]);
}

// === Load chart data ===
async function loadStockData() {
  try {
    const dataUrl = `${API_BASE}/data/${currentSymbol}?days=${currentDays}`;
    const predictUrl = `${API_BASE}/predict/${currentSymbol}?lookback=60&days=7`;

    // Fetch both in parallel
    const [result, prediction] = await Promise.all([
      fetchJSON(dataUrl),
      fetchJSON(predictUrl).catch(() => null),  // prediction failure shouldn't break chart
    ]);

    const labels = result.data.map(d => d.date);
    const closes = result.data.map(d => d.close);
    const ma7 = result.data.map(d => d.ma_7);

    // Append prediction data points to the same chart
    let predLabels = [];
    let predValues = [];
    if (prediction && prediction.predictions) {
      predLabels = prediction.predictions.map(p => p.date);
      // For prediction overlay: nulls during history, then values during prediction
      // Last historical close acts as the "bridge" point
      const bridge = closes[closes.length - 1];
      predValues = [
        ...new Array(closes.length - 1).fill(null),
        bridge,
        ...prediction.predictions.map(p => p.predicted_close),
      ];
    }

    const allLabels = [...labels, ...predLabels];

    renderChart(allLabels, closes, ma7, predValues);

    // Header info
    document.getElementById("stock-name").textContent = result.name;
    document.getElementById("stock-sector").textContent = result.sector;

    const latest = result.data[result.data.length - 1];
    document.getElementById("latest-price").textContent = fmt.inr(latest.close);

    const returnEl = document.getElementById("latest-return");
    returnEl.textContent = fmt.pct(latest.daily_return);
    returnEl.className = "return " + (latest.daily_return >= 0 ? "positive" : "negative");
  } catch (err) {
    console.error("Failed to load data:", err);
  }
}
// === Load summary stats ===
async function loadSummary() {
  try {
    const url = `${API_BASE}/summary/${currentSymbol}`;
    const s = await fetchJSON(url);

    document.getElementById("stat-high").textContent = fmt.inr(s.high_52w);
    document.getElementById("stat-low").textContent = fmt.inr(s.low_52w);
    document.getElementById("stat-avg").textContent = fmt.inr(s.avg_close_52w);
    document.getElementById("stat-vol").textContent =
      s.current_volatility_30d ? `${s.current_volatility_30d.toFixed(1)}%` : "—";
    document.getElementById("stat-distance").textContent = `${s.distance_from_52w_high_pct.toFixed(2)}%`;
  } catch (err) {
    console.error("Failed to load summary:", err);
  }
}

// === Render Chart.js line chart ===
function renderChart(labels, closes, ma7, predValues) {
  const ctx = document.getElementById("price-chart").getContext("2d");

  if (chartInstance) chartInstance.destroy();

  // Pad close and MA arrays with nulls so they align with the longer label array
  const paddedCloses = [...closes, ...new Array(labels.length - closes.length).fill(null)];
  const paddedMa7 = [...ma7, ...new Array(labels.length - ma7.length).fill(null)];

  const datasets = [
    {
      label: "Close Price (₹)",
      data: paddedCloses,
      borderColor: "#1e3a8a",
      backgroundColor: "rgba(30, 58, 138, 0.08)",
      borderWidth: 2,
      fill: true,
      tension: 0.25,
      pointRadius: 0,
      pointHoverRadius: 5,
      spanGaps: false,
    },
    {
      label: "7-day Moving Avg",
      data: paddedMa7,
      borderColor: "#f59e0b",
      borderWidth: 1.5,
      borderDash: [5, 5],
      fill: false,
      tension: 0.25,
      pointRadius: 0,
      spanGaps: false,
    }
  ];

  // Add prediction line if available
  if (predValues && predValues.length > 0) {
    datasets.push({
      label: "🔮 Predicted (next 7 days)",
      data: predValues,
      borderColor: "#dc2626",
      borderWidth: 2,
      borderDash: [8, 4],
      fill: false,
      tension: 0,
      pointRadius: 3,
      pointBackgroundColor: "#dc2626",
      spanGaps: false,
    });
  }

  chartInstance = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", labels: { font: { size: 12 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${fmt.inr(ctx.parsed.y)}`
          }
        }
      },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
        y: {
          ticks: {
            font: { size: 10 },
            callback: (val) => `₹${val.toLocaleString("en-IN")}`
          },
          grid: { color: "#f1f5f9" }
        }
      }
    }
  });
}
// === Time range buttons ===
document.querySelectorAll(".range-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentDays = parseInt(btn.dataset.days);
    if (currentSymbol) loadStockData();
  });
});

// === Boot ===
loadCompanies();