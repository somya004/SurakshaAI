import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  GraduationCap,
  HardHat,
  HeartPulse,
  MapPin,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";

import { getWorkers, getWorkerSafety } from "../api/workersApi";

interface WorkerProfile {
  id: number;
  worker_id: string;
  worker_name: string;
  employer_name: string;
  job_role: string;
  department: string;
  experience_years: number;
  safety_training_completed: boolean;
  hot_work_authorized: boolean;
  confined_space_authorized: boolean;
  electrical_work_authorized: boolean;
  work_at_height_authorized: boolean;
  training_expiry_date: string | null;
  medical_clearance_valid: boolean;
  active: boolean;
}

interface WorkerSafety {
  worker_id: string;
  worker_name: string;
  plant_id: string;
  zone_id: string;
  is_inside: boolean;
  ppe_data_available: boolean;
  ppe_status: string;
  ppe_compliant: boolean | null;
  missing_ppe: string[];
  exposure_level: string;
  worker_at_risk: boolean;
  last_location_update: string | null;
  last_ppe_update: string | null;
}

interface WorkerSafetyResponse {
  plant_id: string | null;
  zone_id: string | null;
  total_workers_inside: number;
  ppe_compliant_workers: number;
  ppe_non_compliant_workers: number;
  ppe_unverified_workers: number;
  workers_at_risk: number;
  ppe_compliance_percentage: number | null;
  workers: WorkerSafety[];
}

interface CombinedWorker {
  profile: WorkerProfile;
  safety?: WorkerSafety;
}

