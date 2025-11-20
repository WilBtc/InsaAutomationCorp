"""
Database models for the Alkhorayef ESP IoT Platform.

This module defines data models for ESP telemetry and diagnostics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class DiagnosisType(str, Enum):
    """Enumeration of possible ESP diagnoses."""

    NORMAL = "NORMAL"
    GAS_LOCK = "GAS_LOCK"
    PUMP_WEAR = "PUMP_WEAR"
    MOTOR_ISSUE = "MOTOR_ISSUE"
    VSD_ISSUE = "VSD_ISSUE"
    VIBRATION_ISSUE = "VIBRATION_ISSUE"
    LOW_FLOW = "LOW_FLOW"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    """Severity levels for diagnostics."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ESPTelemetry:
    """ESP telemetry data model."""

    well_id: str
    timestamp: datetime
    flow_rate: float
    pip: float  # Pump Intake Pressure
    motor_current: float
    motor_temp: float
    vibration: float
    vsd_frequency: float
    flow_variance: float
    torque: float
    gor: float  # Gas-Oil Ratio
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert telemetry to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ESPTelemetry":
        """Create telemetry from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def validate(self) -> List[str]:
        """
        Validate telemetry data ranges.

        Returns:
            List of validation error messages
        """
        errors = []

        if self.flow_rate < 0:
            errors.append("flow_rate must be non-negative")

        if self.pip < 0:
            errors.append("pip (pump intake pressure) must be non-negative")

        if self.motor_current < 0:
            errors.append("motor_current must be non-negative")

        if self.motor_temp < -50 or self.motor_temp > 200:
            errors.append("motor_temp must be between -50 and 200 degrees")

        if self.vibration < 0:
            errors.append("vibration must be non-negative")

        if self.vsd_frequency < 0 or self.vsd_frequency > 120:
            errors.append("vsd_frequency must be between 0 and 120 Hz")

        if self.flow_variance < 0:
            errors.append("flow_variance must be non-negative")

        if self.torque < 0:
            errors.append("torque must be non-negative")

        if self.gor < 0:
            errors.append("gor (gas-oil ratio) must be non-negative")

        return errors


@dataclass
class DiagnosticResult:
    """Diagnostic result data model."""

    well_id: str
    timestamp: datetime
    diagnosis: DiagnosisType
    confidence: float
    severity: Severity
    actions: List[str]
    telemetry_snapshot: Dict[str, Any]
    resolution_time: str
    id: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnostic result to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["diagnosis"] = self.diagnosis.value
        data["severity"] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagnosticResult":
        """Create diagnostic result from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        if isinstance(data.get("diagnosis"), str):
            data["diagnosis"] = DiagnosisType(data["diagnosis"])

        if isinstance(data.get("severity"), str):
            data["severity"] = Severity(data["severity"])

        return cls(**data)

    @property
    def is_critical(self) -> bool:
        """Check if diagnostic is critical."""
        return self.severity in [Severity.CRITICAL, Severity.HIGH]

    @property
    def requires_immediate_action(self) -> bool:
        """Check if diagnostic requires immediate action."""
        return self.severity == Severity.CRITICAL and self.confidence >= 0.8


@dataclass
class WellSummary:
    """Summary statistics for a well."""

    well_id: str
    first_reading: datetime
    last_reading: datetime
    total_readings: int
    avg_flow_rate: float
    avg_motor_temp: float
    avg_vibration: float
    diagnostic_count: int
    critical_diagnostic_count: int
    last_diagnosis: Optional[DiagnosisType] = None
    last_diagnosis_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert well summary to dictionary."""
        data = asdict(self)
        data["first_reading"] = self.first_reading.isoformat()
        data["last_reading"] = self.last_reading.isoformat()
        if self.last_diagnosis:
            data["last_diagnosis"] = self.last_diagnosis.value
        if self.last_diagnosis_time:
            data["last_diagnosis_time"] = self.last_diagnosis_time.isoformat()
        return data


@dataclass
class TelemetryBatch:
    """Batch of telemetry readings for bulk insert."""

    readings: List[ESPTelemetry]

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate all readings in batch.

        Returns:
            Dictionary mapping reading index to error messages
        """
        validation_errors = {}
        for idx, reading in enumerate(self.readings):
            errors = reading.validate()
            if errors:
                validation_errors[str(idx)] = errors
        return validation_errors

    @property
    def is_valid(self) -> bool:
        """Check if all readings in batch are valid."""
        return len(self.validate()) == 0

    @property
    def size(self) -> int:
        """Get batch size."""
        return len(self.readings)


