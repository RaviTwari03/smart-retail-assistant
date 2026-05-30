import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import API_BASE from "../api";

/* ── Status badge ────────────────────────────────────────────── */
function StatusBadge({ status }) {
  const colors = {
    Critical: { bg: "#450a0a", text: "#fca5a5", border: "#dc2626" },
    Warning:  { bg: "#451a03", text: "#fcd34d", border: "#d97706" },
    Stable:   { bg: "#052e16", text: "#86efac", border: "#16a34a" },
    Low:      { bg: "#451a03", text: "#fcd34d", border: "#d97706" },
    Healthy:  { bg: "#052e16", text: "#86efac", border: "#16a34a" },
  };
  const c = colors[status] || { bg: "#1e293b", text: "#94a3b8", border: "#475569" };
  return (
    <span style={{
      background: c.bg,
      color: c.text,
      border: `1px solid ${c.border}`,
      borderRadius: "6px",
      padding: "3px 10px",
      fontSize: "12px",
      fontWeight: "600"
    }}>
      {status}
    </span>
  );
}

/* ── KPI card ────────────────────────────────────────────────── */
function KPICard({ label, value, color = "#38bdf8" }) {
  return (
    <div style={{
      background: "#1e293b",
      borderRadius: "12px",
      padding: "20px",
      minWidth: "160px",
      borderTop: `3px solid ${color}`
    }}>
      <p style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>{label}</p>
      <p style={{ color: "white", fontSize: "24px", fontWeight: "700", margin: 0 }}>{value ?? "—"}</p>
    </div>
  );
}

function InventoryPage() {
  const [stores, setStores] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchInventory(); }, []);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`${API_BASE}/analytics/inventory`);
      setStores(res.data.store_inventory_status || []);
      setKpis(res.data.kpis || null);
      setAnomaly(res.data.anomaly_summary || null);
    } catch (err) {
      console.error("Inventory fetch error:", err);
      setError("Could not load inventory data. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <h1 style={{ fontSize: "32px", marginBottom: "8px" }}>Inventory Analytics</h1>
      <p style={{ color: "#64748b", marginBottom: "28px" }}>Store-level stock status from Walmart dataset</p>

      {loading && <p style={{ color: "#64748b" }}>Loading inventory…</p>}

      {error && (
        <div style={{ background: "#450a0a", border: "1px solid #dc2626", borderRadius: "10px", padding: "16px", marginBottom: "24px", color: "#fca5a5" }}>
          ⚠️ {error}
        </div>
      )}

      {/* KPI row */}
      {!loading && !error && kpis && (
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "28px" }}>
          <KPICard label="Total Stores" value={kpis.total_stores} color="#38bdf8" />
          <KPICard label="Critical" value={kpis.critical_stock_stores} color="#f87171" />
          <KPICard label="Warning" value={kpis.warning_stock_stores} color="#f59e0b" />
          <KPICard label="Stable" value={kpis.stable_stock_stores} color="#34d399" />
          {anomaly && (
            <KPICard
              label="Anomaly Rate"
              value={`${anomaly.anomaly_rate_pct}%`}
              color="#a78bfa"
            />
          )}
        </div>
      )}

      {/* Store table */}
      {!loading && !error && stores.length > 0 && (
        <div style={{ background: "#1e293b", borderRadius: "14px", overflow: "hidden", boxShadow: "0 4px 16px rgba(0,0,0,0.4)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0f172a" }}>
                {["Store ID", "Avg Weekly Sales", "Sales Volatility", "Status"].map(h => (
                  <th key={h} style={{
                    padding: "14px 16px",
                    textAlign: "left",
                    color: "#64748b",
                    fontSize: "12px",
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
              {stores.map((store, i) => (
                <tr
                  key={store.store_id}
                  style={{ background: i % 2 === 0 ? "#1e293b" : "#162032" }}
                >
                  <td style={cell}><strong>Store {store.store_id}</strong></td>
                  <td style={cell}>${Number(store.avg_weekly_sales).toLocaleString()}</td>
                  <td style={cell}>${Number(store.sales_volatility).toLocaleString()}</td>
                  <td style={cell}><StatusBadge status={store.stock_status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && stores.length === 0 && (
        <div style={{ background: "#1e293b", padding: "40px", borderRadius: "14px", textAlign: "center", color: "#64748b" }}>
          No inventory data available.
        </div>
      )}
    </Layout>
  );
}

const cell = {
  padding: "13px 16px",
  color: "#cbd5e1",
  fontSize: "14px",
  borderBottom: "1px solid #1e3a5f"
};

export default InventoryPage;
