import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  Building2,
  CheckCircle2,
  Clock3,
  Flame,
  Gauge,
  HardHat,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Siren,
  Users,
  Wrench,
} from "lucide-react";

import {
  getDashboardSummary,
  getEmergencyResponse,
  getOperationsSummary,
  getPlantMap,
  getRiskEvents,
  getWorkerSafety,
} from "../api/riskApi";

interface RiskEvent {
  id: number;
  created_at: string;
  plant_id: string;
  zone_id: string;
  equipment_id: string;
  sensor_id: string;
  risk_score: number;
  risk_level: string;
  predicted_event: string;
  explanation: string;
  contributing_factors: string;
  recommended_action: string;
  requires_acknowledgement: boolean;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
}

interface DashboardSummary {
  active_incidents: number;
  active_alerts: number;
  active_permits: number;
  active_maintenance_orders: number;
  workers_inside: number;
  ppe_compliance_percentage: number;
  latest_risk_event: {
    id: number;
    plant_id: string;
    zone_id: string;
    equipment_id: string;
    risk_score: number;
    risk_level: string;
    predicted_event: string;
    created_at: string;
  } | null;
}

interface PlantMapResponse {
  total_zones: number;
  critical_zones: number;
  zones: Array<{
    zone_name: string;
    latest_risk_score: number;
    latest_risk_level: string;
    workers_inside: number;
  }>;
}

interface WorkerSafetyResponse {
  total_workers_inside: number;
  ppe_compliant_workers: number;
  ppe_non_compliant_workers: number;
  ppe_unverified_workers: number;
}

interface PermitSummary {
  total_permits: number;
  active_permits: number;
  expired_permits: number;
  upcoming_permits: number;
  closed_permits: number;
  cancelled_permits: number;
  high_risk_permits: number;
  hot_work_permits: number;
  confined_space_permits: number;
  isolation_issues: number;
  gas_test_issues: number;
}

interface MaintenanceSummary {
  total_maintenance_orders: number;
  scheduled_maintenance: number;
  in_progress_maintenance: number;
  paused_maintenance: number;
  completed_maintenance: number;
  overdue_maintenance: number;
  critical_maintenance: number;
  machines_under_maintenance: number;
  lockout_tagout_pending: number;
}

interface OperationsResponse {
  permit_summary: PermitSummary;
  maintenance_summary: MaintenanceSummary;
}

interface EmergencyResponse {
  total_response_actions: number;
  active_emergencies: number;
  pending_actions: number;
  in_progress_actions: number;
  completed_actions: number;
  verified_actions: number;
  critical_actions: number;
  overdue_actions: number;
  mandatory_pending_actions: number;
  responders_assigned: number;
}

interface Recommendation {
  title: string;
  description: string;
  severity: "critical" | "warning" | "success" | "info";
}

interface SystemHealthItem {
  name: string;
  status: "Healthy" | "Warning" | "Critical";
  description: string;
}