# SQL table creation scripts
SQL_CREATE_TABLES = """
-- ESP Telemetry table
CREATE TABLE IF NOT EXISTS esp_telemetry (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    flow_rate DOUBLE PRECISION NOT NULL,
    pip DOUBLE PRECISION NOT NULL,
    motor_current DOUBLE PRECISION NOT NULL,
    motor_temp DOUBLE PRECISION NOT NULL,
    vibration DOUBLE PRECISION NOT NULL,
    vsd_frequency DOUBLE PRECISION NOT NULL,
    flow_variance DOUBLE PRECISION NOT NULL,
    torque DOUBLE PRECISION NOT NULL,
    gor DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for telemetry
CREATE INDEX IF NOT EXISTS idx_telemetry_well_id ON esp_telemetry(well_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON esp_telemetry(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_well_time ON esp_telemetry(well_id, timestamp DESC);

-- Diagnostic results table
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    diagnosis VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    severity VARCHAR(20) NOT NULL,
    actions JSONB NOT NULL,
    telemetry_snapshot JSONB NOT NULL,
    resolution_time VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for diagnostics
CREATE INDEX IF NOT EXISTS idx_diagnostics_well_id ON diagnostic_results(well_id);
CREATE INDEX IF NOT EXISTS idx_diagnostics_timestamp ON diagnostic_results(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_diagnostics_severity ON diagnostic_results(severity);
CREATE INDEX IF NOT EXISTS idx_diagnostics_well_time ON diagnostic_results(well_id, timestamp DESC);

-- Partitioning function for old data (optional, for future use)
CREATE OR REPLACE FUNCTION archive_old_telemetry(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM esp_telemetry
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
"""


# SQL queries for common operations
SQL_QUERIES = {
    "insert_telemetry": """
        INSERT INTO esp_telemetry (
            well_id, timestamp, flow_rate, pip, motor_current,
            motor_temp, vibration, vsd_frequency, flow_variance, torque, gor
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """,
    "insert_diagnostic": """
        INSERT INTO diagnostic_results (
            well_id, timestamp, diagnosis, confidence, severity,
            actions, telemetry_snapshot, resolution_time, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """,
    "get_latest_telemetry": """
        SELECT * FROM esp_telemetry
        WHERE well_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """,
    "get_telemetry_history": """
        SELECT * FROM esp_telemetry
        WHERE well_id = %s
        AND timestamp >= %s
        ORDER BY timestamp DESC
    """,
    "get_diagnostic_history": """
        SELECT * FROM diagnostic_results
        WHERE well_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """,
    "get_well_summary": """
        SELECT
            t.well_id,
            MIN(t.timestamp) as first_reading,
            MAX(t.timestamp) as last_reading,
            COUNT(*) as total_readings,
            AVG(t.flow_rate) as avg_flow_rate,
            AVG(t.motor_temp) as avg_motor_temp,
            AVG(t.vibration) as avg_vibration,
            (SELECT COUNT(*) FROM diagnostic_results WHERE well_id = t.well_id) as diagnostic_count,
            (SELECT COUNT(*) FROM diagnostic_results WHERE well_id = t.well_id AND severity IN ('critical', 'high')) as critical_diagnostic_count
        FROM esp_telemetry t
        WHERE t.well_id = %s
        GROUP BY t.well_id
    """
}
