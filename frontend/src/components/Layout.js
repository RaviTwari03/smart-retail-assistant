import { NavLink } from "react-router-dom";

const NAV_LINKS = [
  { to: "/",          label: "Dashboard" },
  { to: "/forecast",  label: "Forecast"  },
  { to: "/anomaly",   label: "Anomaly"   },
  { to: "/assistant", label: "Assistant" },
  { to: "/inventory", label: "Inventory" },
];

function Layout({ children }) {
  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      backgroundColor: "#020617",
      color: "white",
      fontFamily: "'Inter', 'Segoe UI', sans-serif"
    }}>

      {/* ── Sidebar ── */}
      <div style={{
        width: "210px",
        minWidth: "210px",
        backgroundColor: "#0f172a",
        padding: "32px 24px",
        borderRight: "1px solid #1e293b",
        display: "flex",
        flexDirection: "column"
      }}>
        <div style={{ marginBottom: "40px" }}>
          <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#38bdf8", margin: 0 }}>
            Retail AI
          </h2>
          <p style={{ color: "#475569", fontSize: "11px", marginTop: "4px" }}>Smart Assistant</p>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              style={({ isActive }) => ({
                color: isActive ? "#38bdf8" : "#94a3b8",
                textDecoration: "none",
                fontSize: "15px",
                fontWeight: isActive ? "600" : "400",
                padding: "10px 14px",
                borderRadius: "8px",
                background: isActive ? "#1e3a5f" : "transparent",
                transition: "all 0.15s"
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* ── Page content ── */}
      <div style={{ flex: 1, padding: "40px 48px", overflowY: "auto" }}>
        {children}
      </div>

    </div>
  );
}

export default Layout;
