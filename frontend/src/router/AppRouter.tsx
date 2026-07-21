import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Dashboard from "../pages/Dashboard";
import PlantMap from "../pages/PlantMap";
import Incidents from "../pages/Incidents";
import Emergency from "../pages/Emergency";
import Workers from "../pages/Workers";
import Permits from "../pages/Permits";
import Maintenance from "../pages/Maintenance";
import Risk from "../pages/Risk";
import Analytics from "../pages/Analytics";
import CommandCenter from "../pages/CommandCenter";


function AppRouter() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />

        <div className="main-container">
          <Header />

          <main className="page-content">
            <Routes>
              <Route path="/" element={<Navigate to="/command-center" replace />} />
              <Route path="/command-center" element={<CommandCenter />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/plant-map" element={<PlantMap />} />
              <Route path="/risk" element={<Risk />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/emergency" element={<Emergency />} />
              <Route path="/workers" element={<Workers />} />
              <Route path="/permits" element={<Permits />} />
              <Route path="/maintenance" element={<Maintenance />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default AppRouter;