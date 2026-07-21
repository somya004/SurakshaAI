import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  FileCheck2,
  HardHat,
  RefreshCw,
  ShieldAlert,
  Siren,
  Users,
  Wrench,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getAnalyticsData } from "../api/analyticsApi";

interface DashboardSummary {
  active_incidents: number;
  active_alerts: number;
  active_permits: number;
  active_maintenance_orders: number;
  workers_inside: number;
  ppe_compliance_percentage: number;
  latest_risk_event: {
    risk_score: number;
    risk_level: string;
  } | null;
}

interface RiskEvent {
  id: number;
  created_at: string;
  risk_score: number;
  risk_level: string;
  zone_id: string;
  equipment_id: string;
  predicted_event: string;
}

interface WorkerSafety {
  total_workers_inside?: number;
  ppe_compliant_workers?: number;
  ppe_non_compliant_workers?: number;
  ppe_unverified_workers?: number;
}

interface PlantZone {
  zone_id?: string;
  zone_name?: string;
  latest_risk_score?: number;
  risk_score?: number;
  latest_risk_level?: string;
  risk_level?: string;
  workers_inside?: number;
}

interface PlantMap {
  total_zones?: number;
  critical_zones?: number;
  zones?: PlantZone[];
}

interface PermitSummary {
  total_permits?: number;
  active_permits?: number;
  expired_permits?: number;
  upcoming_permits?: number;
  closed_permits?: number;
  cancelled_permits?: number;
  high_risk_permits?: number;
}

interface MaintenanceSummary {
  total_maintenance_orders?: number;
  scheduled_maintenance?: number;
  in_progress_maintenance?: number;
  paused_maintenance?: number;
  completed_maintenance?: number;
  overdue_maintenance?: number;
  critical_maintenance?: number;
}

interface Operations {
  permit_summary?: PermitSummary;
  maintenance_summary?: MaintenanceSummary;
}

interface AnalyticsResponse {
  dashboard: DashboardSummary;
  risks: RiskEvent[];
  workerSafety: WorkerSafety;
  plantMap: PlantMap;
  operations: Operations;
  incidents: unknown[];
  alerts: unknown[];
}

const chartColors = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  safe: "#14b8a6",
  info: "#3b82f6",
  muted: "#64748b",
  purple: "#8b5cf6",
};

