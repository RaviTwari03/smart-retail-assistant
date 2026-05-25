import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import ForecastPage from "./pages/ForecastPage";
import AssistantPage from "./pages/AssistantPage";
import InventoryPage from "./pages/InventoryPage";

function App() {

  return (

    <BrowserRouter>

      <Routes>

        <Route path="/" element={<Dashboard />} />

        <Route path="/forecast" element={<ForecastPage />} />

        <Route path="/assistant" element={<AssistantPage />} />

        <Route path="/inventory" element={<InventoryPage />} />

      </Routes>

    </BrowserRouter>
  );
}

export default App;