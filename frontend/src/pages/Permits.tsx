import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileCheck2,
  Flame,
  Gauge,
  HardHat,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Users,
  Wrench,
  XCircle,
} from "lucide-react";

import {
  getOperationsSummary,
  getPermits,
} from "../api/permitsApi";

interface Permit {
  id?: number;
  permit_id: string;
  plant_id: string;
  zone_id: string;
  equipment_id: string;
  permit_type: string;
  work_description: string;
  issue_time?: string;
  start_time: string;
  expiry_time: string;
  permit_status: string;
  issuer_id: string;
  approver_id: string;
  contractor_name: string;
  worker_count: number;
  gas_test_required: boolean;
  gas_test_value: number | null;
  isolation_required: boolean;
  isolation_confirmed: boolean;
  ppe_required?: string;
  hot_work_flag?: boolean;
  confined_space_flag?: boolean;
  risk_level: string;

  hot_work?: boolean;
  confined_space?: boolean;
  gas_test_issue?: boolean;
  isolation_issue?: boolean;
  is_currently_active?: boolean;
  is_expired?: boolean;
  is_upcoming?: boolean;
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

interface OperationsResponse {
  plant_id: string | null;
  zone_id: string | null;
  permit_summary: PermitSummary;
  permits: Permit[];
}

function Permits() {
  const [permits, setPermits] = useState<Permit[]>([]);
  const [summary, setSummary] = useState<PermitSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadPermitData = async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const [permitResponse, operationsResponse] = await Promise.all([
        getPermits(),
        getOperationsSummary(),
      ]);

      const operationsData = operationsResponse as OperationsResponse;

      setSummary(operationsData.permit_summary);

      if (Array.isArray(operationsData.permits)) {
        setPermits(operationsData.permits);
      } else if (Array.isArray(permitResponse)) {
        setPermits(permitResponse);
      } else {
        setPermits([]);
      }
    } catch (err) {
      console.error("Permit API error:", err);
      setError("Unable to load permit information.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadPermitData();

    const intervalId = window.setInterval(() => {
      loadPermitData();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  const expiringSoonPermits = useMemo(() => {
    const now = Date.now();
    const nextTwentyFourHours = now + 24 * 60 * 60 * 1000;

    return permits.filter((permit) => {
      const expiryTime = new Date(permit.expiry_time).getTime();

      return expiryTime > now && expiryTime <= nextTwentyFourHours;
    });
  }, [permits]);

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

  const formatPermitType = (value: string) => {
    return value
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  const getPermitStatus = (permit: Permit) => {
    if (permit.is_expired) {
      return "Expired";
    }

    if (permit.is_upcoming) {
      return "Upcoming";
    }

    if (permit.is_currently_active) {
      return "Active";
    }

    return formatPermitType(permit.permit_status || "Unknown");
  };

  const getStatusClass = (permit: Permit) => {
    if (permit.is_expired) {
      return "permit-expired";
    }

    if (permit.is_upcoming) {
      return "permit-upcoming";
    }

    if (permit.is_currently_active) {
      return "permit-active";
    }

    const status = permit.permit_status?.toLowerCase();

    if (status === "closed") {
      return "permit-closed";
    }

    if (status === "cancelled") {
      return "permit-cancelled";
    }

    return "permit-upcoming";
  };

  const getRiskClass = (riskLevel: string) => {
    const value = riskLevel?.toLowerCase();

    if (value === "critical") {
      return "permit-risk-critical";
    }

    if (value === "high") {
      return "permit-risk-high";
    }

    if (value === "medium") {
      return "permit-risk-medium";
    }

    return "permit-risk-low";
  };

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading permit data...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Permit Management</h2>
          <p>
            Monitor industrial work permits, safety controls and expiry status
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadPermitData(true)}
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

      <section className="permit-summary-grid">
        <article className="permit-summary-card">
          <div className="permit-summary-icon permit-total-icon">
            <FileCheck2 size={23} />
          </div>

          <div>
            <p>Total Permits</p>
            <strong>{summary?.total_permits ?? permits.length}</strong>
          </div>
        </article>

        <article className="permit-summary-card">
          <div className="permit-summary-icon permit-active-icon">
            <CheckCircle2 size={23} />
          </div>

          <div>
            <p>Currently Active</p>
            <strong>{summary?.active_permits ?? 0}</strong>
          </div>
        </article>

        <article className="permit-summary-card">
          <div className="permit-summary-icon permit-expired-icon">
            <XCircle size={23} />
          </div>

          <div>
            <p>Expired Permits</p>
            <strong>{summary?.expired_permits ?? 0}</strong>
          </div>
        </article>

        <article className="permit-summary-card">
          <div className="permit-summary-icon permit-risk-icon">
            <ShieldAlert size={23} />
          </div>

          <div>
            <p>High-Risk Permits</p>
            <strong>{summary?.high_risk_permits ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="permit-secondary-grid">
        <article className="permit-small-card permit-hot-work-card">
          <Flame size={20} />

          <div>
            <span>Hot Work</span>
            <strong>{summary?.hot_work_permits ?? 0}</strong>
          </div>
        </article>

        <article className="permit-small-card permit-confined-card">
          <HardHat size={20} />

          <div>
            <span>Confined Space</span>
            <strong>{summary?.confined_space_permits ?? 0}</strong>
          </div>
        </article>

        <article className="permit-small-card permit-isolation-card">
          <Wrench size={20} />

          <div>
            <span>Isolation Issues</span>
            <strong>{summary?.isolation_issues ?? 0}</strong>
          </div>
        </article>

        <article className="permit-small-card permit-gas-card">
          <Gauge size={20} />

          <div>
            <span>Gas Test Issues</span>
            <strong>{summary?.gas_test_issues ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="permit-layout">
        <article className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Permit Records</h3>
              <p>Work permits and associated safety requirements</p>
            </div>

            <span className="record-count">{permits.length} permits</span>
          </div>

          {permits.length === 0 ? (
            <div className="empty-state permit-empty-state">
              <FileCheck2 size={40} />
              <h3>No permits found</h3>
              <p>Permit records will appear here after permit creation.</p>
            </div>
          ) : (
            <div className="permit-record-list">
              {permits.map((permit) => (
                <article
                  className="permit-record-card"
                  key={permit.permit_id}
                >
                  <div className="permit-record-header">
                    <div>
                      <div className="permit-title-row">
                        <h4>{permit.permit_id}</h4>

                        {permit.hot_work || permit.hot_work_flag ? (
                          <Flame size={16} className="hot-work-indicator" />
                        ) : null}
                      </div>

                      <p>{permit.work_description}</p>
                    </div>

                    <div className="permit-badges">
                      <span
                        className={`permit-risk-badge ${getRiskClass(
                          permit.risk_level,
                        )}`}
                      >
                        {permit.risk_level} risk
                      </span>

                      <span
                        className={`permit-status-badge ${getStatusClass(
                          permit,
                        )}`}
                      >
                        {getPermitStatus(permit)}
                      </span>
                    </div>
                  </div>

                  <div className="permit-information-grid">
                    <div>
                      <FileCheck2 size={17} />

                      <span>
                        <small>Permit Type</small>
                        <strong>
                          {formatPermitType(permit.permit_type)}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <MapPin size={17} />

                      <span>
                        <small>Location</small>
                        <strong>
                          {permit.plant_id} / {permit.zone_id}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <Wrench size={17} />

                      <span>
                        <small>Equipment</small>
                        <strong>{permit.equipment_id}</strong>
                      </span>
                    </div>

                    <div>
                      <Users size={17} />

                      <span>
                        <small>Workers</small>
                        <strong>{permit.worker_count}</strong>
                      </span>
                    </div>

                    <div>
                      <Clock3 size={17} />

                      <span>
                        <small>Start Time</small>
                        <strong>{formatDate(permit.start_time)}</strong>
                      </span>
                    </div>

                    <div>
                      <CalendarClock size={17} />

                      <span>
                        <small>Expiry Time</small>
                        <strong>{formatDate(permit.expiry_time)}</strong>
                      </span>
                    </div>
                  </div>

                  <div className="permit-safety-section">
                    <p>Safety Requirements</p>

                    <div className="permit-safety-list">
                      <span
                        className={
                          permit.gas_test_required
                            ? permit.gas_test_issue
                              ? "permit-safety-invalid"
                              : "permit-safety-valid"
                            : "permit-safety-neutral"
                        }
                      >
                        Gas Test:{" "}
                        {permit.gas_test_required
                          ? `${permit.gas_test_value ?? "N/A"}`
                          : "Not required"}
                      </span>

                      <span
                        className={
                          permit.isolation_required
                            ? permit.isolation_confirmed
                              ? "permit-safety-valid"
                              : "permit-safety-invalid"
                            : "permit-safety-neutral"
                        }
                      >
                        Isolation:{" "}
                        {permit.isolation_required
                          ? permit.isolation_confirmed
                            ? "Confirmed"
                            : "Pending"
                          : "Not required"}
                      </span>

                      <span
                        className={
                          permit.approver_id
                            ? "permit-safety-valid"
                            : "permit-safety-invalid"
                        }
                      >
                        Approval:{" "}
                        {permit.approver_id ? "Approved" : "Pending"}
                      </span>
                    </div>
                  </div>

                  {permit.ppe_required && (
                    <div className="permit-ppe-row">
                      <HardHat size={16} />

                      <div>
                        <span>Required PPE</span>
                        <strong>{permit.ppe_required}</strong>
                      </div>
                    </div>
                  )}

                  <div className="permit-record-footer">
                    <span>Contractor: {permit.contractor_name}</span>
                    <span>Issuer: {permit.issuer_id}</span>
                    <span>Approver: {permit.approver_id}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <aside className="permit-side-panel">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Permit Status</h3>
                <p>Current permit lifecycle summary</p>
              </div>
            </div>

            <div className="permit-status-list">
              <div>
                <span>Active</span>
                <strong>{summary?.active_permits ?? 0}</strong>
              </div>

              <div>
                <span>Upcoming</span>
                <strong>{summary?.upcoming_permits ?? 0}</strong>
              </div>

              <div>
                <span>Expired</span>
                <strong>{summary?.expired_permits ?? 0}</strong>
              </div>

              <div>
                <span>Closed</span>
                <strong>{summary?.closed_permits ?? 0}</strong>
              </div>

              <div>
                <span>Cancelled</span>
                <strong>{summary?.cancelled_permits ?? 0}</strong>
              </div>
            </div>
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Expiring Soon</h3>
                <p>Permits expiring within the next 24 hours</p>
              </div>
            </div>

            {expiringSoonPermits.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <CheckCircle2 size={32} />
                <h3>No permits expiring soon</h3>
                <p>No active permit will expire within 24 hours.</p>
              </div>
            ) : (
              <div className="expiring-permit-list">
                {expiringSoonPermits.map((permit) => (
                  <div
                    className="expiring-permit-item"
                    key={permit.permit_id}
                  >
                    <div>
                      <strong>{permit.permit_id}</strong>
                      <span>{formatPermitType(permit.permit_type)}</span>
                    </div>

                    <p>{formatDate(permit.expiry_time)}</p>
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

export default Permits;