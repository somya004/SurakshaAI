import { useEffect, useState } from "react";
import {
  AlertTriangle,
  FileCheck2,
  MapPin,
  ShieldAlert,
  Users,
  Wrench,
} from "lucide-react";

import { getPlantMap } from "../api/plantMapApi";

interface ZoneGeometry {
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface PlantZone {
  id: number;
  plant_id: string;
  zone_id: string;
  zone_name: string;
  zone_type: string;
  floor_level: number;
  geometry: ZoneGeometry | null;
  latitude: number | null;
  longitude: number | null;
  description: string | null;
  zone_status: string;
  latest_risk_score: number;
  latest_risk_level: string;
  latest_risk_time: string | null;
  total_risk_events: number;
  active_incidents: number;
  active_alerts: number;
  workers_inside: number;
  active_permits: number;
  active_maintenance_orders: number;
  equipment_under_maintenance: string[];
}

interface PlantMapResponse {
  plant_id: string | null;
  floor_level: number | null;
  total_zones: number;
  critical_zones: number;
  high_risk_zones: number;
  warning_zones: number;
  maintenance_zones: number;
  normal_zones: number;
  zones: PlantZone[];
}

function PlantMap() {
  const [plantMap, setPlantMap] = useState<PlantMapResponse | null>(null);
  const [selectedZone, setSelectedZone] = useState<PlantZone | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPlantMap = async () => {
    try {
      setError("");
      const data = await getPlantMap();
      setPlantMap(data);

      if (data.zones?.length > 0) {
        setSelectedZone((current) => current ?? data.zones[0]);
      }
    } catch (err) {
      console.error("Plant map API error:", err);
      setError("Unable to load plant map data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlantMap();

    const intervalId = window.setInterval(loadPlantMap, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading plant map...</h2>
      </div>
    );
  }

  if (error || !plantMap) {
    return (
      <div className="simple-page">
        <h2>Plant map unavailable</h2>
        <p>{error}</p>

        <button className="retry-button" type="button" onClick={loadPlantMap}>
          Retry
        </button>
      </div>
    );
  }

  const getZoneClass = (zone: PlantZone) => {
    const level = zone.latest_risk_level?.toLowerCase();
    const status = zone.zone_status?.toLowerCase();

    if (level === "critical") return "zone-critical";
    if (level === "high") return "zone-high";
    if (level === "medium" || status === "warning") return "zone-warning";
    if (status === "maintenance") return "zone-maintenance";

    return "zone-normal";
  };

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Plant Safety Map</h2>
          <p>Live zone-level risk, worker and operational monitoring</p>
        </div>

        <div className="system-status">
          <span />
          {plantMap.total_zones} zone connected
        </div>
      </div>

      <section className="plant-summary-grid">
        <article className="plant-summary-card">
          <p>Total Zones</p>
          <strong>{plantMap.total_zones}</strong>
        </article>

        <article className="plant-summary-card critical-summary">
          <p>Critical Zones</p>
          <strong>{plantMap.critical_zones}</strong>
        </article>

        <article className="plant-summary-card warning-summary">
          <p>Warning Zones</p>
          <strong>{plantMap.warning_zones}</strong>
        </article>

        <article className="plant-summary-card normal-summary">
          <p>Normal Zones</p>
          <strong>{plantMap.normal_zones}</strong>
        </article>
      </section>

      <section className="plant-map-layout">
        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Interactive Plant Layout</h3>
              <p>Select a zone to inspect its live safety status</p>
            </div>
          </div>

          <div className="plant-canvas">
            {plantMap.zones.length === 0 ? (
              <div className="empty-state">No plant zones are available.</div>
            ) : (
              plantMap.zones.map((zone) => (
                <button
                  key={zone.id}
                  type="button"
                  className={`plant-zone-box ${getZoneClass(zone)} ${
                    selectedZone?.id === zone.id ? "selected-zone" : ""
                  }`}
                  onClick={() => setSelectedZone(zone)}
                >
                  <MapPin size={22} />

                  <strong>{zone.zone_name}</strong>

                  <span>{zone.zone_id}</span>

                  <small>
                    Risk: {zone.latest_risk_score} |{" "}
                    {zone.latest_risk_level}
                  </small>
                </button>
              ))
            )}
          </div>
        </article>

        <article className="dashboard-card zone-detail-card">
          <div className="card-heading">
            <div>
              <h3>Zone Details</h3>
              <p>Selected zone information</p>
            </div>
          </div>

          {selectedZone ? (
            <div className="zone-detail-content">
              <div className="zone-title-row">
                <div>
                  <h3>{selectedZone.zone_name}</h3>
                  <p>{selectedZone.description || "No description available"}</p>
                </div>

                <span
                  className={`risk-badge ${selectedZone.latest_risk_level.toLowerCase()}`}
                >
                  {selectedZone.latest_risk_level}
                </span>
              </div>

              <div className="zone-info-grid">
                <div>
                  <span>Plant ID</span>
                  <strong>{selectedZone.plant_id}</strong>
                </div>

                <div>
                  <span>Zone ID</span>
                  <strong>{selectedZone.zone_id}</strong>
                </div>

                <div>
                  <span>Zone Type</span>
                  <strong>{selectedZone.zone_type}</strong>
                </div>

                <div>
                  <span>Floor Level</span>
                  <strong>{selectedZone.floor_level}</strong>
                </div>

                <div>
                  <span>Risk Score</span>
                  <strong>{selectedZone.latest_risk_score}</strong>
                </div>

                <div>
                  <span>Status</span>
                  <strong>{selectedZone.zone_status}</strong>
                </div>
              </div>

              <div className="zone-metric-list">
                <div className="zone-metric-item">
                  <Users size={20} />
                  <span>Workers Inside</span>
                  <strong>{selectedZone.workers_inside}</strong>
                </div>

                <div className="zone-metric-item">
                  <AlertTriangle size={20} />
                  <span>Active Incidents</span>
                  <strong>{selectedZone.active_incidents}</strong>
                </div>

                <div className="zone-metric-item">
                  <ShieldAlert size={20} />
                  <span>Active Alerts</span>
                  <strong>{selectedZone.active_alerts}</strong>
                </div>

                <div className="zone-metric-item">
                  <FileCheck2 size={20} />
                  <span>Active Permits</span>
                  <strong>{selectedZone.active_permits}</strong>
                </div>

                <div className="zone-metric-item">
                  <Wrench size={20} />
                  <span>Maintenance Orders</span>
                  <strong>{selectedZone.active_maintenance_orders}</strong>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">Select a zone to view details.</div>
          )}
        </article>
      </section>
    </div>
  );
}

export default PlantMap;