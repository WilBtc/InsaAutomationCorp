"""
Diagnostics API endpoints for the Alkhorayef ESP IoT Platform.

This module provides REST API endpoints for ESP diagnostic analysis
and result retrieval.
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
from app.db import ESPTelemetry, DiagnosticResult
from app.services import DiagnosticService, TelemetryService


logger = get_logger(__name__)
diagnostics_bp = Blueprint("diagnostics", __name__, url_prefix="/api/v1/diagnostics")
diagnostic_service = DiagnosticService()
telemetry_service = TelemetryService()


@diagnostics_bp.route("/analyze", methods=["POST"])
def analyze_telemetry() -> Response:
    """
    Analyze ESP telemetry data and generate diagnostic result.

    Request body (JSON):
    {
        "well_id": "WELL-001",
        "telemetry": {
            "timestamp": "2025-11-20T14:30:00Z",  // Optional
            "flow_rate": 2500.5,
            "pip": 250.0,
            "motor_current": 45.2,
            "motor_temp": 85.5,
            "vibration": 3.2,
            "vsd_frequency": 60.0,
            "flow_variance": 15.0,
            "torque": 120.5,
            "gor": 150.0
        },
        "store_result": true  // Optional, default: true
    }

    Returns:
        JSON response with diagnostic result
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError(
                message="Request body is required",
                details={"content_type": request.content_type}
            )

        well_id = data.get("well_id")
        if not well_id:
            raise ValidationError(
                message="well_id is required",
                field="well_id"
            )

        telemetry_data = data.get("telemetry")
        if not telemetry_data:
            raise ValidationError(
                message="telemetry data is required",
                field="telemetry"
            )

        store_result = data.get("store_result", True)

        # Parse timestamp
        timestamp = telemetry_data.get("timestamp")
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
            well_id=well_id,
            timestamp=timestamp,
            flow_rate=float(telemetry_data.get("flow_rate", 0)),
            pip=float(telemetry_data.get("pip", 0)),
            motor_current=float(telemetry_data.get("motor_current", 0)),
            motor_temp=float(telemetry_data.get("motor_temp", 0)),
            vibration=float(telemetry_data.get("vibration", 0)),
            vsd_frequency=float(telemetry_data.get("vsd_frequency", 0)),
            flow_variance=float(telemetry_data.get("flow_variance", 0)),
            torque=float(telemetry_data.get("torque", 0)),
            gor=float(telemetry_data.get("gor", 0))
        )

        # Analyze telemetry
        diagnostic = diagnostic_service.analyze_telemetry(telemetry)

        # Store result if requested
        diagnostic_id = None
        if store_result:
            diagnostic_id = diagnostic_service.store_diagnostic_result(diagnostic)

        # Log audit trail
        log_audit(
            logger,
            action="ANALYZE_TELEMETRY",
            resource_type="diagnostic",
            resource_id=str(diagnostic_id) if diagnostic_id else None,
            well_id=well_id,
            diagnosis=diagnostic.diagnosis.value
        )

        response_data = {
            "success": True,
            "well_id": well_id,
            "diagnostic": diagnostic.to_dict()
        }

        if diagnostic_id:
            response_data["diagnostic_id"] = diagnostic_id

        return jsonify(response_data), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in diagnostic analysis", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@diagnostics_bp.route("/wells/<well_id>/analyze-latest", methods=["POST"])
def analyze_latest(well_id: str) -> Response:
    """
    Analyze the latest telemetry reading for a well.

    Args:
        well_id: Well identifier

    Query parameters:
        store_result: Whether to store the diagnostic result (default: true)

    Returns:
        JSON response with diagnostic result
    """
    try:
        store_result = request.args.get("store_result", "true").lower() == "true"

        # Get latest telemetry
        telemetry = telemetry_service.get_latest_telemetry(well_id)

        if telemetry is None:
            raise NotFoundError(
                message=f"No telemetry found for well: {well_id}",
                resource_type="telemetry",
                resource_id=well_id
            )

        # Analyze telemetry
        diagnostic = diagnostic_service.analyze_telemetry(telemetry)

        # Store result if requested
        diagnostic_id = None
        if store_result:
            diagnostic_id = diagnostic_service.store_diagnostic_result(diagnostic)

        # Log audit trail
        log_audit(
            logger,
            action="ANALYZE_LATEST",
            resource_type="diagnostic",
            resource_id=str(diagnostic_id) if diagnostic_id else None,
            well_id=well_id,
            diagnosis=diagnostic.diagnosis.value
        )

        response_data = {
            "success": True,
            "well_id": well_id,
            "diagnostic": diagnostic.to_dict()
        }

        if diagnostic_id:
            response_data["diagnostic_id"] = diagnostic_id

        return jsonify(response_data), 200

    except NotFoundError as e:
        return jsonify(e.to_dict()), 404

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error analyzing latest telemetry", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@diagnostics_bp.route("/wells/<well_id>/history", methods=["GET"])
def get_history(well_id: str) -> Response:
    """
    Get diagnostic history for a well.

    Args:
        well_id: Well identifier

    Query parameters:
        limit: Maximum number of results (default: 10, max: 100)

    Returns:
        JSON response with diagnostic history
    """
    try:
        limit = request.args.get("limit", default=10, type=int)

        # Validate limit parameter
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        diagnostics = diagnostic_service.get_diagnostic_history(well_id, limit)

        return jsonify({
            "success": True,
            "well_id": well_id,
            "limit": limit,
            "count": len(diagnostics),
            "diagnostics": [d.to_dict() for d in diagnostics]
        }), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error retrieving diagnostic history", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@diagnostics_bp.route("/critical", methods=["GET"])
def get_critical() -> Response:
    """
    Get recent critical diagnostic results across all wells.

    Query parameters:
        limit: Maximum number of results (default: 50, max: 100)

    Returns:
        JSON response with critical diagnostic results
    """
    try:
        limit = request.args.get("limit", default=50, type=int)

        # Validate limit parameter
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        diagnostics = diagnostic_service.get_critical_diagnostics(limit)

        return jsonify({
            "success": True,
            "limit": limit,
            "count": len(diagnostics),
            "diagnostics": [d.to_dict() for d in diagnostics]
        }), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error retrieving critical diagnostics", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500
