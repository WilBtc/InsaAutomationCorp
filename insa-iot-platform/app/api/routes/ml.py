"""
Machine Learning API endpoints for the Alkhorayef ESP IoT Platform.

This module provides REST API endpoints for ML/AI analytics including:
- Anomaly detection
- Predictive maintenance
- Performance optimization
- Model management
"""

from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify, Response

from app.core import (
    get_logger,
    ValidationError,
    DatabaseError,
    NotFoundError,
    log_audit,
    require_auth,
    require_role,
    UserRole
)
from app.services.ml import (
    AnomalyDetectionService,
    PredictiveMaintenanceService,
    PerformanceOptimizerService,
)


logger = get_logger(__name__)
ml_bp = Blueprint("ml", __name__, url_prefix="/api/v1/ml")

# Initialize ML services
anomaly_service = AnomalyDetectionService()
predictive_service = PredictiveMaintenanceService()
performance_service = PerformanceOptimizerService()


@ml_bp.route("/train/<well_id>", methods=["POST"])
@require_auth
@require_role([UserRole.ADMIN, UserRole.OPERATOR])
def train_models(well_id: str) -> Response:
    """
    Train all ML models for a specific well.

    This endpoint trains:
    - Anomaly detection model (Isolation Forest)
    - Predictive maintenance models (Prophet/ARIMA for motor temp and vibration)

    Request body (JSON, optional):
    {
        "days": 30,                    // Days of training data (default: 30, min: 7)
        "contamination": 0.1,          // Expected anomaly rate (default: 0.1)
        "n_estimators": 100            // Number of trees in Isolation Forest (default: 100)
    }

    Returns:
        JSON response with training results

    Authentication:
        Requires valid JWT token with ADMIN or OPERATOR role
    """
    try:
        data = request.get_json() or {}

        # Parse parameters
        days = data.get("days", 30)
        contamination = data.get("contamination", 0.1)
        n_estimators = data.get("n_estimators", 100)

        # Validate parameters
        if not isinstance(days, int) or days < 7 or days > 90:
            raise ValidationError(
                message="Days must be an integer between 7 and 90",
                field="days"
            )

        if not isinstance(contamination, (int, float)) or contamination <= 0 or contamination > 0.5:
            raise ValidationError(
                message="Contamination must be between 0 and 0.5",
                field="contamination"
            )

        logger.info(
            f"Starting model training for well {well_id}",
            extra={
                "extra_fields": {
                    "well_id": well_id,
                    "days": days,
                    "initiated_by": getattr(request, "user_id", None),
                }
            }
        )

        # Train anomaly detection model
        anomaly_result = anomaly_service.train_model(
            well_id=well_id,
            days=days,
            contamination=contamination,
            n_estimators=n_estimators
        )

        # Train predictive maintenance models
        predictive_result = predictive_service.train_model(
            well_id=well_id,
            days=days
        )

        # Log audit trail
        log_audit(
            logger,
            action="TRAIN_ML_MODELS",
            resource_type="ml_models",
            resource_id=well_id,
            user_id=getattr(request, "user_id", None),
            details={
                "days": days,
                "anomaly_version": anomaly_result.get("version"),
                "predictive_models": list(predictive_result.get("models_trained", {}).keys()),
            }
        )

        return jsonify({
            "success": True,
            "well_id": well_id,
            "anomaly_detection": anomaly_result,
            "predictive_maintenance": predictive_result,
        }), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in model training", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred during model training"
        }), 500