function Risk() {
  const [riskEvents, setRiskEvents] = useState<RiskEvent[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [plantMap, setPlantMap] = useState<PlantMapResponse | null>(null);
  const [workers, setWorkers] = useState<WorkerSafetyResponse | null>(null);
  const [operations, setOperations] = useState<OperationsResponse | null>(null);
  const [emergency, setEmergency] = useState<EmergencyResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadRiskData = useCallback(async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const [
        riskResponse,
        dashboardResponse,
        plantMapResponse,
        workerResponse,
        operationsResponse,
        emergencyResponse,
      ] = await Promise.all([
        getRiskEvents(),
        getDashboardSummary(),
        getPlantMap(),
        getWorkerSafety(),
        getOperationsSummary(),
        getEmergencyResponse(),
      ]);

      setRiskEvents(Array.isArray(riskResponse) ? riskResponse : []);
      setDashboard(dashboardResponse);
      setPlantMap(plantMapResponse);
      setWorkers(workerResponse);
      setOperations(operationsResponse);
      setEmergency(emergencyResponse);
    } catch (err) {
      console.error("Risk Intelligence API error:", err);
      setError("Unable to load risk intelligence information.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadRiskData();

    const intervalId = window.setInterval(() => {
      loadRiskData();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, [loadRiskData]);

  const latestRisk = useMemo(() => {
    if (riskEvents.length === 0) {
      return null;
    }

    return [...riskEvents].sort(
      (first, second) =>
        new Date(second.created_at).getTime() -
        new Date(first.created_at).getTime(),
    )[0];
  }, [riskEvents]);

  const riskBreakdown = useMemo(() => {
    const ppeCompliance = dashboard?.ppe_compliance_percentage ?? 100;

    const workerRisk = Math.min(
      100,
      Math.round(
        (workers?.ppe_non_compliant_workers ?? 0) * 25 +
          (workers?.ppe_unverified_workers ?? 0) * 15 +
          Math.max(0, 100 - ppeCompliance) * 0.4,
      ),
    );

    const permitSummary = operations?.permit_summary;

    const permitRisk = Math.min(
      100,
      (permitSummary?.expired_permits ?? 0) * 35 +
        (permitSummary?.high_risk_permits ?? 0) * 25 +
        (permitSummary?.isolation_issues ?? 0) * 25 +
        (permitSummary?.gas_test_issues ?? 0) * 25,
    );

    const maintenanceSummary = operations?.maintenance_summary;

    const maintenanceRisk = Math.min(
      100,
      (maintenanceSummary?.critical_maintenance ?? 0) * 25 +
        (maintenanceSummary?.overdue_maintenance ?? 0) * 30 +
        (maintenanceSummary?.lockout_tagout_pending ?? 0) * 30 +
        (maintenanceSummary?.machines_under_maintenance ?? 0) * 10,
    );

    const incidentRisk = Math.min(
      100,
      (dashboard?.active_incidents ?? 0) * 40 +
        (dashboard?.active_alerts ?? 0) * 20,
    );

    const zoneRisk = Math.min(
      100,
      (plantMap?.critical_zones ?? 0) * 40 +
        Math.max(
          0,
          ...(plantMap?.zones ?? []).map(
            (zone) => zone.latest_risk_score ?? 0,
          ),
        ),
    );

    const emergencyRisk = Math.min(
      100,
      (emergency?.active_emergencies ?? 0) * 40 +
        (emergency?.critical_actions ?? 0) * 25 +
        (emergency?.overdue_actions ?? 0) * 20 +
        (emergency?.mandatory_pending_actions ?? 0) * 20,
    );

    return {
      workers: workerRisk,
      permits: permitRisk,
      maintenance: maintenanceRisk,
      incidents: incidentRisk,
      plantSafety: zoneRisk,
      emergency: emergencyRisk,
    };
  }, [dashboard, emergency, operations, plantMap, workers]);

  const overallRiskScore = useMemo(() => {
    if (latestRisk) {
      return Math.round(
        latestRisk.risk_score * 0.5 +
          riskBreakdown.workers * 0.1 +
          riskBreakdown.permits * 0.1 +
          riskBreakdown.maintenance * 0.1 +
          riskBreakdown.incidents * 0.08 +
          riskBreakdown.plantSafety * 0.08 +
          riskBreakdown.emergency * 0.04,
      );
    }

    return Math.round(
      riskBreakdown.workers * 0.18 +
        riskBreakdown.permits * 0.18 +
        riskBreakdown.maintenance * 0.18 +
        riskBreakdown.incidents * 0.16 +
        riskBreakdown.plantSafety * 0.2 +
        riskBreakdown.emergency * 0.1,
    );
  }, [latestRisk, riskBreakdown]);

  const overallRiskLevel = useMemo(() => {
    if (overallRiskScore >= 80) {
      return "critical";
    }

    if (overallRiskScore >= 60) {
      return "high";
    }

    if (overallRiskScore >= 30) {
      return "medium";
    }

    return "low";
  }, [overallRiskScore]);

  const recommendations = useMemo<Recommendation[]>(() => {
    const items: Recommendation[] = [];

    if (latestRisk?.risk_level === "critical") {
      items.push({
        title: "Critical risk event detected",
        description:
          latestRisk.recommended_action ||
          "Immediately isolate the affected zone and begin emergency assessment.",
        severity: "critical",
      });
    }

    if ((operations?.permit_summary.expired_permits ?? 0) > 0) {
      items.push({
        title: "Expired work permit detected",
        description:
          "Stop work under expired permits and complete permit renewal before operations continue.",
        severity: "critical",
      });
    }

    if ((operations?.permit_summary.high_risk_permits ?? 0) > 0) {
      items.push({
        title: "High-risk permit requires supervision",
        description:
          "Verify gas testing, isolation and PPE controls before hazardous work begins.",
        severity: "warning",
      });
    }

    if ((workers?.ppe_unverified_workers ?? 0) > 0) {
      items.push({
        title: "Worker PPE verification pending",
        description: `Verify PPE for ${
          workers?.ppe_unverified_workers ?? 0
        } worker(s) before allowing entry into hazardous areas.`,
        severity: "warning",
      });
    }

    if ((operations?.maintenance_summary.critical_maintenance ?? 0) > 0) {
      items.push({
        title: "Critical equipment maintenance recorded",
        description:
          "Continue post-maintenance monitoring and verify equipment performance before full operation.",
        severity: "warning",
      });
    }

    if ((emergency?.active_emergencies ?? 0) > 0) {
      items.push({
        title: "Emergency response is active",
        description:
          "Track assigned responders and complete all mandatory emergency actions.",
        severity: "critical",
      });
    }

    if (
      (dashboard?.active_incidents ?? 0) === 0 &&
      (dashboard?.active_alerts ?? 0) === 0
    ) {
      items.push({
        title: "No active incidents or alerts",
        description:
          "Continue live sensor monitoring and routine safety inspections.",
        severity: "success",
      });
    }

    if (items.length === 0) {
      items.push({
        title: "Plant conditions are stable",
        description:
          "No immediate risks were detected. Continue standard safety monitoring.",
        severity: "success",
      });
    }

    return items;
  }, [dashboard, emergency, latestRisk, operations, workers]);

  const systemHealth = useMemo<SystemHealthItem[]>(() => {
    const getStatus = (
      criticalCondition: boolean,
      warningCondition: boolean,
    ): "Healthy" | "Warning" | "Critical" => {
      if (criticalCondition) {
        return "Critical";
      }

      if (warningCondition) {
        return "Warning";
      }

      return "Healthy";
    };

    return [
      {
        name: "Workers & PPE",
        status: getStatus(
          (workers?.ppe_non_compliant_workers ?? 0) > 0,
          (workers?.ppe_unverified_workers ?? 0) > 0,
        ),
        description: `${
          dashboard?.ppe_compliance_percentage ?? 0
        }% PPE compliance`,
      },
      {
        name: "Incidents",
        status: getStatus(
          (dashboard?.active_incidents ?? 0) > 0,
          (dashboard?.active_alerts ?? 0) > 0,
        ),
        description: `${dashboard?.active_incidents ?? 0} active incidents`,
      },
      {
        name: "Permits",
        status: getStatus(
          (operations?.permit_summary.expired_permits ?? 0) > 0,
          (operations?.permit_summary.high_risk_permits ?? 0) > 0,
        ),
        description: `${
          operations?.permit_summary.active_permits ?? 0
        } currently active`,
      },
      {
        name: "Maintenance",
        status: getStatus(
          (operations?.maintenance_summary.overdue_maintenance ?? 0) > 0 ||
            (operations?.maintenance_summary.lockout_tagout_pending ?? 0) > 0,
          (operations?.maintenance_summary.critical_maintenance ?? 0) > 0,
        ),
        description: `${
          operations?.maintenance_summary.completed_maintenance ?? 0
        } completed orders`,
      },
      {
        name: "Emergency",
        status: getStatus(
          (emergency?.active_emergencies ?? 0) > 0,
          (emergency?.pending_actions ?? 0) > 0,
        ),
        description: `${emergency?.pending_actions ?? 0} pending actions`,
      },
      {
        name: "Plant Safety",
        status: getStatus(
          (plantMap?.critical_zones ?? 0) > 0 ||
            latestRisk?.risk_level === "critical",
          riskBreakdown.plantSafety >= 30,
        ),
        description: `${plantMap?.critical_zones ?? 0} critical zones`,
      },
    ];
  }, [
    dashboard,
    emergency,
    latestRisk,
    operations,
    plantMap,
    riskBreakdown.plantSafety,
    workers,
  ]);

  const contributingFactors = useMemo(() => {
    if (!latestRisk?.contributing_factors) {
      return [];
    }

    return latestRisk.contributing_factors
      .split("|")
      .map((factor) => factor.trim())
      .filter(Boolean);
  }, [latestRisk]);

  const formatDate = (value?: string | null) => {
    if (!value) {
      return "Not available";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Invalid date";
    }

    return date.toLocaleString();
  };

  const formatText = (value?: string) => {
    if (!value) {
      return "Unknown";
    }

    return value
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading risk intelligence...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Risk Intelligence</h2>
          <p>
            Unified industrial risk analysis, prioritization and safety
            recommendations
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadRiskData(true)}
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

      <section className="risk-overview-grid">
        <article
          className={`risk-score-card risk-score-${overallRiskLevel}`}
        >
          <div className="risk-score-header">
            <div>
              <span>Overall Plant Risk</span>
              <h3>{formatText(overallRiskLevel)}</h3>
            </div>

            <ShieldAlert size={34} />
          </div>

          <div className="risk-score-value">
            <strong>{overallRiskScore}</strong>
            <span>/100</span>
          </div>

          <div className="risk-score-track">
            <div
              className="risk-score-progress"
              style={{ width: `${Math.min(overallRiskScore, 100)}%` }}
            />
          </div>

          <p>
            Calculated from live risk events, PPE, permits, maintenance,
            incidents and emergency response.
          </p>
        </article>

        <article className="dashboard-card latest-risk-card">
          <div className="card-heading">
            <div>
              <h3>Latest Risk Event</h3>
              <p>Most recent safety-engine assessment</p>
            </div>

            {latestRisk && (
              <span
                className={`latest-risk-level latest-risk-${latestRisk.risk_level}`}
              >
                {formatText(latestRisk.risk_level)}
              </span>
            )}
          </div>

          {latestRisk ? (
            <>
              <div className="latest-risk-main">
                <div>
                  <span>Risk score</span>
                  <strong>{latestRisk.risk_score}/100</strong>
                </div>

                <div>
                  <span>Zone</span>
                  <strong>{latestRisk.zone_id}</strong>
                </div>

                <div>
                  <span>Equipment</span>
                  <strong>{latestRisk.equipment_id}</strong>
                </div>
              </div>

              <div className="latest-risk-prediction">
                <AlertTriangle size={18} />

                <div>
                  <span>Predicted Event</span>
                  <p>{latestRisk.predicted_event}</p>
                </div>
              </div>

              <div className="latest-risk-footer">
                <span>{formatDate(latestRisk.created_at)}</span>

                <span>
                  {latestRisk.acknowledged
                    ? `Acknowledged by ${
                        latestRisk.acknowledged_by ?? "Safety team"
                      }`
                    : "Acknowledgement required"}
                </span>
              </div>
            </>
          ) : (
            <div className="empty-state compact-empty-state">
              <CheckCircle2 size={32} />
              <h3>No risk events</h3>
              <p>No risk event has been recorded.</p>
            </div>
          )}
        </article>
      </section>

      <section className="risk-breakdown-section dashboard-card">
        <div className="card-heading">
          <div>
            <h3>Risk Breakdown</h3>
            <p>Risk contribution from each operational subsystem</p>
          </div>
        </div>

        <div className="risk-breakdown-grid">
          {[
            {
              label: "Workers",
              value: riskBreakdown.workers,
              icon: Users,
            },
            {
              label: "Permits",
              value: riskBreakdown.permits,
              icon: Flame,
            },
            {
              label: "Maintenance",
              value: riskBreakdown.maintenance,
              icon: Wrench,
            },
            {
              label: "Incidents",
              value: riskBreakdown.incidents,
              icon: Siren,
            },
            {
              label: "Plant Safety",
              value: riskBreakdown.plantSafety,
              icon: Building2,
            },
            {
              label: "Emergency",
              value: riskBreakdown.emergency,
              icon: ShieldAlert,
            },
          ].map((item) => {
            const Icon = item.icon;

            return (
              <article className="risk-breakdown-item" key={item.label}>
                <div className="risk-breakdown-title">
                  <span>
                    <Icon size={17} />
                    {item.label}
                  </span>

                  <strong>{item.value}</strong>
                </div>

                <div className="risk-breakdown-track">
                  <div
                    className={`risk-breakdown-progress ${
                      item.value >= 70
                        ? "risk-progress-critical"
                        : item.value >= 40
                          ? "risk-progress-warning"
                          : "risk-progress-safe"
                    }`}
                    style={{ width: `${Math.min(item.value, 100)}%` }}
                  />
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section className="risk-content-layout">
        <div className="risk-primary-column">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>AI Safety Recommendations</h3>
                <p>Prioritized actions generated from current plant data</p>
              </div>

              <Bot size={21} />
            </div>

            <div className="risk-recommendation-list">
              {recommendations.map((recommendation, index) => (
                <div
                  className={`risk-recommendation risk-recommendation-${recommendation.severity}`}
                  key={`${recommendation.title}-${index}`}
                >
                  <div className="risk-recommendation-icon">
                    {recommendation.severity === "critical" ? (
                      <AlertTriangle size={19} />
                    ) : recommendation.severity === "success" ? (
                      <CheckCircle2 size={19} />
                    ) : (
                      <ShieldAlert size={19} />
                    )}
                  </div>

                  <div>
                    <strong>{recommendation.title}</strong>
                    <p>{recommendation.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Contributing Factors</h3>
                <p>Conditions responsible for the latest risk score</p>
              </div>

              <Gauge size={21} />
            </div>

            {contributingFactors.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <CheckCircle2 size={32} />
                <h3>No contributing factors</h3>
                <p>No dangerous operating condition was identified.</p>
              </div>
            ) : (
              <div className="risk-factor-list">
                {contributingFactors.map((factor, index) => (
                  <div className="risk-factor-item" key={`${factor}-${index}`}>
                    <span>{index + 1}</span>
                    <p>{factor}</p>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Risk Event History</h3>
                <p>Recent safety-engine detections</p>
              </div>

              <Clock3 size={21} />
            </div>

            {riskEvents.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <Activity size={32} />
                <h3>No risk history</h3>
                <p>Risk events will appear here when detected.</p>
              </div>
            ) : (
              <div className="risk-history-list">
                {riskEvents.map((risk) => (
                  <div className="risk-history-item" key={risk.id}>
                    <div
                      className={`risk-history-indicator risk-history-${risk.risk_level}`}
                    />

                    <div className="risk-history-content">
                      <div>
                        <strong>{formatText(risk.risk_level)} Risk</strong>
                        <span>{formatDate(risk.created_at)}</span>
                      </div>

                      <p>{risk.predicted_event}</p>

                      <div className="risk-history-meta">
                        <span>
                          <MapPin size={13} />
                          {risk.zone_id}
                        </span>

                        <span>
                          <Wrench size={13} />
                          {risk.equipment_id}
                        </span>

                        <span>
                          <Gauge size={13} />
                          {risk.risk_score}/100
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>

        <aside className="risk-side-column">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>High Priority Items</h3>
                <p>Issues requiring immediate attention</p>
              </div>
            </div>

            <div className="priority-risk-list">
              {latestRisk?.risk_level === "critical" && (
                <div className="priority-risk-item priority-critical">
                  <ShieldAlert size={17} />
                  <span>Critical risk in {latestRisk.zone_id}</span>
                </div>
              )}

              {(operations?.permit_summary.expired_permits ?? 0) > 0 && (
                <div className="priority-risk-item priority-critical">
                  <Flame size={17} />
                  <span>
                    {operations?.permit_summary.expired_permits} expired
                    permit(s)
                  </span>
                </div>
              )}

              {(workers?.ppe_unverified_workers ?? 0) > 0 && (
                <div className="priority-risk-item priority-warning">
                  <HardHat size={17} />
                  <span>
                    {workers?.ppe_unverified_workers} PPE verification pending
                  </span>
                </div>
              )}

              {(operations?.maintenance_summary.critical_maintenance ?? 0) >
                0 && (
                <div className="priority-risk-item priority-warning">
                  <Wrench size={17} />
                  <span>Critical maintenance requires monitoring</span>
                </div>
              )}

              {(emergency?.pending_actions ?? 0) > 0 && (
                <div className="priority-risk-item priority-warning">
                  <Siren size={17} />
                  <span>{emergency?.pending_actions} emergency actions pending</span>
                </div>
              )}

              {overallRiskScore < 30 && (
                <div className="priority-risk-item priority-safe">
                  <CheckCircle2 size={17} />
                  <span>No immediate high-priority issue</span>
                </div>
              )}
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>System Health</h3>
                <p>Operational status of each safety module</p>
              </div>
            </div>

            <div className="system-health-list">
              {systemHealth.map((item) => (
                <div className="system-health-item" key={item.name}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.description}</span>
                  </div>

                  <span
                    className={`system-health-status system-health-${item.status.toLowerCase()}`}
                  >
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Live Plant Snapshot</h3>
                <p>Current operational safety metrics</p>
              </div>
            </div>

            <div className="risk-snapshot-list">
              <div>
                <Users size={17} />
                <span>Workers inside</span>
                <strong>{dashboard?.workers_inside ?? 0}</strong>
              </div>

              <div>
                <HardHat size={17} />
                <span>PPE compliance</span>
                <strong>{dashboard?.ppe_compliance_percentage ?? 0}%</strong>
              </div>

              <div>
                <Flame size={17} />
                <span>Active permits</span>
                <strong>{dashboard?.active_permits ?? 0}</strong>
              </div>

              <div>
                <Siren size={17} />
                <span>Active incidents</span>
                <strong>{dashboard?.active_incidents ?? 0}</strong>
              </div>

              <div>
                <Wrench size={17} />
                <span>Active maintenance</span>
                <strong>{dashboard?.active_maintenance_orders ?? 0}</strong>
              </div>

              <div>
                <Building2 size={17} />
                <span>Critical zones</span>
                <strong>{plantMap?.critical_zones ?? 0}</strong>
              </div>
            </div>
          </article>
        </aside>
      </section>
    </div>
  );
}

export default Risk;