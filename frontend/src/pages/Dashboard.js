import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import API_BASE from "../api";

function StatCard({ title, value, color = "#38bdf8", icon }) {
  return (
    <div style={{
      background: "#1e293b",
      padding: "24px",
      borderRadius: "14px",
      width: "220px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
      borderLeft: `4px solid ${color}`
    }}>
      <p style={{ color: "#94a3b8", fontSize: "13px", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {title}
      </p>
      <p style={{ fontSize: "30px", fontWeight: "700", color: "white", margin: 0 }}>
        {value ?? <span style={{ color: "#475569" }}>—</span>}
      </p>
    </div>
  );
}

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchMetrics(); }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`${API_BASE}/dashboard-metrics`);
      setMetrics(res.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError("Could not reach the backend. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <h1 style={{ fontSize: "32px", marginBottom: "8px" }}>Smart Retail Assistant</h1>
      <p style={{ color: "#64748b", marginBottom: "32px" }}>Live KPI overview</p>

      {loading && <p style={{ color: "#64748b" }}>Loading metrics…</p>}

      {error && (
        <div style={{ background: "#450a0a", border: "1px solid #dc2626", borderRadius: "10px", padding: "16px", marginBottom: "24px", color: "#fca5a5" }}>
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && metrics && (
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <StatCard
            title="Total Revenue"
            value={metrics.total_revenue != null ? `$${Number(metrics.total_revenue).toLocaleString()}` : null}
            color="#38bdf8"
          />
          <StatCard
            title="Inventory Alerts"
            value={metrics.inventory_alerts ?? null}
            color="#f59e0b"
          />
          <StatCard
            title="Sales Trend"
            value={metrics.sales_trend ?? null}
            color="#34d399"
          />
        </div>
      )}
    </Layout>
  );
}

export default Dashboard;
