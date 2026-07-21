import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  fetchCommandCenterOverview,
  fetchModelMetrics,
} from "../api/mlCommandCenterApi";

import type {
  CommandCenterOverview,
  ModelMetrics,
} from "../types/mlCommandCenter";

type RiskFilter =
  | "ALL"
  | "SAFE"
  | "ALERT"
  | "HIGH"
  | "CRITICAL";

function CommandCenter() {
  const [overview, setOverview] =
    useState<CommandCenterOverview | null>(null);

  const [metrics, setMetrics] =
    useState<ModelMetrics | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [searchText, setSearchText] =
    useState("");

  const [riskFilter, setRiskFilter] =
    useState<RiskFilter>("ALL");

  const [lastUpdated, setLastUpdated] =
    useState<Date | null>(null);

  const loadCommandCenterData =
    useCallback(async (manualRefresh = false) => {
      try {
        if (manualRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        setError("");

        const [overviewData, metricsData] =
          await Promise.all([
            fetchCommandCenterOverview(),
            fetchModelMetrics(),
          ]);

        setOverview(overviewData);
        setMetrics(metricsData);
        setLastUpdated(new Date());
      } catch (requestError) {
        console.error(
          "Unable to load Command Center:",
          requestError,
        );

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load ML Command Center data.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    }, []);

  useEffect(() => {
    void loadCommandCenterData();

    const refreshInterval = window.setInterval(() => {
      void loadCommandCenterData();
    }, 15000);

    return () => {
      window.clearInterval(refreshInterval);
    };
  }, [loadCommandCenterData]);

  const filteredRegions = useMemo(() => {
    if (!overview) {
      return [];
    }

    const normalizedSearch =
      searchText.trim().toLowerCase();

    return overview.regions.filter((region) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        region.factory
          .toLowerCase()
          .includes(normalizedSearch) ||
        region.region
          .toLowerCase()
          .includes(normalizedSearch) ||
        region.zone_id
          .toLowerCase()
          .includes(normalizedSearch);

      const matchesRisk =
        riskFilter === "ALL" ||
        region.risk_level.toUpperCase() ===
          riskFilter;

      return matchesSearch && matchesRisk;
    });
  }, [overview, riskFilter, searchText]);

  const highestRiskRegion = useMemo(() => {
    if (!overview || overview.regions.length === 0) {
      return null;
    }

    return [...overview.regions].sort(
      (first, second) =>
        second.compound_risk_score -
        first.compound_risk_score,
    )[0];
  }, [overview]);

  if (loading && !overview) {
    return (
      <main className="ml-command-center-page">
        <section className="command-state-card">
          <div className="command-spinner" />

          <h2>Loading ML Command Center</h2>

          <p>
            Reading model metrics and compound-risk
            assessments.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="ml-command-center-page">
      <section className="ml-command-header">
        <div>
          <p className="page-eyebrow">
            Unified Industrial Safety Intelligence
          </p>

          <h1>ML Command Center</h1>

          <p>
            Zone-level accident probability,
            anomaly intelligence and compound-risk
            decisions from one place.
          </p>
        </div>

        <div className="command-header-actions">
          <div className="live-status">
            <span className="live-status-dot" />

            <div>
              <strong>Live monitoring</strong>

              <small>
                {lastUpdated
                  ? `Updated ${lastUpdated.toLocaleTimeString()}`
                  : "Waiting for data"}
              </small>
            </div>
          </div>

          <button
            type="button"
            className="secondary-button"
            disabled={refreshing}
            onClick={() =>
              void loadCommandCenterData(true)
            }
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>
        </div>
      </section>

      {error && (
        <section className="command-error-card">
          <div>
            <strong>
              Command Center data unavailable
            </strong>

            <p>{error}</p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              void loadCommandCenterData(true)
            }
          >
            Retry
          </button>
        </section>
      )}

      <section className="command-section">
        <div className="command-section-heading">
          <div>
            <p className="section-eyebrow">
              Model Reliability
            </p>

            <h2>Prediction Model Performance</h2>

            <p>
              Metrics used to evaluate the accident
              prediction model.
            </p>
          </div>

          <span
            className={`model-status-badge ${
              metrics?.available
                ? "model-available"
                : "model-unavailable"
            }`}
          >
            {metrics?.available
              ? "Model available"
              : "Model unavailable"}
          </span>
        </div>

        <section className="model-metrics-grid">
          <MetricCard
            label="Selected Model"
            value={
              metrics?.available
                ? metrics.model_name ??
                  "Not specified"
                : "Unavailable"
            }
            description="Active accident prediction model"
          />

          <MetricCard
            label="Recall"
            value={
              metrics?.available
                ? `${metrics.recall ?? 0}%`
                : "—"
            }
            description="Detected positive safety events"
          />

          <MetricCard
            label="False Negative Rate"
            value={
              metrics?.available
                ? `${
                    metrics.false_negative_rate ?? 0
                  }%`
                : "—"
            }
            description="High-risk events potentially missed"
          />

          <MetricCard
            label="ROC-AUC"
            value={
              metrics?.available
                ? `${metrics.roc_auc ?? 0}%`
                : "—"
            }
            description="Overall prediction separation"
          />
        </section>
      </section>

      {overview && (
        <>
          <section className="command-section">
            <div className="command-section-heading">
              <div>
                <p className="section-eyebrow">
                  Compound Intelligence
                </p>

                <h2>ML Risk Overview</h2>

                <p>
                  Consolidated status of every
                  assessed industrial zone.
                </p>
              </div>
            </div>

            <section className="overview-summary-grid">
              <MetricCard
                label="Assessed Zones"
                value={
                  overview.summary.total_regions
                }
                description="Zones with an ML assessment"
              />

              <MetricCard
                label="Safe Zones"
                value={
                  overview.summary.safe_regions
                }
                description="No immediate compound-risk alert"
                variant="safe"
              />

              <MetricCard
                label="Alert Zones"
                value={
                  overview.summary.alert_regions +
                  overview.summary.high_regions +
                  overview.summary.critical_regions
                }
                description="Zones requiring attention"
                variant="warning"
              />

              <MetricCard
                label="Workers Exposed"
                value={
                  overview.summary.workers_exposed
                }
                description="Workers linked to assessed risk"
                variant={
                  overview.summary.workers_exposed > 0
                    ? "danger"
                    : "safe"
                }
              />
            </section>
          </section>

          <section className="command-intelligence-grid">
            <article className="command-panel priority-panel">
              <div className="panel-heading">
                <div>
                  <p className="section-eyebrow">
                    Priority Intelligence
                  </p>

                  <h2>Highest Compound Risk</h2>
                </div>

                {highestRiskRegion && (
                  <RiskBadge
                    level={
                      highestRiskRegion.risk_level
                    }
                  />
                )}
              </div>

              {highestRiskRegion ? (
                <>
                  <div className="priority-zone">
                    <div>
                      <span>Zone</span>

                      <strong>
                        {highestRiskRegion.zone_id}
                      </strong>

                      <p>
                        {highestRiskRegion.factory}
                        {" · "}
                        {highestRiskRegion.region}
                      </p>
                    </div>

                    <div className="priority-score">
                      <span>Compound score</span>

                      <strong>
                        {
                          highestRiskRegion
                            .compound_risk_score
                        }
                      </strong>
                    </div>
                  </div>

                  <div className="priority-metrics">
                    <div>
                      <span>ML probability</span>

                      <strong>
                        {
                          highestRiskRegion
                            .ml_probability
                        }
                        %
                      </strong>
                    </div>

                    <div>
                      <span>Workers exposed</span>

                      <strong>
                        {
                          highestRiskRegion
                            .workers_exposed
                        }
                      </strong>
                    </div>
                  </div>

                  <div className="decision-box">
                    <span>
                      Recommended safety decision
                    </span>

                    <strong>
                      {
                        highestRiskRegion
                          .final_decision
                      }
                    </strong>
                  </div>
                </>
              ) : (
                <EmptyState
                  title="No ML assessment available"
                  description="No zone-level compound-risk record has been generated yet."
                />
              )}
            </article>

            <article className="command-panel distribution-panel">
              <div className="panel-heading">
                <div>
                  <p className="section-eyebrow">
                    Risk Distribution
                  </p>

                  <h2>Zone Classification</h2>
                </div>
              </div>

              <RiskDistributionRow
                label="Safe"
                value={
                  overview.summary.safe_regions
                }
                total={
                  overview.summary.total_regions
                }
                className="distribution-safe"
              />

              <RiskDistributionRow
                label="Alert"
                value={
                  overview.summary.alert_regions
                }
                total={
                  overview.summary.total_regions
                }
                className="distribution-alert"
              />

              <RiskDistributionRow
                label="High"
                value={
                  overview.summary.high_regions
                }
                total={
                  overview.summary.total_regions
                }
                className="distribution-high"
              />

              <RiskDistributionRow
                label="Critical"
                value={
                  overview.summary.critical_regions
                }
                total={
                  overview.summary.total_regions
                }
                className="distribution-critical"
              />
            </article>
          </section>

          <section className="command-section">
            <div className="command-section-heading regions-heading">
              <div>
                <p className="section-eyebrow">
                  Zone Predictions
                </p>

                <h2>Compound-Risk Assessments</h2>

                <p>
                  Search and filter ML predictions
                  without entering sensor data
                  manually.
                </p>
              </div>

              <div className="region-controls">
                <input
                  type="search"
                  value={searchText}
                  placeholder="Search factory, region or zone"
                  aria-label="Search assessed zones"
                  onChange={(event) =>
                    setSearchText(
                      event.target.value,
                    )
                  }
                />

                <select
                  value={riskFilter}
                  aria-label="Filter by risk level"
                  onChange={(event) =>
                    setRiskFilter(
                      event.target
                        .value as RiskFilter,
                    )
                  }
                >
                  <option value="ALL">
                    All risk levels
                  </option>

                  <option value="SAFE">
                    Safe
                  </option>

                  <option value="ALERT">
                    Alert
                  </option>

                  <option value="HIGH">
                    High
                  </option>

                  <option value="CRITICAL">
                    Critical
                  </option>
                </select>
              </div>
            </div>

            {filteredRegions.length === 0 ? (
              <EmptyState
                title="No matching assessment"
                description={
                  overview.regions.length === 0
                    ? "The Command Center has not received a zone assessment yet."
                    : "Change the search text or risk filter."
                }
              />
            ) : (
              <div className="regions-table-wrapper">
                <table className="regions-table">
                  <thead>
                    <tr>
                      <th>Factory</th>
                      <th>Region</th>
                      <th>Zone</th>
                      <th>ML Probability</th>
                      <th>Compound Risk</th>
                      <th>Risk Status</th>
                      <th>Workers Exposed</th>
                      <th>Safety Decision</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredRegions.map(
                      (region) => (
                        <tr
                          key={
                            `${region.factory}-` +
                            `${region.region}-` +
                            region.zone_id
                          }
                        >
                          <td>
                            <strong>
                              {region.factory}
                            </strong>
                          </td>

                          <td>{region.region}</td>

                          <td>
                            <span className="zone-code">
                              {region.zone_id}
                            </span>
                          </td>

                          <td>
                            <ProbabilityCell
                              value={
                                region.ml_probability
                              }
                            />
                          </td>

                          <td>
                            <strong>
                              {
                                region
                                  .compound_risk_score
                              }
                            </strong>
                          </td>

                          <td>
                            <RiskBadge
                              level={
                                region.risk_level
                              }
                            />
                          </td>

                          <td>
                            {
                              region
                                .workers_exposed
                            }
                          </td>

                          <td className="decision-cell">
                            {region.final_decision}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}

            <div className="table-footer">
              Showing {filteredRegions.length} of{" "}
              {overview.regions.length} assessments
            </div>
          </section>
        </>
      )}
    </main>
  );
}

interface MetricCardProps {
  label: string;
  value: string | number;
  description?: string;
  variant?: "default" | "safe" | "warning" | "danger";
}

function MetricCard({
  label,
  value,
  description,
  variant = "default",
}: MetricCardProps) {
  return (
    <article
      className={`ml-metric-card metric-${variant}`}
    >
      <span>{label}</span>

      <strong>{value}</strong>

      {description && <p>{description}</p>}
    </article>
  );
}

function RiskBadge({
  level,
}: {
  level: string;
}) {
  return (
    <span
      className={`risk-badge risk-${level.toLowerCase()}`}
    >
      {level}
    </span>
  );
}

function ProbabilityCell({
  value,
}: {
  value: number;
}) {
  const normalizedValue = Math.max(
    0,
    Math.min(100, value),
  );

  return (
    <div className="probability-cell">
      <strong>{normalizedValue}%</strong>

      <div className="probability-track">
        <span
          style={{
            width: `${normalizedValue}%`,
          }}
        />
      </div>
    </div>
  );
}

interface RiskDistributionRowProps {
  label: string;
  value: number;
  total: number;
  className: string;
}

function RiskDistributionRow({
  label,
  value,
  total,
  className,
}: RiskDistributionRowProps) {
  const percentage =
    total > 0
      ? Math.round((value / total) * 100)
      : 0;

  return (
    <div className="distribution-row">
      <div className="distribution-label">
        <span>{label}</span>

        <strong>
          {value} ({percentage}%)
        </strong>
      </div>

      <div className="distribution-track">
        <span
          className={className}
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
}

function EmptyState({
  title,
  description,
}: EmptyStateProps) {
  return (
    <div className="empty-overview">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

export default CommandCenter;