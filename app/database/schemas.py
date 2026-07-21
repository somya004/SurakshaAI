from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Parent class for all database tables.

    Every SQLAlchemy table that we create later will inherit from Base.
    """

    pass


class SensorReading(Base):
    """
    Stores one industrial sensor-reading record.

    For now, the table contains the most important common sensor fields.
    More fields and relationships will be added later.
    """

    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    equipment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    sensor_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    pressure: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    humidity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    vibration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    gas: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    sparks: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    motor_current: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    rpm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    coolant_flow_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    equipment_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="api"
    )
    
class RiskEvent(Base):
    """
    Stores warning, high and critical safety events.

    A risk event is created automatically after a sensor reading
    is analysed by the compound-risk engine.
    """

    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    equipment_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    sensor_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )

    predicted_event: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    contributing_factors: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    recommended_action: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    requires_acknowledgement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    acknowledged_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
class Permit(Base):
    """
    Stores Permit-to-Work records.

    Examples:
    - hot work
    - confined-space entry
    - electrical work
    - work at height
    - excavation
    - lifting operation
    """

    __tablename__ = "permits"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    permit_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    equipment_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    permit_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    work_description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    issue_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    expiry_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    permit_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True
    )

    issuer_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    approver_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    contractor_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    worker_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    gas_test_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    gas_test_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    isolation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    isolation_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    ppe_required: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    hot_work_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )

    confined_space_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium"
    )


class MaintenanceOrder(Base):
    """
    Stores equipment-maintenance and isolation information.
    """

    __tablename__ = "maintenance_orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    work_order_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    equipment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    maintenance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    failure_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    reported_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    maintenance_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="scheduled",
        index=True
    )

    equipment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="operational"
    )

    lockout_tagout_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    lockout_tagout_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium"
    )

    assigned_team: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    maintenance_overdue_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
class Worker(Base):
    """
    Stores worker profile, training and authorisation data.
    """

    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    worker_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    worker_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    employer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    job_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    experience_years: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    safety_training_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    hot_work_authorized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    confined_space_authorized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    electrical_work_authorized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    work_at_height_authorized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    training_expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    medical_clearance_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )


class WorkerLocation(Base):
    """
    Stores the latest or historical worker-location updates.

    Location may later come from:
    - RFID
    - BLE beacon
    - GPS
    - access-control system
    - CCTV person tracking
    """

    __tablename__ = "worker_locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    worker_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    location_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    entry_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="inside",
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


class WorkerPPEStatus(Base):
    """
    Stores PPE status.

    Initially this can be entered manually.
    Later it will be updated automatically by the YOLO CCTV model.
    """

    __tablename__ = "worker_ppe_status"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    worker_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    helmet_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    safety_vest_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    gloves_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    goggles_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    safety_shoes_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    detection_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


class ShiftRecord(Base):
    """
    Stores worker shift, attendance and handover information.
    """

    __tablename__ = "shift_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    shift_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    worker_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    shift_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    shift_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    shift_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    attendance_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="present",
    )

    fatigue_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    handover_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    handover_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
class Incident(Base):
    """
    Stores industrial safety incidents created from
    high or critical compound-risk events.

    Multiple related risk events may update the same
    open incident instead of creating duplicates.
    """

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    risk_event_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    equipment_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    sensor_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    incident_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        index=True,
    )

    final_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    contributing_factors: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recommended_actions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    exposed_worker_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    event_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    acknowledged_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    acknowledgement_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    corrective_actions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    latest_event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
class Alert(Base):
    """
    Stores alerts generated from risk events and incidents.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    risk_event_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    equipment_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    recipient_roles: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    notification_channels: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    acknowledged_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    acknowledgement_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    current_escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    maximum_escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    next_escalation_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class AlertEscalationLog(Base):
    """
    Stores every alert delivery and escalation attempt.
    """

    __tablename__ = "alert_escalation_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    alert_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    recipient_roles: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    notification_channels: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    delivery_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    delivery_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
class ResponseAction(Base):
    """
    Stores emergency, mitigation and corrective actions
    assigned for an industrial safety incident.
    """

    __tablename__ = "response_actions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    alert_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    equipment_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    assigned_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_automatically: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    verification_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    completion_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    verification_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
class PlantZone(Base):
    """
    Stores the physical zones used by the plant-map system.
    """

    __tablename__ = "plant_zones"

    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "zone_id",
            name="uq_plant_zone",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    zone_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    zone_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    geometry: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    floor_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )    

class CommandCenterAssessment(Base):
    """Persists the latest and historical ML command-center assessments."""

    __tablename__ = "command_center_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    factory: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    compound_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    workers_exposed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

