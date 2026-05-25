import { Link } from "react-router-dom";

function Layout({ children }) {

  return (

    <div style={{
      display: "flex",
      minHeight: "100vh",
      backgroundColor: "#020617",
      color: "white"
    }}>

      {/* Sidebar */}

      <div style={{
        width: "220px",
        backgroundColor: "#0f172a",
        padding: "30px"
      }}>

        <h2>Retail AI</h2>

        <div style={{
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          marginTop: "40px"
        }}>

          <Link
            to="/"
            style={linkStyle}
          >
            Dashboard
          </Link>

          <Link
            to="/forecast"
            style={linkStyle}
          >
            Forecast
          </Link>

          <Link
            to="/assistant"
            style={linkStyle}
          >
            Assistant
          </Link>

          <Link
            to="/inventory"
            style={linkStyle}
          >
            Inventory
          </Link>

        </div>

      </div>

      {/* Page Content */}

      <div style={{
        flex: 1,
        padding: "40px"
      }}>

        {children}

      </div>

    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontSize: "18px"
};

export default Layout;