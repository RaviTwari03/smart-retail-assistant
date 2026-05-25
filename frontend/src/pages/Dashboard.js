import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";

function Dashboard() {

  const [metrics, setMetrics] = useState({});

  useEffect(() => {

    fetchMetrics();

  }, []);

  const fetchMetrics = async () => {

    try {

      const response = await axios.get(
        "http://127.0.0.1:8000/dashboard-metrics"
      );

      setMetrics(response.data);

    } catch (error) {

      console.log(error);
    }
  };

  return (

    <Layout>

      <h1 style={{
        fontSize: "36px",
        marginBottom: "30px"
      }}>
        Smart Retail Assistant
      </h1>

      <div style={{
        display: "flex",
        gap: "20px",
        flexWrap: "wrap"
      }}>

        {/* Revenue Card */}

        <div style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          width: "250px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
        }}>

          <h3>Total Revenue</h3>

          <p style={{
            fontSize: "28px",
            fontWeight: "bold",
            marginTop: "10px"
          }}>
            ${metrics.total_revenue}
          </p>

        </div>

        {/* Inventory Card */}

        <div style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          width: "250px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
        }}>

          <h3>Inventory Alerts</h3>

          <p style={{
            fontSize: "28px",
            fontWeight: "bold",
            marginTop: "10px"
          }}>
            {metrics.inventory_alerts}
          </p>

        </div>

        {/* Sales Trend Card */}

        <div style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          width: "250px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
        }}>

          <h3>Sales Trend</h3>

          <p style={{
            fontSize: "28px",
            fontWeight: "bold",
            marginTop: "10px"
          }}>
            {metrics.sales_trend}
          </p>

        </div>

      </div>

    </Layout>
  );
}

export default Dashboard;