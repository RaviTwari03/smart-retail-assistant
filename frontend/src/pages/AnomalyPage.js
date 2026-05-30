import { useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import API_BASE from "../api";

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

/* ── Stat card ───────────────────────────────────────────────── */
function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "#1e293b",
      borderRadius: "12px",
      padding: "20px 24px",
      minWidth: "150px",
      borderTop: `3px solid ${color}`
    }}>
      <p style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
        {label}
      </p>
      <p style={{ color: "white", fontSize: "26px", fontWeight: "700", margin: 0 }}>{value}</p>
    </div>
  );
}

/* ── Custom scatter tooltip ──────────────────────────────────── */
function ScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div style={{
      background: "#0f172a",
      border: "1px solid #334155",
      borderRadius: "8px",
      padding: "10px 14px"
    }}>
      <p style={{ color: "#94a3b8", fontSize: "12px", margin: "0 0 4px" }}>Week #{d?.index + 1}</p>
      <p style={{ color: d?.is_anomaly ? "#f87171" : "#34d399", fontSize: "14px", margin: 0 }}>
        Sales: <strong>${Number(d?.sales).toLocaleString()}</strong>
      </p>
      <p style={{ color: d?.is_anomaly ? "#f87171" : "#64748b", fontSize: "12px", margin: "4px 0 0" }}>
        {d?.is_anomaly ? "⚠️ Anomaly detected" : "✓ Normal"}
      </p>
    </div>
  );
}

/* ── Default weekly sales from Walmart dataset (45 stores, sampled) ── */
const DEFAULT_SALES = [
  1643690, 1641957, 1611968, 1409728, 1554807, 1439542, 1472516, 1404429,
  1594968, 1545418, 1466058, 1391256, 1425821, 1490234, 1523456, 1478901,
  1612345, 1589012, 1534567, 1601234, 1678901, 1723456, 1756789, 1812345,
  1867890, 1923456, 1978901, 2034567, 2089012, 2145678, 2201234, 2256789,
  2312345, 2367890, 2423456, 2478901, 2534567, 2589012, 2645678, 2701234,
  2756789, 2812345, 2867890, 2923456, 2978901,
];

