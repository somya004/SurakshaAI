export interface ActivePermit {
  permit_id: string;
  permit_type: string;
  status: string;
}

export interface SensorAssessmentRequest {
  factory: string;
  region: string;
  zone_id: string;

  shift: "day" | "night";
  workers: number;
  experience_level: "junior" | "senior";
  training: "yes" | "no";

  temperature: number;
  pressure: number;
  humidity: number;
  vibration: number;
  machine_speed: number;
  equipment_age: number;
  service_days: number;
  gas: number;
  sparks: number;
  alarm: "on" | "off";

  motor_current: number;
  rpm: number;
  ambient_humidity: number;
  tool_wear: number;
  coolant_flow_rate: number;
  voltage_fluctuation_percent: number;
  operator_experience_years: number;

  timestamp: string;
  active_permit: ActivePermit | null;
}

export interface TriggeredRule {
  rule_id: string;
  severity: string;
  message: string;
}

export interface CommandCenterAssessment {
  sensor_ingestion: {
    status: string;
    factory: string;
    region: string;
    zone_id: string;
    timestamp: string;
  };

  ml_prediction: {
    model_name: string;
    predicted_class: number;
    predicted_event: string;
    accident_probability: number;
  };

  anomaly_detection: {
    available: boolean;
    is_anomaly: boolean;
    raw_anomaly_score: number | null;
    anomaly_component_score: number;
  };

  rule_detection: {
    triggered: boolean;
    triggered_rule_count: number;
    rule_score: number;
    triggered_rules: TriggeredRule[];
  };

  permit_conflict: {
    conflict_detected: boolean;
    permit_id: string | null;
    permit_type: string | null;
    reason: string;
    recommended_action: string;
  };

  worker_exposure: {
    workers_present: number;
    workers_exposed: number;
    evacuation_required: boolean;
    training_status: string;
    experience_level: string;
  };

  compound_assessment: {
    ml_score: number;
    anomaly_score: number;
    rule_score: number;
    operational_score: number;
    compound_risk_score: number;
    risk_level: string;
    final_decision: string;
    contributing_factors: string[];
  };
}

export interface RegionOverview {
  factory: string;
  region: string;
  zone_id: string;
  timestamp: string;
  ml_probability: number;
  is_anomaly: boolean;
  compound_risk_score: number;
  risk_level: string;
  workers_exposed: number;
  final_decision: string;
}

export interface CommandCenterOverview {
  summary: {
    total_regions: number;
    safe_regions: number;
    alert_regions: number;
    high_regions: number;
    critical_regions: number;
    workers_exposed: number;
  };

  safe_regions: RegionOverview[];
  alert_regions: RegionOverview[];
  regions: RegionOverview[];
}

export interface ModelMetrics {
  available: boolean;
  model_name: string | null;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  roc_auc?: number;
  pr_auc?: number;
  false_negative_rate?: number;

  confusion_matrix?: {
    true_negative: number;
    false_positive: number;
    false_negative: number;
    true_positive: number;
  };
}