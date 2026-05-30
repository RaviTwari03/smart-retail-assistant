import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import API_BASE from "../api";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

/* ── Custom tooltip ─────────────────────────────────────────── */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#0f172a",
      border: "1px solid #334155",
      borderRadius: "8px",
      padding: "12px",
      minWidth: "180px"
    }}>
      <p style={{ color: "#94a3b8", marginBottom: "8px", fontSize: "12px" }}>{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color, margin: "3px 0", fontSize: "13px" }}>
          {p.name}: <strong>${Number(p.value).toLocaleString()}</strong>
        </p>
      ))}
    </div>
  );
}

/* ── KPI pill ────────────────────────────────────────────────── */
function KPIPill({ label, value, color = "#38bdf8" }) {
  return (
    <div style={{
      background: "#1e293b",
      borderRadius: "10px",
      padding: "16px 20px",
      minWidth: "150px",
      borderTop: `3px solid ${color}`
    }}>
      <p style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>
        {label}
      </p>
      <p style={{ color: "white", fontSize: "20px", fontWeight: "700", margin: 0 }}>{value}</p>
    </div>
  );
}

function ForecastPage() {
  const [chartData, setChartData] = useState([]);
  const [kpis, setKpis]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  useEffect(() => { fetchForecast(); }, []);

  const fetchForecast = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use /forecast directly — always works, no analytics dependency
      const res  = await axios.get(`${API_BASE}/forecast`);
      const raw  = res.data?.forecast ?? [];

      if (!raw.length) {
        setError("Forecast returned empty data.");
        return;
      }

      // Map API keys (ds / yhat / yhat_lower / yhat_upper) → chart keys
      const mapped = raw.map((p) => ({
        date:        p.ds,
        forecast:    p.yhat,
        lower_bound: p.yhat_lower,
        upper_bound: p.yhat_upper,
      }));

      setChartData(mapped);

      // Derive KPIs from the data
      const values     = mapped.map((p) => p.forecast);
      const peak       = mapped.reduce((a, b) => (b.forecast > a.forecast ? b : a));
      const low        = mapped.reduce((a, b) => (b.forecast < a.forecast ? b : a));
      const changePct  = (((values[values.length - 1] - values[0]) / values[0]) * 100).toFixed(1);
      const trend      = changePct > 2 ? "Upward ↑" : changePct < -2 ? "Downward ↓" : "Stable →";

      setKpis({
        next_week:   values[0],
        peak_value:  peak.forecast,
        peak_date:   peak.date,
        avg_value:   values.reduce((a, b) => a + b, 0) / values.length,
        trend,
        change_pct:  changePct,
      });

    } catch (err) {
      console.error("Forecast error:", err);
      setError("Could not load forecast. Make sure the backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const trendColor = kpis?.trend?.includes("Upward")
    ? "#34d399"
    : kpis?.trend?.includes("Downward")
    ? "#f87171"
    : "#f59e0b";

  return (
    <Layout>
      <h1 style={{ fontSize: "32px", marginBottom: "6px" }}>Forecast Analytics</h1>
      <p style={{ color: "#64748b", marginBottom: "28px" }}>Prophet 7-day sales prediction</p>

      {/* Loading */}
      {loading && (
        <p style={{ color: "#64748b" }}>Loading forecast…</p>
      )}

      {/* Error */}
      {!loading && error && (
        <div style={{
          background: "#450a0a",
          border: "1px solid #dc2626",
          borderRadius: "10px",
          padding: "16px",
          color: "#fca5a5",
          marginBottom: "24px"
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* KPI row */}
      {!loading && !error && kpis && (
        <div style={{ display: "flex", gap: "14px", flexWrap: "wrap", marginBottom: "28px" }}>
          <KPIPill label="Next Week"    value={`$${Number(kpis.next_week).toLocaleString()}`}  color="#38bdf8" />
          <KPIPill label="Peak Forecast" value={`$${Number(kpis.peak_value).toLocaleString()}`} color="#a78bfa" />
          <KPIPill label="Avg Forecast"  value={`$${Number(kpis.avg_value.toFixed(0)).toLocaleString()}`} color="#34d399" />
          <KPIPill label="Trend"         value={kpis.trend}                                     color={trendColor} />
          <KPIPill label="7-Day Change"  value={`${kpis.change_pct > 0 ? "+" : ""}${kpis.change_pct}%`} color={trendColor} />
        </div>
      )}

      {/* Chart */}
      {!loading && !error && chartData.length > 0 && (
        <div style={{
          background: "#1e293b",
          padding: "28px",
          borderRadius: "16px",
          boxShadow: "0 4px 16px rgba(0,0,0,0.4)"
        }}>
          <h3 style={{ color: "#94a3b8", marginBottom: "20px", fontWeight: "500", fontSize: "15px" }}>
            7-Day Sales Forecast with Confidence Bands
          </h3>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                tickFormatter={(v) => `$${(v / 1_000_000).toFixed(1)}M`}
                width={70}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: "#94a3b8", paddingTop: "12px" }} />

              {/* Confidence band — lower */}
              <Line
                type="monotone"
                dataKey="lower_bound"
                name="Lower Bound"
                stroke="#334155"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
              />
              {/* Main forecast line */}
              <Line
                type="monotone"
                dataKey="forecast"
                name="Forecast"
                stroke="#38bdf8"
                strokeWidth={3}
                dot={{ fill: "#38bdf8", r: 5 }}
                activeDot={{ r: 7 }}
              />
              {/* Confidence band — upper */}
              <Line
                type="monotone"
                dataKey="upper_bound"
                name="Upper Bound"
                stroke="#334155"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Layout>
  );
}

export default ForecastPage;