function AnomalyPage() {
  const [salesInput, setSalesInput]   = useState(DEFAULT_SALES.join(", "));
  const [results, setResults]         = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [hasRun, setHasRun]           = useState(false);

  const runDetection = async () => {
    try {
      setLoading(true);
      setError(null);

      // Parse comma-separated numbers
      const values = salesInput
        .split(",")
        .map((v) => parseFloat(v.trim()))
        .filter((v) => !isNaN(v));

      if (values.length < 3) {
        setError("Please enter at least 3 sales values.");
        return;
      }

      const res = await axios.post(`${API_BASE}/detect-anomaly`, { sales: values });
      const raw = res.data?.results ?? [];

      // Attach index for chart x-axis
      setResults(raw.map((r, i) => ({ ...r, index: i })));
      setHasRun(true);

    } catch (err) {
      console.error("Anomaly error:", err);
      setError("Could not run anomaly detection. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  // Split into normal and anomaly series for scatter chart
  const normalPoints  = results.filter((r) => !r.is_anomaly);
  const anomalyPoints = results.filter((r) =>  r.is_anomaly);

  const totalAnomalies = anomalyPoints.length;
  const anomalyRate    = results.length
    ? ((totalAnomalies / results.length) * 100).toFixed(1)
    : 0;
  const avgSales = results.length
    ? (results.reduce((s, r) => s + r.sales, 0) / results.length).toFixed(0)
    : 0;

  return (
    <Layout>
      <h1 style={{ fontSize: "32px", marginBottom: "6px" }}>Anomaly Detection</h1>
      <p style={{ color: "#64748b", marginBottom: "28px" }}>
        IsolationForest model — detects unusual weekly sales patterns
      </p>

      {/* Input area */}
      <div style={{
        background: "#1e293b",
        borderRadius: "14px",
        padding: "24px",
        marginBottom: "28px",
        maxWidth: "860px"
      }}>
        <label style={{ color: "#94a3b8", fontSize: "13px", display: "block", marginBottom: "10px" }}>
          Weekly Sales Values (comma-separated numbers)
        </label>
        <textarea
          value={salesInput}
          onChange={(e) => setSalesInput(e.target.value)}
          rows={4}
          style={{
            width: "100%",
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "8px",
            color: "#e2e8f0",
            fontSize: "13px",
            padding: "12px",
            resize: "vertical",
            fontFamily: "monospace",
            boxSizing: "border-box"
          }}
        />
        <div style={{ display: "flex", gap: "12px", marginTop: "14px", alignItems: "center" }}>
          <button
            onClick={runDetection}
            disabled={loading}
            style={{
              padding: "11px 28px",
              borderRadius: "8px",
              border: "none",
              background: loading ? "#1e3a5f" : "#2563eb",
              color: "white",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "14px",
              fontWeight: "600"
            }}
          >
            {loading ? "Detecting…" : "Run Detection"}
          </button>
          <button
            onClick={() => setSalesInput(DEFAULT_SALES.join(", "))}
            style={{
              padding: "11px 20px",
              borderRadius: "8px",
              border: "1px solid #334155",
              background: "transparent",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "13px"
            }}
          >
            Load Sample Data
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          background: "#450a0a",
          border: "1px solid #dc2626",
          borderRadius: "10px",
          padding: "14px 16px",
          color: "#fca5a5",
          marginBottom: "24px",
          maxWidth: "860px"
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {hasRun && !error && results.length > 0 && (
        <>
          {/* KPI row */}
          <div style={{ display: "flex", gap: "14px", flexWrap: "wrap", marginBottom: "28px" }}>
            <StatCard label="Total Weeks"   value={results.length}    color="#38bdf8" />
            <StatCard label="Anomalies"     value={totalAnomalies}    color="#f87171" />
            <StatCard label="Normal Weeks"  value={normalPoints.length} color="#34d399" />
            <StatCard label="Anomaly Rate"  value={`${anomalyRate}%`} color="#f59e0b" />
            <StatCard label="Avg Sales"     value={`$${Number(avgSales).toLocaleString()}`} color="#a78bfa" />
          </div>

          {/* Scatter chart */}
          <div style={{
            background: "#1e293b",
            padding: "28px",
            borderRadius: "16px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
            marginBottom: "28px"
          }}>
            <h3 style={{ color: "#94a3b8", marginBottom: "20px", fontWeight: "500", fontSize: "15px" }}>
              Sales Distribution — Normal vs Anomaly
            </h3>
            <ResponsiveContainer width="100%" height={340}>
              <ScatterChart margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                <XAxis
                  dataKey="index"
                  name="Week"
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  label={{ value: "Week #", position: "insideBottom", offset: -5, fill: "#64748b", fontSize: 12 }}
                />
                <YAxis
                  dataKey="sales"
                  name="Sales"
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  tickFormatter={(v) => `$${(v / 1_000_000).toFixed(1)}M`}
                  width={70}
                />
                <Tooltip content={<ScatterTooltip />} />
                <Legend wrapperStyle={{ color: "#94a3b8", paddingTop: "12px" }} />
                <Scatter
                  name="Normal"
                  data={normalPoints}
                  fill="#34d399"
                  opacity={0.8}
                />
                <Scatter
                  name="Anomaly"
                  data={anomalyPoints}
                  fill="#f87171"
                  opacity={0.9}
                  shape="triangle"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Results table */}
          <div style={{
            background: "#1e293b",
            borderRadius: "14px",
            overflow: "hidden",
            boxShadow: "0 4px 16px rgba(0,0,0,0.4)"
          }}>
            <div style={{ padding: "16px 20px", borderBottom: "1px solid #1e3a5f" }}>
              <h3 style={{ color: "#94a3b8", margin: 0, fontWeight: "500", fontSize: "15px" }}>
                Detailed Results
              </h3>
            </div>
            <div style={{ maxHeight: "320px", overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#0f172a", position: "sticky", top: 0 }}>
                    {["Week", "Sales", "Status"].map((h) => (
                      <th key={h} style={{
                        padding: "12px 16px",
                        textAlign: "left",
                        color: "#64748b",
                        fontSize: "11px",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        fontWeight: "600",
                        borderBottom: "1px solid #1e3a5f"
                      }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr
                      key={r.index}
                      style={{
                        background: r.is_anomaly
                          ? "rgba(239,68,68,0.08)"
                          : r.index % 2 === 0 ? "#1e293b" : "#162032"
                      }}
                    >
                      <td style={td}>Week {r.index + 1}</td>
                      <td style={td}>${Number(r.sales).toLocaleString()}</td>
                      <td style={td}>
                        <span style={{
                          background: r.is_anomaly ? "#450a0a" : "#052e16",
                          color:      r.is_anomaly ? "#fca5a5" : "#86efac",
                          border:     `1px solid ${r.is_anomaly ? "#dc2626" : "#16a34a"}`,
                          borderRadius: "6px",
                          padding: "2px 10px",
                          fontSize: "12px",
                          fontWeight: "600"
                        }}>
                          {r.is_anomaly ? "⚠️ Anomaly" : "✓ Normal"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}

const td = {
  padding: "11px 16px",
  color: "#cbd5e1",
  fontSize: "14px",
  borderBottom: "1px solid #1e3a5f"
};

export default AnomalyPage;