@ml_bp.route("/anomalies/<well_id>", methods=["GET"])
@require_auth
def get_anomalies(well_id: str) -> Response:
    """
    Get detected anomalies for a well.

    Query parameters:
        hours: Number of hours to analyze (default: 24, max: 168)

    Args:
        well_id: Well identifier

    Returns:
        JSON response with anomaly detection results

    Authentication:
        Requires valid JWT token
    """
    try:
        hours = request.args.get("hours", default=24, type=int)

        # Validate hours parameter
        if hours < 1:
            hours = 1
        elif hours > 168:  # Max 7 days
            hours = 168

        # Detect anomalies
        anomalies = anomaly_service.detect_batch_anomalies(well_id, hours)

        # Count anomalies by severity
        severity_counts = {
            "critical": sum(1 for a in anomalies if a["severity"] == "critical"),
            "high": sum(1 for a in anomalies if a["severity"] == "high"),
            "medium": sum(1 for a in anomalies if a["severity"] == "medium"),
            "low": sum(1 for a in anomalies if a["severity"] == "low"),
        }

        total_anomalies = sum(1 for a in anomalies if a["is_anomaly"])

        # Get model info
        model_info = anomaly_service.get_model_info(well_id)

        return jsonify({
            "success": True,
            "well_id": well_id,
            "hours_analyzed": hours,
            "total_records": len(anomalies),
            "total_anomalies": total_anomalies,
            "anomaly_rate": total_anomalies / len(anomalies) if anomalies else 0,
            "severity_counts": severity_counts,
            "model_info": model_info,
            "anomalies": anomalies,
        }), 200

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in anomaly detection", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@ml_bp.route("/predictions/<well_id>", methods=["GET"])
@require_auth
def get_predictions(well_id: str) -> Response:
    """
    Get predictive maintenance forecast for a well.

    Query parameters:
        forecast_hours: Hours to forecast ahead (default: 24, max: 72)

    Args:
        well_id: Well identifier

    Returns:
        JSON response with maintenance predictions

    Authentication:
        Requires valid JWT token
    """
    try:
        forecast_hours = request.args.get("forecast_hours", default=24, type=int)

        # Validate forecast_hours parameter
        if forecast_hours < 1:
            forecast_hours = 1
        elif forecast_hours > 72:  # Max 3 days
            forecast_hours = 72

        # Get predictions
        predictions = predictive_service.predict_maintenance(well_id, forecast_hours)

        return jsonify({
            "success": True,
            **predictions
        }), 200

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except Exception as e:
        logger.error("Unexpected error in predictive maintenance", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@ml_bp.route("/optimize/<well_id>", methods=["GET"])
@require_auth
def get_optimization(well_id: str) -> Response:
    """
    Get performance optimization recommendations for a well.

    Query parameters:
        hours: Hours of data to analyze (default: 24, max: 168)
        include_peers: Include peer comparison (default: false)

    Args:
        well_id: Well identifier

    Returns:
        JSON response with optimization recommendations

    Authentication:
        Requires valid JWT token
    """
    try:
        hours = request.args.get("hours", default=24, type=int)
        include_peers = request.args.get("include_peers", default="false", type=str).lower() == "true"

        # Validate hours parameter
        if hours < 1:
            hours = 1
        elif hours > 168:  # Max 7 days
            hours = 168

        # Get performance analysis
        analysis = performance_service.analyze_well_performance(well_id, hours)

        # Optionally include peer comparison
        peer_comparison = None
        if include_peers:
            try:
                peer_comparison = performance_service.compare_to_peers(well_id, hours)
            except Exception as e:
                logger.warning(f"Peer comparison failed: {e}")

        result = {
            "success": True,
            **analysis
        }

        if peer_comparison:
            result["peer_comparison"] = peer_comparison

        return jsonify(result), 200

    except DatabaseError as e:
        logger.error(f"Database error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 500

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except Exception as e:
        logger.error("Unexpected error in performance optimization", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@ml_bp.route("/models", methods=["GET"])
@require_auth
@require_role([UserRole.ADMIN])
def list_models() -> Response:
    """
    List all trained ML models (admin only).

    Query parameters:
        well_id: Filter by well ID (optional)
        model_type: Filter by model type (optional)

    Returns:
        JSON response with list of models

    Authentication:
        Requires valid JWT token with ADMIN role
    """
    try:
        well_id = request.args.get("well_id", default=None, type=str)
        model_type = request.args.get("model_type", default=None, type=str)

        models = []

        # For simplicity, we'll list models from a few wells
        # In production, you'd want to query all wells from the database
        from pathlib import Path
        models_dir = Path("models")

        if not models_dir.exists():
            return jsonify({
                "success": True,
                "models": [],
                "message": "No models directory found"
            }), 200

        # List all model types
        for model_type_dir in models_dir.iterdir():
            if not model_type_dir.is_dir():
                continue

            if model_type and model_type_dir.name != model_type:
                continue

            # List all wells for this model type
            for well_dir in model_type_dir.iterdir():
                if not well_dir.is_dir():
                    continue

                if well_id and well_dir.name != well_id:
                    continue

                # Get latest model metadata
                metadata_file = well_dir / "latest_metadata.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        models.append({
                            "model_type": model_type_dir.name,
                            "well_id": well_dir.name,
                            "version": metadata.get("version", "unknown"),
                            "trained_at": metadata.get("training_date", metadata.get("saved_at", "unknown")),
                            "size_bytes": metadata.get("model_size_bytes", 0),
                            "metadata": metadata
                        })

        return jsonify({
            "success": True,
            "count": len(models),
            "models": models
        }), 200

    except Exception as e:
        logger.error("Unexpected error listing models", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@ml_bp.route("/models/<model_type>/<well_id>", methods=["DELETE"])
@require_auth
@require_role([UserRole.ADMIN])
def delete_model(model_type: str, well_id: str) -> Response:
    """
    Delete a trained ML model (admin only).

    Args:
        model_type: Type of model (anomaly, predictive_motor_temp, predictive_vibration, etc.)
        well_id: Well identifier

    Returns:
        JSON response with deletion status

    Authentication:
        Requires valid JWT token with ADMIN role
    """
    try:
        # Validate model_type
        valid_types = [
            "anomaly",
            "predictive_motor_temp",
            "predictive_vibration",
            "performance"
        ]

        if model_type not in valid_types:
            raise ValidationError(
                message=f"Invalid model type. Must be one of: {', '.join(valid_types)}",
                field="model_type"
            )

        # Delete the entire model directory for this well
        from pathlib import Path
        import shutil

        model_dir = Path("models") / model_type / well_id

        if not model_dir.exists():
            raise NotFoundError(
                message=f"Model not found: {model_type}/{well_id}",
                resource_type="ml_model",
                resource_id=f"{model_type}/{well_id}"
            )

        shutil.rmtree(model_dir)

        # Log audit trail
        log_audit(
            logger,
            action="DELETE_ML_MODEL",
            resource_type="ml_model",
            resource_id=f"{model_type}/{well_id}",
            user_id=getattr(request, "user_id", None)
        )

        logger.info(
            f"Model deleted: {model_type}/{well_id}",
            extra={
                "extra_fields": {
                    "model_type": model_type,
                    "well_id": well_id,
                    "deleted_by": getattr(request, "user_id", None),
                }
            }
        )

        return jsonify({
            "success": True,
            "message": f"Model {model_type}/{well_id} deleted successfully"
        }), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}", extra={"extra_fields": e.details})
        return jsonify(e.to_dict()), 400

    except NotFoundError as e:
        return jsonify(e.to_dict()), 404

    except Exception as e:
        logger.error("Unexpected error deleting model", exc_info=e)
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }), 500


@ml_bp.route("/health", methods=["GET"])
def ml_health() -> Response:
    """
    ML service health check endpoint.

    Returns:
        JSON response with service health status
    """
    try:
        from pathlib import Path
        import sys

        # Check if models directory exists
        models_dir = Path("models")
        models_exist = models_dir.exists()

        # Check if ML libraries are available
        libraries_status = {
            "sklearn": True,  # Already imported in services
            "pandas": True,   # Already imported
            "numpy": True,    # Already imported
        }

        # Check Prophet availability
        try:
            from prophet import Prophet
            libraries_status["prophet"] = True
        except ImportError:
            libraries_status["prophet"] = False

        # Check statsmodels availability
        try:
            from statsmodels.tsa.arima.model import ARIMA
            libraries_status["statsmodels"] = True
        except ImportError:
            libraries_status["statsmodels"] = False

        all_libraries_ok = all(libraries_status.values())

        return jsonify({
            "status": "healthy" if (models_exist and all_libraries_ok) else "degraded",
            "models_directory": str(models_dir),
            "models_directory_exists": models_exist,
            "ml_libraries": libraries_status,
            "python_version": sys.version,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error("Health check failed", exc_info=e)
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
