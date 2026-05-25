import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

function ForecastPage() {

  const [forecast, setForecast] = useState([]);

  useEffect(() => {

    fetchForecast();

  }, []);

  const fetchForecast = async () => {

    try {

      const response = await axios.get(
        "http://127.0.0.1:8000/forecast"
      );

      setForecast(response.data.forecast);

    } catch (error) {

      console.log(error);
    }
  };

  return (

    <Layout>

      <h1 style={{
        fontSize: "36px",
        marginBottom: "30px",
        color: "white"
      }}>
        Forecast Analytics
      </h1>

      <div style={{
        marginTop: "20px",
        background: "#1e293b",
        padding: "30px",
        borderRadius: "16px",
        boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
      }}>

        <LineChart
          width={900}
          height={400}
          data={forecast}
        >

          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

          <XAxis
            dataKey="ds"
            stroke="#cbd5e1"
          />

          <YAxis stroke="#cbd5e1" />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="yhat"
            stroke="#38bdf8"
            strokeWidth={3}
          />

        </LineChart>

      </div>

    </Layout>
  );
}

export default ForecastPage;