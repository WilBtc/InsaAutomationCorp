"""
Diagnostic service for the Alkhorayef ESP IoT Platform.

This module handles business logic for ESP diagnostic analysis,
result storage, and retrieval.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from app.core import (
    get_logger,
    ValidationError,
    DatabaseError,
    NotFoundError,
    log_performance
)
from app.db import (
    get_db_pool,
    DiagnosticResult,
    DiagnosisType,
    Severity,
    ESPTelemetry,
    SQL_QUERIES
)


logger = get_logger(__name__)


class DiagnosticService:
    """Service for managing ESP diagnostic analysis."""

    def __init__(self) -> None:
        """Initialize diagnostic service."""
        self._db_pool = None

    @property
    def db_pool(self):
        """Lazy-load database connection pool on first access."""
        if self._db_pool is None:
            self._db_pool = get_db_pool()
        return self._db_pool

    def store_diagnostic_result(
        self,
        diagnostic: DiagnosticResult
    ) -> int:
        """
        Store a diagnostic result.

        Args:
            diagnostic: Diagnostic result to store

        Returns:
            Database ID of inserted record

        Raises:
            ValidationError: If diagnostic data is invalid
            DatabaseError: If insertion fails
        """
        start_time = datetime.now()

        # Validate confidence score
        if not (0 <= diagnostic.confidence <= 1):
            raise ValidationError(
                message="Confidence must be between 0 and 1",
                field="confidence"
            )

        try:
            # Convert actions and telemetry snapshot to JSON
            actions_json = json.dumps(diagnostic.actions)
            snapshot_json = json.dumps(diagnostic.telemetry_snapshot)

            # Insert diagnostic result
            result = self.db_pool.execute_query(
                SQL_QUERIES["insert_diagnostic"],
                params=(
                    diagnostic.well_id,
                    diagnostic.timestamp,
                    diagnostic.diagnosis.value,
                    diagnostic.confidence,
                    diagnostic.severity.value,
                    actions_json,
                    snapshot_json,
                    diagnostic.resolution_time,
                    diagnostic.notes
                ),
                fetch=True
            )

            diagnostic_id = result[0][0] if result else None

            duration = (datetime.now() - start_time).total_seconds() * 1000
            log_performance(
                logger,
                "store_diagnostic",
                duration,
                well_id=diagnostic.well_id,
                diagnosis=diagnostic.diagnosis.value
            )

            logger.info(
                "Diagnostic result stored successfully",
                extra={
                    "extra_fields": {
                        "well_id": diagnostic.well_id,
                        "diagnostic_id": diagnostic_id,
                        "diagnosis": diagnostic.diagnosis.value,
                        "severity": diagnostic.severity.value,
                        "confidence": diagnostic.confidence
                    }
                }
            )

            return diagnostic_id

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Failed to store diagnostic result",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": diagnostic.well_id,
                        "diagnosis": diagnostic.diagnosis.value
                    }
                }
            )
            raise DatabaseError(
                message="Failed to store diagnostic result",
                operation="INSERT",
                details={"well_id": diagnostic.well_id}
            ) from e

    def get_diagnostic_history(
        self,
        well_id: str,
        limit: int = 10
    ) -> List[DiagnosticResult]:
        """
        Get diagnostic history for a well.

        Args:
            well_id: Well identifier
            limit: Maximum number of results to return

        Returns:
            List of diagnostic results

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If query fails
        """
        if limit < 1 or limit > 1000:
            raise ValidationError(
                message="Limit must be between 1 and 1000",
                field="limit"
            )

        try:
            result = self.db_pool.execute_query(
                SQL_QUERIES["get_diagnostic_history"],
                params=(well_id, limit),
                fetch=True,
                return_dict=True
            )

            diagnostics = [
                DiagnosticResult(
                    id=row["id"],
                    well_id=row["well_id"],
                    timestamp=row["timestamp"],
                    diagnosis=DiagnosisType(row["diagnosis"]),
                    confidence=row["confidence"],
                    severity=Severity(row["severity"]),
                    actions=json.loads(row["actions"]) if isinstance(row["actions"], str) else row["actions"],
                    telemetry_snapshot=json.loads(row["telemetry_snapshot"]) if isinstance(row["telemetry_snapshot"], str) else row["telemetry_snapshot"],
                    resolution_time=row["resolution_time"],
                    notes=row.get("notes")
                )
                for row in result
            ]

            logger.info(
                "Retrieved diagnostic history",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "limit": limit,
                        "count": len(diagnostics)
                    }
                }
            )

            return diagnostics

        except Exception as e:
            logger.error(
                "Failed to get diagnostic history",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "limit": limit
                    }
                }
            )
            raise DatabaseError(
                message="Failed to get diagnostic history",
                operation="SELECT",
                details={"well_id": well_id}
            ) from e

    def analyze_telemetry(
        self,
        telemetry: ESPTelemetry
    ) -> DiagnosticResult:
        """
        Analyze telemetry data and generate diagnostic result.

        This is a simplified decision tree for demonstration.
        In production, this would integrate with the AI/ML diagnostic system.

        Args:
            telemetry: ESP telemetry data

        Returns:
            Diagnostic result

        Raises:
            ValidationError: If telemetry is invalid
        """
        # Validate telemetry
        errors = telemetry.validate()
        if errors:
            raise ValidationError(
                message="Telemetry validation failed",
                details={"errors": errors}
            )

        # Simple decision tree logic
        diagnosis = DiagnosisType.NORMAL
        confidence = 0.95
        severity = Severity.INFO
        actions = ["Continue normal operations"]
        resolution_time = "N/A"

        # Check for gas lock
        if telemetry.gor > 300 and telemetry.pip < 200:
            diagnosis = DiagnosisType.GAS_LOCK
            confidence = 0.85
            severity = Severity.HIGH
            actions = [
                "Reduce VSD frequency by 10%",
                "Monitor GOR levels",
                "Consider gas separator installation"
            ]
            resolution_time = "2-4 hours"

        # Check for pump wear
        elif telemetry.flow_rate < 1000 and telemetry.vibration > 5.0:
            diagnosis = DiagnosisType.PUMP_WEAR
            confidence = 0.75
            severity = Severity.MEDIUM
            actions = [
                "Schedule pump inspection",
                "Monitor vibration trends",
                "Plan for pump replacement if needed"
            ]
            resolution_time = "1-2 weeks"

        # Check for motor issues
        elif telemetry.motor_temp > 150 or telemetry.motor_current > 80:
            diagnosis = DiagnosisType.MOTOR_ISSUE
            confidence = 0.90
            severity = Severity.CRITICAL
            actions = [
                "Reduce motor load immediately",
                "Check cooling system",
                "Inspect motor windings",
                "Consider emergency shutdown if temperature exceeds 180°C"
            ]
            resolution_time = "Immediate"

        # Check for VSD issues
        elif telemetry.vsd_frequency < 30 and telemetry.flow_rate < 800:
            diagnosis = DiagnosisType.VSD_ISSUE
            confidence = 0.80
            severity = Severity.HIGH
            actions = [
                "Inspect VSD controller",
                "Check input power quality",
                "Verify frequency setpoint"
            ]
            resolution_time = "4-8 hours"

        # Check for vibration issues
        elif telemetry.vibration > 8.0:
            diagnosis = DiagnosisType.VIBRATION_ISSUE
            confidence = 0.88
            severity = Severity.HIGH
            actions = [
                "Reduce operating speed",
                "Inspect pump alignment",
                "Check for bearing wear",
                "Monitor for rapid deterioration"
            ]
            resolution_time = "2-6 hours"

        # Check for low flow
        elif telemetry.flow_rate < 500:
            diagnosis = DiagnosisType.LOW_FLOW
            confidence = 0.70
            severity = Severity.MEDIUM
            actions = [
                "Check for blockages",
                "Verify wellbore conditions",
                "Consider increasing VSD frequency"
            ]
            resolution_time = "4-12 hours"

        diagnostic = DiagnosticResult(
            well_id=telemetry.well_id,
            timestamp=datetime.now(),
            diagnosis=diagnosis,
            confidence=confidence,
            severity=severity,
            actions=actions,
            telemetry_snapshot=telemetry.to_dict(),
            resolution_time=resolution_time
        )

        logger.info(
            "Telemetry analyzed",
            extra={
                "extra_fields": {
                    "well_id": telemetry.well_id,
                    "diagnosis": diagnosis.value,
                    "confidence": confidence,
                    "severity": severity.value
                }
            }
        )

        return diagnostic

    def get_critical_diagnostics(
        self,
        limit: int = 50
    ) -> List[DiagnosticResult]:
        """
        Get recent critical diagnostic results across all wells.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of critical diagnostic results

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If query fails
        """
        if limit < 1 or limit > 1000:
            raise ValidationError(
                message="Limit must be between 1 and 1000",
                field="limit"
            )

        query = """
            SELECT * FROM diagnostic_results
            WHERE severity IN ('critical', 'high')
            ORDER BY timestamp DESC
            LIMIT %s
        """

        try:
            result = self.db_pool.execute_query(
                query,
                params=(limit,),
                fetch=True,
                return_dict=True
            )

            diagnostics = [
                DiagnosticResult(
                    id=row["id"],
                    well_id=row["well_id"],
                    timestamp=row["timestamp"],
                    diagnosis=DiagnosisType(row["diagnosis"]),
                    confidence=row["confidence"],
                    severity=Severity(row["severity"]),
                    actions=json.loads(row["actions"]) if isinstance(row["actions"], str) else row["actions"],
                    telemetry_snapshot=json.loads(row["telemetry_snapshot"]) if isinstance(row["telemetry_snapshot"], str) else row["telemetry_snapshot"],
                    resolution_time=row["resolution_time"],
                    notes=row.get("notes")
                )
                for row in result
            ]

            logger.info(
                "Retrieved critical diagnostics",
                extra={
                    "extra_fields": {
                        "limit": limit,
                        "count": len(diagnostics)
                    }
                }
            )

            return diagnostics

        except Exception as e:
            logger.error(
                "Failed to get critical diagnostics",
                exc_info=e,
                extra={"extra_fields": {"limit": limit}}
            )
            raise DatabaseError(
                message="Failed to get critical diagnostics",
                operation="SELECT"
            ) from e