function Analytics() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadAnalytics = useCallback(async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const response = await getAnalyticsData();

      setData({
        dashboard: response.dashboard ?? {},
        risks: Array.isArray(response.risks) ? response.risks : [],
        workerSafety: response.workerSafety ?? {},
        plantMap: response.plantMap ?? {},
        operations: response.operations ?? {},
        incidents: Array.isArray(response.incidents)
          ? response.incidents
          : [],
        alerts: Array.isArray(response.alerts) ? response.alerts : [],
      });
    } catch (err) {
      console.error("Analytics API error:", err);
      setError("Unable to load analytics information.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();

    const intervalId = window.setInterval(() => {
      loadAnalytics();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, [loadAnalytics]);

  const riskDistribution = useMemo(() => {
    const result = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    };

    data?.risks.forEach((risk) => {
      const level = risk.risk_level?.toLowerCase();

      if (level === "critical") {
        result.critical += 1;
      } else if (level === "high") {
        result.high += 1;
      } else if (level === "medium") {
        result.medium += 1;
      } else {
        result.low += 1;
      }
    });

    return [
      {
        name: "Critical",
        value: result.critical,
        color: chartColors.critical,
      },
      {
        name: "High",
        value: result.high,
        color: chartColors.high,
      },
      {
        name: "Medium",
        value: result.medium,
        color: chartColors.medium,
      },
      {
        name: "Low",
        value: result.low,
        color: chartColors.low,
      },
    ];
  }, [data]);

  const permitDistribution = useMemo(() => {
    const summary = data?.operations?.permit_summary;

    return [
      {
        name: "Active",
        value: summary?.active_permits ?? 0,
        color: chartColors.info,
      },
      {
        name: "Expired",
        value: summary?.expired_permits ?? 0,
        color: chartColors.critical,
      },
      {
        name: "Upcoming",
        value: summary?.upcoming_permits ?? 0,
        color: chartColors.medium,
      },
      {
        name: "Closed",
        value: summary?.closed_permits ?? 0,
        color: chartColors.low,
      },
      {
        name: "Cancelled",
        value: summary?.cancelled_permits ?? 0,
        color: chartColors.muted,
      },
    ];
  }, [data]);

  const maintenanceDistribution = useMemo(() => {
    const summary = data?.operations?.maintenance_summary;

    return [
      {
        name: "Scheduled",
        value: summary?.scheduled_maintenance ?? 0,
      },
      {
        name: "In Progress",
        value: summary?.in_progress_maintenance ?? 0,
      },
      {
        name: "Paused",
        value: summary?.paused_maintenance ?? 0,
      },
      {
        name: "Completed",
        value: summary?.completed_maintenance ?? 0,
      },
      {
        name: "Overdue",
        value: summary?.overdue_maintenance ?? 0,
      },
      {
        name: "Critical",
        value: summary?.critical_maintenance ?? 0,
      },
    ];
  }, [data]);

  const ppeDistribution = useMemo(() => {
    const compliant =
      data?.workerSafety?.ppe_compliant_workers ??
      Math.round(
        ((data?.dashboard?.workers_inside ?? 0) *
          (data?.dashboard?.ppe_compliance_percentage ?? 0)) /
          100,
      );

    const nonCompliant =
      data?.workerSafety?.ppe_non_compliant_workers ?? 0;

    const totalWorkers =
      data?.workerSafety?.total_workers_inside ??
      data?.dashboard?.workers_inside ??
      0;

    const unverified =
      data?.workerSafety?.ppe_unverified_workers ??
      Math.max(0, totalWorkers - compliant - nonCompliant);

    return [
      {
        name: "Compliant",
        value: compliant,
        color: chartColors.low,
      },
      {
        name: "Non-Compliant",
        value: nonCompliant,
        color: chartColors.critical,
      },
      {
        name: "Unverified",
        value: unverified,
        color: chartColors.medium,
      },
    ];
  }, [data]);

  const zoneRiskData = useMemo(() => {
    const zones = data?.plantMap?.zones ?? [];

    return zones.map((zone, index) => ({
      name:
        zone.zone_name ??
        zone.zone_id ??
        `Zone ${index + 1}`,
      risk:
        zone.latest_risk_score ??
        zone.risk_score ??
        0,
      workers: zone.workers_inside ?? 0,
    }));
  }, [data]);

  const incidentAlertData = useMemo(() => {
    return [
      {
        name: "Incidents",
        value:
          data?.incidents.length ??
          data?.dashboard?.active_incidents ??
          0,
      },
      {
        name: "Alerts",
        value:
          data?.alerts.length ??
          data?.dashboard?.active_alerts ??
          0,
      },
    ];
  }, [data]);

  const riskTrendData = useMemo(() => {
    return [...(data?.risks ?? [])]
      .sort(
        (first, second) =>
          new Date(first.created_at).getTime() -
          new Date(second.created_at).getTime(),
      )
      .map((risk) => ({
        date: new Date(risk.created_at).toLocaleDateString(undefined, {
          day: "2-digit",
          month: "short",
        }),
        score: risk.risk_score,
        level: risk.risk_level,
      }));
  }, [data]);

  const currentRiskScore =
    data?.dashboard?.latest_risk_event?.risk_score ??
    data?.risks?.[0]?.risk_score ??
    0;

  const criticalZones =
    data?.plantMap?.critical_zones ??
    zoneRiskData.filter((zone) => zone.risk >= 80).length;

  const hasChartData = (items: Array<{ value: number }>) =>
    items.some((item) => item.value > 0);

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading analytics...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Analytics Dashboard</h2>
          <p>
            Visual analysis of plant safety, permits, workers,
            maintenance and risk trends
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadAnalytics(true)}
        >
          <RefreshCw
            size={17}
            className={refreshing ? "refresh-icon-spinning" : ""}
          />

          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="page-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      <section className="analytics-kpi-grid">
        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-risk">
            <ShieldAlert size={21} />
          </div>

          <div>
            <span>Current Risk Score</span>
            <strong>{currentRiskScore}/100</strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-workers">
            <Users size={21} />
          </div>

          <div>
            <span>Workers Inside</span>
            <strong>{data?.dashboard?.workers_inside ?? 0}</strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-ppe">
            <HardHat size={21} />
          </div>

          <div>
            <span>PPE Compliance</span>
            <strong>
              {data?.dashboard?.ppe_compliance_percentage ?? 0}%
            </strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-permit">
            <FileCheck2 size={21} />
          </div>

          <div>
            <span>Active Permits</span>
            <strong>{data?.dashboard?.active_permits ?? 0}</strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-maintenance">
            <Wrench size={21} />
          </div>

          <div>
            <span>Active Maintenance</span>
            <strong>
              {data?.dashboard?.active_maintenance_orders ?? 0}
            </strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-zone">
            <BarChart3 size={21} />
          </div>

          <div>
            <span>Critical Zones</span>
            <strong>{criticalZones}</strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-incident">
            <Siren size={21} />
          </div>

          <div>
            <span>Active Incidents</span>
            <strong>{data?.dashboard?.active_incidents ?? 0}</strong>
          </div>
        </article>

        <article className="analytics-kpi-card">
          <div className="analytics-kpi-icon analytics-icon-alert">
            <AlertTriangle size={21} />
          </div>

          <div>
            <span>Active Alerts</span>
            <strong>{data?.dashboard?.active_alerts ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="analytics-chart-grid">
        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>Risk Level Distribution</h3>
              <p>Recorded risks grouped by severity</p>
            </div>
          </div>

          {hasChartData(riskDistribution) ? (
            <div className="analytics-chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={88}
                    paddingAngle={3}
                  >
                    {riskDistribution.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.color}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="analytics-empty-chart">
              No risk records available
            </div>
          )}
        </article>

        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>Permit Status Distribution</h3>
              <p>Current permit lifecycle overview</p>
            </div>
          </div>

          {hasChartData(permitDistribution) ? (
            <div className="analytics-chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={permitDistribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={88}
                  >
                    {permitDistribution.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.color}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="analytics-empty-chart">
              No permit records available
            </div>
          )}
        </article>

        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>PPE Compliance</h3>
              <p>Worker PPE verification status</p>
            </div>
          </div>

          {hasChartData(ppeDistribution) ? (
            <div className="analytics-chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ppeDistribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={58}
                    outerRadius={88}
                    paddingAngle={4}
                  >
                    {ppeDistribution.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.color}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="analytics-empty-chart">
              No worker PPE records available
            </div>
          )}
        </article>

        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>Incident and Alert Comparison</h3>
              <p>Current incident and alert counts</p>
            </div>
          </div>

          <div className="analytics-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={incidentAlertData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1f3045"
                />

                <XAxis
                  dataKey="name"
                  stroke="#718399"
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  allowDecimals={false}
                  stroke="#718399"
                  tick={{ fontSize: 11 }}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  fill={chartColors.info}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="analytics-wide-grid">
        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>Maintenance Status</h3>
              <p>Work orders grouped by operational status</p>
            </div>
          </div>

          <div className="analytics-chart-container analytics-large-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={maintenanceDistribution}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1f3045"
                />

                <XAxis
                  dataKey="name"
                  stroke="#718399"
                  tick={{ fontSize: 10 }}
                />

                <YAxis
                  allowDecimals={false}
                  stroke="#718399"
                  tick={{ fontSize: 10 }}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  fill={chartColors.purple}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="dashboard-card analytics-chart-card">
          <div className="card-heading">
            <div>
              <h3>Zone Risk Comparison</h3>
              <p>Latest calculated risk score for each plant zone</p>
            </div>
          </div>

          {zoneRiskData.length > 0 ? (
            <div className="analytics-chart-container analytics-large-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={zoneRiskData}
                  layout="vertical"
                  margin={{
                    top: 5,
                    right: 20,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#1f3045"
                  />

                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    stroke="#718399"
                    tick={{ fontSize: 10 }}
                  />

                  <YAxis
                    type="category"
                    dataKey="name"
                    width={75}
                    stroke="#718399"
                    tick={{ fontSize: 10 }}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="risk"
                    fill={chartColors.critical}
                    radius={[0, 6, 6, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="analytics-empty-chart analytics-large-chart">
              No plant zone records available
            </div>
          )}
        </article>
      </section>

      <section className="dashboard-card analytics-risk-trend-card">
        <div className="card-heading">
          <div>
            <h3>Risk Score Trend</h3>
            <p>
              Risk score history based on safety-engine detections
            </p>
          </div>

          <Activity size={21} />
        </div>

        {riskTrendData.length > 0 ? (
          <div className="analytics-chart-container analytics-trend-chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={riskTrendData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1f3045"
                />

                <XAxis
                  dataKey="date"
                  stroke="#718399"
                  tick={{ fontSize: 10 }}
                />

                <YAxis
                  domain={[0, 100]}
                  stroke="#718399"
                  tick={{ fontSize: 10 }}
                />

                <Tooltip />
                <Legend />

                <Line
                  type="monotone"
                  dataKey="score"
                  name="Risk Score"
                  stroke={chartColors.critical}
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="analytics-empty-chart analytics-trend-chart">
            Risk trend will appear after risk events are recorded
          </div>
        )}
      </section>
    </div>
  );
}

export default Analytics;