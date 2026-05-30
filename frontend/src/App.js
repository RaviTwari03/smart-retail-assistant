import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard    from "./pages/Dashboard";
import ForecastPage from "./pages/ForecastPage";
import AssistantPage from "./pages/AssistantPage";
import InventoryPage from "./pages/InventoryPage";
import AnomalyPage  from "./pages/AnomalyPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<Dashboard />}     />
        <Route path="/forecast"  element={<ForecastPage />}  />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/anomaly"   element={<AnomalyPage />}   />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
