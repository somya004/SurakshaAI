import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  RefreshCw,
  ShieldAlert,
  Siren,
  Timer,
  UserRoundCheck,
} from "lucide-react";

import {
  getEmergencySummary,
  getResponseActions,
} from "../api/emergencyApi";

interface ResponseAction {
  id?: number;
  action_id?: string;
  incident_id?: string;
  action_type?: string;
  action_description?: string;
  priority?: string;
  status?: string;
  assigned_role?: string;
  assigned_to?: string;
  mandatory?: boolean;
  due_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  verified?: boolean;
  created_at?: string | null;
}

interface EmergencySummary {
  plant_id: string | null;
  zone_id: string | null;
  incident_id: string | null;
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
  assigned_roles_count: number;
  assigned_roles: string[];
  average_response_time_minutes: number | null;
  average_completion_time_minutes: number | null;
  actions: ResponseAction[];
}

function Emergency() {
  const [summary, setSummary] = useState<EmergencySummary | null>(null);
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadEmergencyData = async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const [summaryData, responseActionsData] = await Promise.all([
        getEmergencySummary(),
        getResponseActions(),
      ]);

      setSummary(summaryData);

      if (Array.isArray(responseActionsData)) {
        setActions(responseActionsData);
      } else if (Array.isArray(summaryData?.actions)) {
        setActions(summaryData.actions);
      } else {
        setActions([]);
      }
    } catch (err) {
      console.error("Emergency API error:", err);
      setError("Unable to load emergency response data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadEmergencyData();

    const intervalId = window.setInterval(() => {
      loadEmergencyData();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  const formatMinutes = (minutes: number | null | undefined) => {
    if (minutes === null || minutes === undefined) {
      return "N/A";
    }

    return `${minutes.toFixed(1)} min`;
  };

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

  const getPriorityClass = (priority?: string) => {
    const value = priority?.toLowerCase();

    if (value === "critical") return "emergency-critical";
    if (value === "high") return "emergency-high";
    if (value === "medium") return "emergency-medium";

    return "emergency-low";
  };

  const getStatusClass = (status?: string) => {
    const value = status?.toLowerCase();

    if (value === "completed") return "action-completed";
    if (value === "in_progress" || value === "in progress") {
      return "action-in-progress";
    }

    if (value === "verified") return "action-verified";

    return "action-pending";
  };

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading emergency response data...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Emergency Response</h2>
          <p>
            Monitor emergency events, response actions and assigned responders
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadEmergencyData(true)}
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

      <section className="emergency-summary-grid">
        <article className="emergency-summary-card">
          <div className="emergency-summary-icon active-emergency-icon">
            <Siren size={23} />
          </div>

          <div>
            <p>Active Emergencies</p>
            <strong>{summary?.active_emergencies ?? 0}</strong>
          </div>
        </article>

        <article className="emergency-summary-card">
          <div className="emergency-summary-icon pending-action-icon">
            <Clock3 size={23} />
          </div>

          <div>
            <p>Pending Actions</p>
            <strong>{summary?.pending_actions ?? 0}</strong>
          </div>
        </article>

        <article className="emergency-summary-card">
          <div className="emergency-summary-icon progress-action-icon">
            <Timer size={23} />
          </div>

          <div>
            <p>In Progress</p>
            <strong>{summary?.in_progress_actions ?? 0}</strong>
          </div>
        </article>

        <article className="emergency-summary-card">
          <div className="emergency-summary-icon completed-action-icon">
            <CheckCircle2 size={23} />
          </div>

          <div>
            <p>Completed Actions</p>
            <strong>{summary?.completed_actions ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="emergency-secondary-grid">
        <article className="emergency-small-card emergency-danger-card">
          <ShieldAlert size={20} />

          <div>
            <span>Critical Actions</span>
            <strong>{summary?.critical_actions ?? 0}</strong>
          </div>
        </article>

        <article className="emergency-small-card emergency-warning-card">
          <AlertTriangle size={20} />

          <div>
            <span>Overdue Actions</span>
            <strong>{summary?.overdue_actions ?? 0}</strong>
          </div>
        </article>

        <article className="emergency-small-card emergency-responder-card">
          <UserRoundCheck size={20} />

          <div>
            <span>Responders Assigned</span>
            <strong>{summary?.responders_assigned ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="emergency-layout">
        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Emergency Response Actions</h3>
              <p>Live emergency tasks and operational response status</p>
            </div>

            <span className="record-count">
              {summary?.total_response_actions ?? actions.length} actions
            </span>
          </div>

          {actions.length === 0 ? (
            <div className="empty-state emergency-empty-state">
              <Siren size={40} />
              <h3>No active response actions</h3>
              <p>
                Emergency actions will appear here when an incident requires a
                response.
              </p>
            </div>
          ) : (
            <div className="emergency-action-list">
              {actions.map((action, index) => (
                <article
                  className="emergency-action-card"
                  key={action.id ?? action.action_id ?? index}
                >
                  <div className="emergency-action-header">
                    <div>
                      <h4>
                        {action.action_type ??
                          action.action_description ??
                          "Emergency Response Action"}
                      </h4>

                      <p>
                        Incident: {action.incident_id ?? "Not assigned"}
                      </p>
                    </div>

                    <div className="emergency-action-badges">
                      <span
                        className={`emergency-priority-badge ${getPriorityClass(
                          action.priority,
                        )}`}
                      >
                        {action.priority ?? "Normal"}
                      </span>

                      <span
                        className={`emergency-status-badge ${getStatusClass(
                          action.status,
                        )}`}
                      >
                        {action.status ?? "Pending"}
                      </span>
                    </div>
                  </div>

                  <p className="emergency-action-description">
                    {action.action_description ??
                      "No action description available."}
                  </p>

                  <div className="emergency-action-details">
                    <div>
                      <span>Assigned Role</span>
                      <strong>{action.assigned_role ?? "Not assigned"}</strong>
                    </div>

                    <div>
                      <span>Assigned To</span>
                      <strong>{action.assigned_to ?? "Not assigned"}</strong>
                    </div>

                    <div>
                      <span>Mandatory</span>
                      <strong>{action.mandatory ? "Yes" : "No"}</strong>
                    </div>

                    <div>
                      <span>Verified</span>
                      <strong>{action.verified ? "Yes" : "No"}</strong>
                    </div>
                  </div>

                  <div className="emergency-action-footer">
                    <span>Created: {formatDate(action.created_at)}</span>
                    <span>Due: {formatDate(action.due_at)}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <aside className="emergency-side-panel">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Response Performance</h3>
                <p>Average emergency handling times</p>
              </div>
            </div>

            <div className="response-performance-list">
              <div className="response-performance-item">
                <Timer size={20} />

                <div>
                  <span>Average Response Time</span>
                  <strong>
                    {formatMinutes(summary?.average_response_time_minutes)}
                  </strong>
                </div>
              </div>

              <div className="response-performance-item">
                <CheckCircle2 size={20} />

                <div>
                  <span>Average Completion Time</span>
                  <strong>
                    {formatMinutes(summary?.average_completion_time_minutes)}
                  </strong>
                </div>
              </div>

              <div className="response-performance-item">
                <ShieldAlert size={20} />

                <div>
                  <span>Verified Actions</span>
                  <strong>{summary?.verified_actions ?? 0}</strong>
                </div>
              </div>

              <div className="response-performance-item">
                <AlertTriangle size={20} />

                <div>
                  <span>Mandatory Pending</span>
                  <strong>{summary?.mandatory_pending_actions ?? 0}</strong>
                </div>
              </div>
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Assigned Response Roles</h3>
                <p>Teams currently involved in emergency response</p>
              </div>
            </div>

            {!summary || summary.assigned_roles.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <UserRoundCheck size={32} />
                <p>No response roles are currently assigned.</p>
              </div>
            ) : (
              <div className="assigned-role-list">
                {summary.assigned_roles.map((role) => (
                  <div className="assigned-role-item" key={role}>
                    <UserRoundCheck size={17} />
                    <span>{role}</span>
                  </div>
                ))}
              </div>
            )}
          </article>
        </aside>
      </section>
    </div>
  );
}

export default Emergency;