import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Cog,
  LockKeyhole,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Timer,
  Users,
  Wrench,
} from "lucide-react";

import {
  getMaintenanceOrders,
  getOperationsSummary,
} from "../api/maintenanceApi";

interface MaintenanceOrder {
  id?: number;
  work_order_id: string;
  plant_id: string;
  zone_id: string;
  equipment_id: string;
  maintenance_type: string;
  failure_description: string;
  reported_time: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  maintenance_status: string;
  equipment_status: string;
  lockout_tagout_required: boolean;
  lockout_tagout_confirmed: boolean;
  criticality: string;
  assigned_team: string;
  maintenance_overdue_days: number;

  is_under_maintenance?: boolean;
  is_overdue?: boolean;
  lockout_tagout_issue?: boolean;
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
  maintenance_summary: MaintenanceSummary;
  maintenance_orders: MaintenanceOrder[];
}

function Maintenance() {
  const [orders, setOrders] = useState<MaintenanceOrder[]>([]);
  const [summary, setSummary] = useState<MaintenanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadMaintenanceData = async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const [maintenanceResponse, operationsResponse] = await Promise.all([
        getMaintenanceOrders(),
        getOperationsSummary(),
      ]);

      const operationsData = operationsResponse as OperationsResponse;

      setSummary(operationsData.maintenance_summary);

      if (Array.isArray(operationsData.maintenance_orders)) {
        setOrders(operationsData.maintenance_orders);
      } else if (Array.isArray(maintenanceResponse)) {
        setOrders(maintenanceResponse);
      } else {
        setOrders([]);
      }
    } catch (err) {
      console.error("Maintenance API error:", err);
      setError("Unable to load maintenance information.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMaintenanceData();

    const intervalId = window.setInterval(() => {
      loadMaintenanceData();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  const overdueOrders = useMemo(() => {
    return orders.filter(
      (order) =>
        order.is_overdue === true || order.maintenance_overdue_days > 0,
    );
  }, [orders]);

  const activeOrders = useMemo(() => {
    return orders.filter((order) => {
      const status = order.maintenance_status.toLowerCase();

      return (
        status === "scheduled" ||
        status === "in_progress" ||
        status === "in progress" ||
        status === "paused"
      );
    });
  }, [orders]);

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

  const getStatusClass = (status: string) => {
    const value = status.toLowerCase();

    if (value === "completed") {
      return "maintenance-completed";
    }

    if (value === "in_progress" || value === "in progress") {
      return "maintenance-progress";
    }

    if (value === "scheduled") {
      return "maintenance-scheduled";
    }

    if (value === "paused") {
      return "maintenance-paused";
    }

    if (value === "cancelled") {
      return "maintenance-cancelled";
    }

    return "maintenance-scheduled";
  };

  const getCriticalityClass = (criticality: string) => {
    const value = criticality.toLowerCase();

    if (value === "critical") {
      return "maintenance-critical";
    }

    if (value === "high") {
      return "maintenance-high";
    }

    if (value === "medium") {
      return "maintenance-medium";
    }

    return "maintenance-low";
  };

  const isLotoSafe = (order: MaintenanceOrder) => {
    if (!order.lockout_tagout_required) {
      return true;
    }

    return (
      order.lockout_tagout_confirmed === true &&
      order.lockout_tagout_issue !== true
    );
  };

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading maintenance data...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Maintenance Management</h2>
          <p>
            Monitor equipment health, maintenance work orders and LOTO safety
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadMaintenanceData(true)}
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

      <section className="maintenance-summary-grid">
        <article className="maintenance-summary-card">
          <div className="maintenance-summary-icon maintenance-total-icon">
            <Wrench size={23} />
          </div>

          <div>
            <p>Total Work Orders</p>
            <strong>
              {summary?.total_maintenance_orders ?? orders.length}
            </strong>
          </div>
        </article>

        <article className="maintenance-summary-card">
          <div className="maintenance-summary-icon maintenance-progress-icon">
            <Timer size={23} />
          </div>

          <div>
            <p>In Progress</p>
            <strong>{summary?.in_progress_maintenance ?? 0}</strong>
          </div>
        </article>

        <article className="maintenance-summary-card">
          <div className="maintenance-summary-icon maintenance-completed-icon">
            <CheckCircle2 size={23} />
          </div>

          <div>
            <p>Completed</p>
            <strong>{summary?.completed_maintenance ?? 0}</strong>
          </div>
        </article>

        <article className="maintenance-summary-card">
          <div className="maintenance-summary-icon maintenance-overdue-icon">
            <AlertTriangle size={23} />
          </div>

          <div>
            <p>Overdue</p>
            <strong>{summary?.overdue_maintenance ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="maintenance-secondary-grid">
        <article className="maintenance-small-card maintenance-critical-card">
          <ShieldAlert size={20} />

          <div>
            <span>Critical Maintenance</span>
            <strong>{summary?.critical_maintenance ?? 0}</strong>
          </div>
        </article>

        <article className="maintenance-small-card maintenance-machine-card">
          <Cog size={20} />

          <div>
            <span>Machines Under Maintenance</span>
            <strong>{summary?.machines_under_maintenance ?? 0}</strong>
          </div>
        </article>

        <article className="maintenance-small-card maintenance-loto-card">
          <LockKeyhole size={20} />

          <div>
            <span>LOTO Pending</span>
            <strong>{summary?.lockout_tagout_pending ?? 0}</strong>
          </div>
        </article>

        <article className="maintenance-small-card maintenance-scheduled-card">
          <CalendarClock size={20} />

          <div>
            <span>Scheduled</span>
            <strong>{summary?.scheduled_maintenance ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="maintenance-layout">
        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Maintenance Work Orders</h3>
              <p>Equipment repairs and preventive maintenance activities</p>
            </div>

            <span className="record-count">{orders.length} orders</span>
          </div>

          {orders.length === 0 ? (
            <div className="empty-state maintenance-empty-state">
              <Wrench size={40} />
              <h3>No maintenance orders</h3>
              <p>Maintenance work orders will appear here when created.</p>
            </div>
          ) : (
            <div className="maintenance-order-list">
              {orders.map((order) => (
                <article
                  className="maintenance-order-card"
                  key={order.work_order_id}
                >
                  <div className="maintenance-order-header">
                    <div>
                      <h4>{order.work_order_id}</h4>
                      <p>{order.failure_description}</p>
                    </div>

                    <div className="maintenance-badges">
                      <span
                        className={`maintenance-criticality-badge ${getCriticalityClass(
                          order.criticality,
                        )}`}
                      >
                        {formatText(order.criticality)}
                      </span>

                      <span
                        className={`maintenance-status-badge ${getStatusClass(
                          order.maintenance_status,
                        )}`}
                      >
                        {formatText(order.maintenance_status)}
                      </span>
                    </div>
                  </div>

                  <div className="maintenance-information-grid">
                    <div>
                      <Wrench size={17} />

                      <span>
                        <small>Maintenance Type</small>
                        <strong>
                          {formatText(order.maintenance_type)}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <Cog size={17} />

                      <span>
                        <small>Equipment</small>
                        <strong>{order.equipment_id}</strong>
                      </span>
                    </div>

                    <div>
                      <MapPin size={17} />

                      <span>
                        <small>Location</small>
                        <strong>
                          {order.plant_id} / {order.zone_id}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <Users size={17} />

                      <span>
                        <small>Assigned Team</small>
                        <strong>{order.assigned_team}</strong>
                      </span>
                    </div>

                    <div>
                      <Clock3 size={17} />

                      <span>
                        <small>Scheduled Start</small>
                        <strong>{formatDate(order.scheduled_start)}</strong>
                      </span>
                    </div>

                    <div>
                      <CalendarClock size={17} />

                      <span>
                        <small>Scheduled End</small>
                        <strong>{formatDate(order.scheduled_end)}</strong>
                      </span>
                    </div>
                  </div>

                  <div className="maintenance-safety-section">
                    <p>Equipment and Safety Status</p>

                    <div className="maintenance-safety-list">
                      <span
                        className={
                          order.equipment_status.toLowerCase() === "operational"
                            ? "maintenance-safety-valid"
                            : "maintenance-safety-warning"
                        }
                      >
                        Equipment: {formatText(order.equipment_status)}
                      </span>

                      <span
                        className={
                          isLotoSafe(order)
                            ? "maintenance-safety-valid"
                            : "maintenance-safety-invalid"
                        }
                      >
                        LOTO:{" "}
                        {!order.lockout_tagout_required
                          ? "Not required"
                          : order.lockout_tagout_confirmed
                            ? "Confirmed"
                            : "Pending"}
                      </span>

                      <span
                        className={
                          order.maintenance_overdue_days > 0
                            ? "maintenance-safety-invalid"
                            : "maintenance-safety-valid"
                        }
                      >
                        Overdue:{" "}
                        {order.maintenance_overdue_days > 0
                          ? `${order.maintenance_overdue_days} days`
                          : "No"}
                      </span>
                    </div>
                  </div>

                  <div className="maintenance-timeline">
                    <div>
                      <span>Reported</span>
                      <strong>{formatDate(order.reported_time)}</strong>
                    </div>

                    <div>
                      <span>Actual Start</span>
                      <strong>{formatDate(order.actual_start)}</strong>
                    </div>

                    <div>
                      <span>Actual End</span>
                      <strong>{formatDate(order.actual_end)}</strong>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <aside className="maintenance-side-panel">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Maintenance Status</h3>
                <p>Current lifecycle of maintenance work</p>
              </div>
            </div>

            <div className="maintenance-status-list">
              <div>
                <span>Scheduled</span>
                <strong>{summary?.scheduled_maintenance ?? 0}</strong>
              </div>

              <div>
                <span>In Progress</span>
                <strong>{summary?.in_progress_maintenance ?? 0}</strong>
              </div>

              <div>
                <span>Paused</span>
                <strong>{summary?.paused_maintenance ?? 0}</strong>
              </div>

              <div>
                <span>Completed</span>
                <strong>{summary?.completed_maintenance ?? 0}</strong>
              </div>

              <div>
                <span>Overdue</span>
                <strong>{summary?.overdue_maintenance ?? 0}</strong>
              </div>
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Active Maintenance</h3>
                <p>Work orders requiring operational attention</p>
              </div>
            </div>

            {activeOrders.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <CheckCircle2 size={32} />
                <h3>No active maintenance</h3>
                <p>No equipment is currently undergoing maintenance.</p>
              </div>
            ) : (
              <div className="active-maintenance-list">
                {activeOrders.map((order) => (
                  <div
                    className="active-maintenance-item"
                    key={order.work_order_id}
                  >
                    <div>
                      <strong>{order.work_order_id}</strong>
                      <span>{order.equipment_id}</span>
                    </div>

                    <p>{formatText(order.maintenance_status)}</p>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Overdue Maintenance</h3>
                <p>Delayed work orders requiring escalation</p>
              </div>
            </div>

            {overdueOrders.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <CheckCircle2 size={32} />
                <h3>No overdue maintenance</h3>
                <p>All maintenance work orders are within schedule.</p>
              </div>
            ) : (
              <div className="overdue-maintenance-list">
                {overdueOrders.map((order) => (
                  <div
                    className="overdue-maintenance-item"
                    key={order.work_order_id}
                  >
                    <div>
                      <strong>{order.work_order_id}</strong>
                      <span>{order.equipment_id}</span>
                    </div>

                    <p>{order.maintenance_overdue_days} days overdue</p>
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

export default Maintenance;