function Workers() {
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [safetyData, setSafetyData] =
    useState<WorkerSafetyResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadWorkers = async (manualRefresh = false) => {
    try {
      if (manualRefresh) {
        setRefreshing(true);
      }

      setError("");

      const [workersResponse, safetyResponse] = await Promise.all([
        getWorkers(),
        getWorkerSafety(),
      ]);

      setWorkers(Array.isArray(workersResponse) ? workersResponse : []);
      setSafetyData(safetyResponse);
    } catch (err) {
      console.error("Workers API error:", err);
      setError("Unable to load workers and PPE information.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadWorkers();

    const intervalId = window.setInterval(() => {
      loadWorkers();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  const combinedWorkers = useMemo<CombinedWorker[]>(() => {
    return workers.map((profile) => ({
      profile,
      safety: safetyData?.workers.find(
        (worker) => worker.worker_id === profile.worker_id,
      ),
    }));
  }, [workers, safetyData]);

  const formatDate = (date: string | null | undefined) => {
    if (!date) {
      return "Not available";
    }

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "Invalid date";
    }

    return parsedDate.toLocaleString();
  };

  const getPpeClass = (worker?: WorkerSafety) => {
    if (!worker || worker.ppe_status === "not_verified") {
      return "ppe-unverified";
    }

    if (worker.ppe_compliant === true) {
      return "ppe-compliant";
    }

    if (worker.ppe_compliant === false) {
      return "ppe-non-compliant";
    }

    return "ppe-unverified";
  };

  const getPpeLabel = (worker?: WorkerSafety) => {
    if (!worker) {
      return "No live data";
    }

    if (worker.ppe_status === "not_verified") {
      return "Not verified";
    }

    if (worker.ppe_compliant === true) {
      return "Compliant";
    }

    if (worker.ppe_compliant === false) {
      return "Non-compliant";
    }

    return worker.ppe_status || "Unknown";
  };

  const compliancePercentage =
    safetyData?.ppe_compliance_percentage === null ||
    safetyData?.ppe_compliance_percentage === undefined
      ? "N/A"
      : `${safetyData.ppe_compliance_percentage.toFixed(1)}%`;

  if (loading) {
    return (
      <div className="simple-page">
        <h2>Loading workers and PPE data...</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <h2>Workers & PPE</h2>
          <p>
            Monitor workers, safety authorizations, locations and PPE compliance
          </p>
        </div>

        <button
          type="button"
          className="refresh-button"
          disabled={refreshing}
          onClick={() => loadWorkers(true)}
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

      <section className="worker-summary-grid">
        <article className="worker-summary-card">
          <div className="worker-summary-icon total-workers-icon">
            <Users size={23} />
          </div>

          <div>
            <p>Total Registered Workers</p>
            <strong>{workers.length}</strong>
          </div>
        </article>

        <article className="worker-summary-card">
          <div className="worker-summary-icon workers-inside-icon">
            <UserCheck size={23} />
          </div>

          <div>
            <p>Workers Inside</p>
            <strong>{safetyData?.total_workers_inside ?? 0}</strong>
          </div>
        </article>

        <article className="worker-summary-card">
          <div className="worker-summary-icon compliance-icon">
            <HardHat size={23} />
          </div>

          <div>
            <p>PPE Compliance</p>
            <strong>{compliancePercentage}</strong>
          </div>
        </article>

        <article className="worker-summary-card">
          <div className="worker-summary-icon risk-workers-icon">
            <AlertTriangle size={23} />
          </div>

          <div>
            <p>Workers at Risk</p>
            <strong>{safetyData?.workers_at_risk ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="ppe-status-grid">
        <article className="ppe-status-card ppe-good-card">
          <CheckCircle2 size={21} />

          <div>
            <span>PPE Compliant</span>
            <strong>{safetyData?.ppe_compliant_workers ?? 0}</strong>
          </div>
        </article>

        <article className="ppe-status-card ppe-bad-card">
          <XCircle size={21} />

          <div>
            <span>PPE Non-compliant</span>
            <strong>{safetyData?.ppe_non_compliant_workers ?? 0}</strong>
          </div>
        </article>

        <article className="ppe-status-card ppe-pending-card">
          <Clock3 size={21} />

          <div>
            <span>PPE Unverified</span>
            <strong>{safetyData?.ppe_unverified_workers ?? 0}</strong>
          </div>
        </article>
      </section>

      <section className="workers-layout">
        <article className="dashboard-card worker-list-card">
          <div className="card-heading">
            <div>
              <h3>Worker Safety Records</h3>
              <p>Profile, location, PPE and authorization details</p>
            </div>
          </div>

          {combinedWorkers.length === 0 ? (
            <div className="empty-state">
              <Users size={37} />

              <h3>No workers found</h3>

              <p>Worker records will appear here after registration.</p>
            </div>
          ) : (
            <div className="worker-record-list">
              {combinedWorkers.map(({ profile, safety }) => (
                <article className="worker-record" key={profile.id}>
                  <div className="worker-record-header">
                    <div className="worker-avatar">
                      {profile.worker_name.charAt(0).toUpperCase()}
                    </div>

                    <div className="worker-main-info">
                      <div className="worker-name-row">
                        <div>
                          <h4>{profile.worker_name}</h4>

                          <p>
                            {profile.worker_id} · {profile.employer_name}
                          </p>
                        </div>

                        <div className="worker-badges">
                          <span
                            className={`worker-status-badge ${
                              profile.active ? "worker-active" : "worker-inactive"
                            }`}
                          >
                            {profile.active ? "Active" : "Inactive"}
                          </span>

                          <span
                            className={`ppe-status-badge ${getPpeClass(safety)}`}
                          >
                            {getPpeLabel(safety)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="worker-info-grid">
                    <div>
                      <BriefcaseBusiness size={17} />

                      <span>
                        <small>Role</small>
                        <strong>{profile.job_role}</strong>
                      </span>
                    </div>

                    <div>
                      <ShieldCheck size={17} />

                      <span>
                        <small>Department</small>
                        <strong>{profile.department}</strong>
                      </span>
                    </div>

                    <div>
                      <MapPin size={17} />

                      <span>
                        <small>Current Location</small>
                        <strong>
                          {safety
                            ? `${safety.plant_id} / ${safety.zone_id}`
                            : "No location data"}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <HardHat size={17} />

                      <span>
                        <small>Entry Status</small>
                        <strong>
                          {safety?.is_inside ? "Inside plant" : "Outside plant"}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <GraduationCap size={17} />

                      <span>
                        <small>Experience</small>
                        <strong>{profile.experience_years} years</strong>
                      </span>
                    </div>

                    <div>
                      <HeartPulse size={17} />

                      <span>
                        <small>Medical Clearance</small>
                        <strong>
                          {profile.medical_clearance_valid
                            ? "Valid"
                            : "Not valid"}
                        </strong>
                      </span>
                    </div>
                  </div>

                  <div className="authorization-section">
                    <p>Safety Authorizations</p>

                    <div className="authorization-list">
                      <span
                        className={
                          profile.safety_training_completed
                            ? "authorization-valid"
                            : "authorization-invalid"
                        }
                      >
                        Safety Training
                      </span>

                      <span
                        className={
                          profile.hot_work_authorized
                            ? "authorization-valid"
                            : "authorization-invalid"
                        }
                      >
                        Hot Work
                      </span>

                      <span
                        className={
                          profile.confined_space_authorized
                            ? "authorization-valid"
                            : "authorization-invalid"
                        }
                      >
                        Confined Space
                      </span>

                      <span
                        className={
                          profile.electrical_work_authorized
                            ? "authorization-valid"
                            : "authorization-invalid"
                        }
                      >
                        Electrical Work
                      </span>

                      <span
                        className={
                          profile.work_at_height_authorized
                            ? "authorization-valid"
                            : "authorization-invalid"
                        }
                      >
                        Work at Height
                      </span>
                    </div>
                  </div>

                  <div className="worker-record-footer">
                    <span>
                      Training expiry:{" "}
                      {formatDate(profile.training_expiry_date)}
                    </span>

                    <span>
                      Last location update:{" "}
                      {formatDate(safety?.last_location_update)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <aside className="workers-side-panel">
          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>Live Worker Locations</h3>
                <p>Workers currently detected inside the plant</p>
              </div>
            </div>

            {!safetyData || safetyData.workers.length === 0 ? (
              <div className="empty-state compact-empty-state">
                <MapPin size={31} />
                <p>No live location records found.</p>
              </div>
            ) : (
              <div className="worker-location-list">
                {safetyData.workers.map((worker) => (
                  <div className="worker-location-item" key={worker.worker_id}>
                    <div>
                      <strong>{worker.worker_name}</strong>
                      <span>{worker.worker_id}</span>
                    </div>

                    <div className="location-value">
                      <MapPin size={15} />
                      {worker.zone_id}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="dashboard-card">
            <div className="card-heading">
              <div>
                <h3>PPE Violations</h3>
                <p>Missing or non-compliant protective equipment</p>
              </div>
            </div>

            {(safetyData?.ppe_non_compliant_workers ?? 0) === 0 ? (
              <div className="empty-state compact-empty-state">
                <CheckCircle2 size={32} />
                <h3>No PPE violations</h3>
                <p>No confirmed non-compliant workers were detected.</p>
              </div>
            ) : (
              <div className="ppe-violation-list">
                {safetyData?.workers
                  .filter((worker) => worker.ppe_compliant === false)
                  .map((worker) => (
                    <article
                      className="ppe-violation-item"
                      key={worker.worker_id}
                    >
                      <div>
                        <strong>{worker.worker_name}</strong>
                        <span>{worker.zone_id}</span>
                      </div>

                      <p>
                        {worker.missing_ppe.length > 0
                          ? worker.missing_ppe.join(", ")
                          : "PPE non-compliance detected"}
                      </p>
                    </article>
                  ))}
              </div>
            )}
          </article>
        </aside>
      </section>
    </div>
  );
}

export default Workers;