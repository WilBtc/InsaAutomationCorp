"""
Telemetry service for the Alkhorayef ESP IoT Platform.

This module handles business logic for ESP telemetry data ingestion,
retrieval, and analysis.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.core import (
    get_logger,
    ValidationError,
    DatabaseError,
    NotFoundError,
    log_performance
)
from app.db import (
    get_db_pool,
    ESPTelemetry,
    TelemetryBatch,
    WellSummary,
    SQL_QUERIES
)


logger = get_logger(__name__)


class TelemetryService:
    """Service for managing ESP telemetry data."""

    def __init__(self) -> None:
        """Initialize telemetry service."""
        self.db_pool = get_db_pool()

    def ingest_telemetry(
        self,
        telemetry: ESPTelemetry
    ) -> int:
        """
        Ingest a single telemetry reading.

        Args:
            telemetry: ESP telemetry data

        Returns:
            Database ID of inserted record

        Raises:
            ValidationError: If telemetry data is invalid
            DatabaseError: If insertion fails
        """
        start_time = datetime.now()

        # Validate telemetry data
        errors = telemetry.validate()
        if errors:
            raise ValidationError(
                message="Telemetry validation failed",
                details={"errors": errors}
            )

        try:
            # Insert telemetry
            result = self.db_pool.execute_query(
                SQL_QUERIES["insert_telemetry"],
                params=(
                    telemetry.well_id,
                    telemetry.timestamp,
                    telemetry.flow_rate,
                    telemetry.pip,
                    telemetry.motor_current,
                    telemetry.motor_temp,
                    telemetry.vibration,
                    telemetry.vsd_frequency,
                    telemetry.flow_variance,
                    telemetry.torque,
                    telemetry.gor
                ),
                fetch=True
            )

            telemetry_id = result[0][0] if result else None

            duration = (datetime.now() - start_time).total_seconds() * 1000
            log_performance(
                logger,
                "ingest_telemetry",
                duration,
                well_id=telemetry.well_id
            )

            logger.info(
                "Telemetry ingested successfully",
                extra={
                    "extra_fields": {
                        "well_id": telemetry.well_id,
                        "telemetry_id": telemetry_id
                    }
                }
            )

            return telemetry_id

        except Exception as e:
            logger.error(
                "Failed to ingest telemetry",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": telemetry.well_id
                    }
                }
            )
            raise DatabaseError(
                message="Failed to ingest telemetry",
                operation="INSERT",
                details={"well_id": telemetry.well_id}
            ) from e

    def ingest_batch(
        self,
        batch: TelemetryBatch
    ) -> Dict[str, Any]:
        """
        Ingest a batch of telemetry readings.

        Args:
            batch: Batch of telemetry readings

        Returns:
            Dictionary with ingestion results

        Raises:
            ValidationError: If batch validation fails
            DatabaseError: If batch insertion fails
        """
        start_time = datetime.now()

        # Validate batch
        validation_errors = batch.validate()
        if validation_errors:
            raise ValidationError(
                message="Batch validation failed",
                details={"errors": validation_errors}
            )

        try:
            # Prepare batch parameters
            params_list = [
                (
                    reading.well_id,
                    reading.timestamp,
                    reading.flow_rate,
                    reading.pip,
                    reading.motor_current,
                    reading.motor_temp,
                    reading.vibration,
                    reading.vsd_frequency,
                    reading.flow_variance,
                    reading.torque,
                    reading.gor
                )
                for reading in batch.readings
            ]

            # Execute batch insert
            self.db_pool.execute_many(
                SQL_QUERIES["insert_telemetry"],
                params_list
            )

            duration = (datetime.now() - start_time).total_seconds() * 1000
            log_performance(
                logger,
                "ingest_batch",
                duration,
                batch_size=batch.size
            )

            logger.info(
                "Batch ingested successfully",
                extra={
                    "extra_fields": {
                        "batch_size": batch.size,
                        "duration_ms": duration
                    }
                }
            )

            return {
                "success": True,
                "batch_size": batch.size,
                "duration_ms": duration
            }

        except Exception as e:
            logger.error(
                "Failed to ingest batch",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "batch_size": batch.size
                    }
                }
            )
            raise DatabaseError(
                message="Failed to ingest batch",
                operation="BATCH_INSERT",
                details={"batch_size": batch.size}
            ) from e

    def get_latest_telemetry(
        self,
        well_id: str
    ) -> Optional[ESPTelemetry]:
        """
        Get the latest telemetry reading for a well.

        Args:
            well_id: Well identifier

        Returns:
            Latest telemetry or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            result = self.db_pool.execute_query(
                SQL_QUERIES["get_latest_telemetry"],
                params=(well_id,),
                fetch=True,
                return_dict=True
            )

            if not result:
                logger.info(
                    "No telemetry found for well",
                    extra={"extra_fields": {"well_id": well_id}}
                )
                return None

            row = result[0]
            return ESPTelemetry(
                id=row["id"],
                well_id=row["well_id"],
                timestamp=row["timestamp"],
                flow_rate=row["flow_rate"],
                pip=row["pip"],
                motor_current=row["motor_current"],
                motor_temp=row["motor_temp"],
                vibration=row["vibration"],
                vsd_frequency=row["vsd_frequency"],
                flow_variance=row["flow_variance"],
                torque=row["torque"],
                gor=row["gor"]
            )

        except Exception as e:
            logger.error(
                "Failed to get latest telemetry",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Failed to get latest telemetry",
                operation="SELECT",
                details={"well_id": well_id}
            ) from e

    def get_telemetry_history(
        self,
        well_id: str,
        hours: int = 24
    ) -> List[ESPTelemetry]:
        """
        Get telemetry history for a well.

        Args:
            well_id: Well identifier
            hours: Number of hours of history to retrieve

        Returns:
            List of telemetry readings

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If query fails
        """
        if hours < 1:
            raise ValidationError(
                message="Hours must be at least 1",
                field="hours"
            )

        start_time = datetime.now() - timedelta(hours=hours)

        try:
            result = self.db_pool.execute_query(
                SQL_QUERIES["get_telemetry_history"],
                params=(well_id, start_time),
                fetch=True,
                return_dict=True
            )

            telemetry_list = [
                ESPTelemetry(
                    id=row["id"],
                    well_id=row["well_id"],
                    timestamp=row["timestamp"],
                    flow_rate=row["flow_rate"],
                    pip=row["pip"],
                    motor_current=row["motor_current"],
                    motor_temp=row["motor_temp"],
                    vibration=row["vibration"],
                    vsd_frequency=row["vsd_frequency"],
                    flow_variance=row["flow_variance"],
                    torque=row["torque"],
                    gor=row["gor"]
                )
                for row in result
            ]

            logger.info(
                "Retrieved telemetry history",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "hours": hours,
                        "count": len(telemetry_list)
                    }
                }
            )

            return telemetry_list

        except Exception as e:
            logger.error(
                "Failed to get telemetry history",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "hours": hours
                    }
                }
            )
            raise DatabaseError(
                message="Failed to get telemetry history",
                operation="SELECT",
                details={"well_id": well_id, "hours": hours}
            ) from e

    def get_well_summary(
        self,
        well_id: str
    ) -> WellSummary:
        """
        Get summary statistics for a well.

        Args:
            well_id: Well identifier

        Returns:
            Well summary statistics

        Raises:
            NotFoundError: If well has no data
            DatabaseError: If query fails
        """
        try:
            result = self.db_pool.execute_query(
                SQL_QUERIES["get_well_summary"],
                params=(well_id,),
                fetch=True,
                return_dict=True
            )

            if not result:
                raise NotFoundError(
                    message=f"No data found for well: {well_id}",
                    resource_type="well",
                    resource_id=well_id
                )

            row = result[0]
            return WellSummary(
                well_id=row["well_id"],
                first_reading=row["first_reading"],
                last_reading=row["last_reading"],
                total_readings=row["total_readings"],
                avg_flow_rate=row["avg_flow_rate"],
                avg_motor_temp=row["avg_motor_temp"],
                avg_vibration=row["avg_vibration"],
                diagnostic_count=row["diagnostic_count"],
                critical_diagnostic_count=row["critical_diagnostic_count"]
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to get well summary",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Failed to get well summary",
                operation="SELECT",
                details={"well_id": well_id}
            ) from e
