import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BellRing,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import { getAlerts, getIncidents } from "../api/incidentsApi";

interface Incident {
  id?: number;
  incident_id?: string;
  title?: string;
  description?: string;
  severity?: string;
  status?: string;
  plant_id?: string;
  zone_id?: string;
  created_at?: string;
}

interface Alert {
  id?: number;
  alert_id?: string;
  title?: string;
  message?: string;
  severity?: string;
  status?: string;
  plant_id?: string;
  zone_id?: string;
  created_at?: string;
}

function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setError("");

      const [incidentData, alertData] = await Promise.all([
        getIncidents(),
        getAlerts(),
      ]);

      setIncidents(Array.isArray(incidentData) ? incidentData : []);
      setAlerts(Array.isArray(alertData) ? alertData : []);
    } catch (err) {
      console.error("Incidents page API error:", err);
      setError("Unable to load incidents and alerts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const intervalId = window.setInterval(loadData, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  const getSeverityClass = (severity?: string) => {
    const value = severity?.toLowerCase();

    if (value === "critical") return "critical";
    if (value === "high") return "high";
    if (value === "medium") return "medium";

    return "low";
  };

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading incidents and alerts...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Incidents & Alerts</h2>
          <p>Monitor and manage active industrial safety events</p>
        </div>

        <button className="refresh-button" type="button" onClick={loadData}>
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="page-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      <section className="incident-summary-grid">
        <article className="incident-summary-card">
          <div className="summary-icon incident-summary-icon">
            <AlertTriangle size={22} />
          </div>

          <div>
            <p>Total Incidents</p>
            <strong>{incidents.length}</strong>
          </div>
        </article>

        <article className="incident-summary-card">
          <div className="summary-icon alert-summary-icon">
            <BellRing size={22} />
          </div>

          <div>
            <p>Total Alerts</p>
            <strong>{alerts.length}</strong>
          </div>
        </article>

        <article className="incident-summary-card">
          <div className="summary-icon critical-summary-icon">
            <ShieldAlert size={22} />
          </div>

          <div>
            <p>Critical Events</p>
            <strong>
              {
                [...incidents, ...alerts].filter(
                  (item) => item.severity?.toLowerCase() === "critical",
                ).length
              }
            </strong>
          </div>
        </article>

        <article className="incident-summary-card">
          <div className="summary-icon resolved-summary-icon">
            <CheckCircle2 size={22} />
          </div>

          <div>
            <p>Resolved Incidents</p>
            <strong>
              {
                incidents.filter(
                  (item) => item.status?.toLowerCase() === "resolved",
                ).length
              }
            </strong>
          </div>
        </article>
      </section>

      <section className="incidents-layout">
        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Incident Records</h3>
              <p>All recorded industrial incidents</p>
            </div>
          </div>

          {incidents.length === 0 ? (
            <div className="empty-state">
              <AlertTriangle size={35} />
              <h3>No incidents found</h3>
              <p>Incident records will appear here when created.</p>
            </div>
          ) : (
            <div className="incident-list">
              {incidents.map((incident, index) => (
                <article
                  className="incident-record"
                  key={incident.id ?? incident.incident_id ?? index}
                >
                  <div className="record-header">
                    <div>
                      <h4>{incident.title ?? "Safety Incident"}</h4>
                      <p>
                        {incident.plant_id ?? "Unknown plant"} ·{" "}
                        {incident.zone_id ?? "Unknown zone"}
                      </p>
                    </div>

                    <span
                      className={`risk-badge ${getSeverityClass(
                        incident.severity,
                      )}`}
                    >
                      {incident.severity ?? "Unknown"}
                    </span>
                  </div>

                  <p className="record-description">
                    {incident.description ?? "No description available"}
                  </p>

                  <div className="record-footer">
                    <span>Status: {incident.status ?? "Unknown"}</span>
                    <span>
                      {incident.created_at
                        ? new Date(incident.created_at).toLocaleString()
                        : "No timestamp"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Active Alerts</h3>
              <p>Latest safety warnings and escalations</p>
            </div>
          </div>

          {alerts.length === 0 ? (
            <div className="empty-state">
              <BellRing size={35} />
              <h3>No alerts found</h3>
              <p>Alert records will appear here when generated.</p>
            </div>
          ) : (
            <div className="alert-record-list">
              {alerts.map((alert, index) => (
                <article
                  className="alert-record"
                  key={alert.id ?? alert.alert_id ?? index}
                >
                  <div className="record-header">
                    <div>
                      <h4>{alert.title ?? "Safety Alert"}</h4>
                      <p>
                        {alert.plant_id ?? "Unknown plant"} ·{" "}
                        {alert.zone_id ?? "Unknown zone"}
                      </p>
                    </div>

                    <span
                      className={`risk-badge ${getSeverityClass(
                        alert.severity,
                      )}`}
                    >
                      {alert.severity ?? "Unknown"}
                    </span>
                  </div>

                  <p className="record-description">
                    {alert.message ?? "No alert message available"}
                  </p>

                  <div className="record-footer">
                    <span>Status: {alert.status ?? "Unknown"}</span>
                    <span>
                      {alert.created_at
                        ? new Date(alert.created_at).toLocaleString()
                        : "No timestamp"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}

export default Incidents;