"""
Telemetry API endpoints for the Alkhorayef ESP IoT Platform.

This module provides REST API endpoints for ESP telemetry data ingestion
and retrieval.
"""

from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify, Response

from app.core import (
    get_logger,
    ValidationError,
    DatabaseError,
    NotFoundError,
    log_audit
)
from app.db import ESPTelemetry, TelemetryBatch
from app.services import TelemetryService


logger = get_logger(__name__)
telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/v1/telemetry")
telemetry_service = TelemetryService()


@telemetry_bp.route("/ingest", methods=["POST"])
def ingest_telemetry() -> Response:
    """
    Ingest a single ESP telemetry reading.

    Request body (JSON):
    {
        "well_id": "WELL-001",
        "timestamp": "2025-11-20T14:30:00Z",  // Optional, defaults to now
        "flow_rate": 2500.5,
        "pip": 250.0,
        "motor_current": 45.2,
        "motor_temp": 85.5,
        "vibration": 3.2,
        "vsd_frequency": 60.0,
        "flow_variance": 15.0,
        "torque": 120.5,
        "gor": 150.0
    }

    Returns:
        JSON response with ingestion status and telemetry ID
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError(
                message="Request body is required",
                details={"content_type": request.content_type}
            )

        # Parse timestamp if provided
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValidationError(
                    message="Invalid timestamp format",
                    field="timestamp",
                    details={"error": str(e)}
                )
        else:
            timestamp = datetime.utcnow()

        # Create telemetry object
        telemetry = ESPTelemetry(
            well_id=data.get("well_id"),
            timestamp=timestamp,
            flow_rate=float(data.get("flow_rate", 0)),
            pip=float(data.get("pip", 0)),
            motor_current=float(data.get("motor_current", 0)),
            motor_temp=float(data.get("motor_temp", 0)),
            vibration=float(data.get("vibration", 0)),
            vsd_frequency=float(data.get("vsd_frequency", 0)),
            flow_variance=float(data.get("flow_variance", 0)),
            torque=float(data.get("torque", 0)),
            gor=float(data.get("gor", 0))
        )

        # Ingest telemetry
        telemetry_id = telemetry_service.ingest_telemetry(telemetry)

        # Log audit trail
        log_audit(
            logger,
            action="INGEST_TELEMETRY",
            resource_type="telemetry",
            resource_id=str(telemetry_id),
            well_id=telemetry.well_id
        )

        return jsonify({
            "success": True,
            "telemetry_id": telemetry_id,
            "well_id": telemetry.well_id,
            "timestamp": telemetry.timestamp.isoformat()
        }), 201

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in telemetry ingestion", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@telemetry_bp.route("/batch", methods=["POST"])
def ingest_batch() -> Response:
    """
    Ingest a batch of ESP telemetry readings.

    Request body (JSON):
    {
        "readings": [
            { "well_id": "WELL-001", "flow_rate": 2500.5, ... },
            { "well_id": "WELL-001", "flow_rate": 2510.2, ... }
        ]
    }

    Returns:
        JSON response with batch ingestion status
    """
    try:
        data = request.get_json()

        if not data or "readings" not in data:
            raise ValidationError(
                message="Request body must contain 'readings' array",
                field="readings"
            )

        readings_data = data["readings"]
        if not isinstance(readings_data, list):
            raise ValidationError(
                message="'readings' must be an array",
                field="readings"
            )

        if len(readings_data) == 0:
            raise ValidationError(
                message="'readings' array cannot be empty",
                field="readings"
            )

        # Parse readings
        readings = []
        for idx, reading_data in enumerate(readings_data):
            try:
                timestamp = reading_data.get("timestamp")
                if timestamp:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.utcnow()

                reading = ESPTelemetry(
                    well_id=reading_data.get("well_id"),
                    timestamp=timestamp,
                    flow_rate=float(reading_data.get("flow_rate", 0)),
                    pip=float(reading_data.get("pip", 0)),
                    motor_current=float(reading_data.get("motor_current", 0)),
                    motor_temp=float(reading_data.get("motor_temp", 0)),
                    vibration=float(reading_data.get("vibration", 0)),
                    vsd_frequency=float(reading_data.get("vsd_frequency", 0)),
                    flow_variance=float(reading_data.get("flow_variance", 0)),
                    torque=float(reading_data.get("torque", 0)),
                    gor=float(reading_data.get("gor", 0))
                )
                readings.append(reading)
            except (KeyError, ValueError, TypeError) as e:
                raise ValidationError(
                    message=f"Invalid reading at index {idx}",
                    details={"index": idx, "error": str(e)}
                )

        # Create batch and ingest
        batch = TelemetryBatch(readings=readings)
        result = telemetry_service.ingest_batch(batch)

        # Log audit trail
        log_audit(
            logger,
            action="INGEST_BATCH",
            resource_type="telemetry",
            batch_size=batch.size
        )

        return jsonify({
            "success": True,
            "batch_size": result["batch_size"],
            "duration_ms": result["duration_ms"]
        }), 201

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in batch ingestion", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@telemetry_bp.route("/wells/<well_id>/latest", methods=["GET"])
def get_latest(well_id: str) -> Response:
    """
    Get the latest telemetry reading for a well.

    Args:
        well_id: Well identifier

    Returns:
        JSON response with latest telemetry data
    """
    try:
        telemetry = telemetry_service.get_latest_telemetry(well_id)

        if telemetry is None:
            raise NotFoundError(
                message=f"No telemetry found for well: {well_id}",
                resource_type="telemetry",
                resource_id=well_id
            )

        return jsonify({
            "success": True,
            "telemetry": telemetry.to_dict()
        }), 200

    except NotFoundError as e:
        return jsonify(e.to_dict()), 404

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error retrieving latest telemetry", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@telemetry_bp.route("/wells/<well_id>/history", methods=["GET"])
def get_history(well_id: str) -> Response:
    """
    Get telemetry history for a well.

    Query parameters:
        hours: Number of hours of history (default: 24, max: 168)

    Args:
        well_id: Well identifier

    Returns:
        JSON response with telemetry history
    """
    try:
        hours = request.args.get("hours", default=24, type=int)

        # Validate hours parameter
        if hours < 1:
            hours = 1
        elif hours > 168:  # Max 7 days
            hours = 168

        telemetry_list = telemetry_service.get_telemetry_history(well_id, hours)

        return jsonify({
            "success": True,
            "well_id": well_id,
            "hours": hours,
            "count": len(telemetry_list),
            "telemetry": [t.to_dict() for t in telemetry_list]
        }), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error retrieving telemetry history", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@telemetry_bp.route("/wells/<well_id>/summary", methods=["GET"])
def get_summary(well_id: str) -> Response:
    """
    Get summary statistics for a well.

    Args:
        well_id: Well identifier

    Returns:
        JSON response with well summary statistics
    """
    try:
        summary = telemetry_service.get_well_summary(well_id)

        return jsonify({
            "success": True,
            "summary": summary.to_dict()
        }), 200

    except NotFoundError as e:
        return jsonify(e.to_dict()), 404

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error retrieving well summary", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500
