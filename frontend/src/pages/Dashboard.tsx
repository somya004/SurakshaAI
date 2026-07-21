import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  ShieldAlert,
  Users,
  Wrench,
} from "lucide-react";

import { getDashboardSummary } from "../api/dashboardApi";

interface RiskEvent {
  id: number;
  plant_id: string;
  zone_id: string;
  equipment_id: string;
  risk_score: number;
  risk_level: string;
  predicted_event: string;
  created_at: string;
}

interface DashboardSummary {
  active_incidents: number;
  active_alerts: number;
  active_permits: number;
  active_maintenance_orders: number;
  workers_inside: number;
  ppe_compliance_percentage: number;
  latest_risk_event: RiskEvent | null;
}

function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = async () => {
    try {
      setError("");
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error("Dashboard API error:", err);
      setError("Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();

    const intervalId = window.setInterval(loadDashboard, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading dashboard...</h2>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="simple-page">
        <h2>Dashboard data unavailable</h2>
        <p>{error}</p>

        <button className="retry-button" type="button" onClick={loadDashboard}>
          Retry
        </button>
      </div>
    );
  }

  const kpiData = [
    {
      title: "Workers Inside",
      value: summary.workers_inside,
      description: "Currently inside the plant",
      icon: Users,
      className: "blue",
    },
    {
      title: "Active Incidents",
      value: summary.active_incidents,
      description: "Open safety incidents",
      icon: AlertTriangle,
      className: "orange",
    },
    {
      title: "Active Alerts",
      value: summary.active_alerts,
      description: "Alerts requiring attention",
      icon: ShieldAlert,
      className: "red",
    },
    {
      title: "PPE Compliance",
      value: `${summary.ppe_compliance_percentage}%`,
      description: "Current worker compliance",
      icon: CheckCircle2,
      className: "green",
    },
  ];

  const riskLevel =
    summary.latest_risk_event?.risk_level?.toLowerCase() ?? "unknown";

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Industrial Safety Command Center</h2>
          <p>Real-time plant safety, risk and incident monitoring</p>
        </div>

        <div className="system-status">
          <span />
          Backend connected
        </div>
      </div>

      <section className="kpi-grid">
        {kpiData.map((item) => {
          const Icon = item.icon;

          return (
            <article className="kpi-card" key={item.title}>
              <div className={`kpi-icon ${item.className}`}>
                <Icon size={24} />
              </div>

              <div>
                <p>{item.title}</p>
                <h3>{item.value}</h3>
                <span>{item.description}</span>
              </div>
            </article>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-card large-card">
          <div className="card-heading">
            <div>
              <h3>Latest Compound Risk Event</h3>
              <p>Most recent risk detected by SurakshaAI</p>
            </div>

            <span className={`risk-badge ${riskLevel}`}>
              {summary.latest_risk_event?.risk_level ?? "No risk"}
            </span>
          </div>

          {summary.latest_risk_event ? (
            <div className="risk-event-panel">
              <div className="risk-score-section">
                <p>Risk Score</p>
                <strong>{summary.latest_risk_event.risk_score}</strong>
                <span>/ 100</span>
              </div>

              <div className="risk-details">
                <div>
                  <span>Plant</span>
                  <strong>{summary.latest_risk_event.plant_id}</strong>
                </div>

                <div>
                  <span>Zone</span>
                  <strong>{summary.latest_risk_event.zone_id}</strong>
                </div>

                <div>
                  <span>Equipment</span>
                  <strong>{summary.latest_risk_event.equipment_id}</strong>
                </div>

                <div>
                  <span>Detected</span>
                  <strong>
                    {new Date(
                      summary.latest_risk_event.created_at,
                    ).toLocaleString()}
                  </strong>
                </div>
              </div>

              <div className="predicted-event">
                <span>Predicted Event</span>
                <p>{summary.latest_risk_event.predicted_event}</p>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              No risk events are currently available.
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Operations Overview</h3>
              <p>Current operational activity</p>
            </div>
          </div>

          <div className="operations-list">
            <div className="operation-item">
              <div className="operation-icon permit-icon">
                <FileCheck2 size={21} />
              </div>

              <div>
                <p>Active Permits</p>
                <strong>{summary.active_permits}</strong>
              </div>
            </div>

            <div className="operation-item">
              <div className="operation-icon maintenance-icon">
                <Wrench size={21} />
              </div>

              <div>
                <p>Maintenance Orders</p>
                <strong>{summary.active_maintenance_orders}</strong>
              </div>
            </div>

            <div className="operation-item">
              <div className="operation-icon incident-icon">
                <AlertTriangle size={21} />
              </div>

              <div>
                <p>Active Incidents</p>
                <strong>{summary.active_incidents}</strong>
              </div>
            </div>

            <div className="operation-item">
              <div className="operation-icon alert-icon">
                <ShieldAlert size={21} />
              </div>

              <div>
                <p>Active Alerts</p>
                <strong>{summary.active_alerts}</strong>
              </div>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

export default Dashboard;