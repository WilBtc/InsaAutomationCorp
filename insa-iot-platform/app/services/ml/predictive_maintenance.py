"""
Predictive maintenance service using time-series forecasting.

This module provides predictive maintenance capabilities including
motor temperature and vibration forecasting, RUL estimation, and
maintenance window recommendations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import warnings
import numpy as np
import pandas as pd

# Suppress Prophet logging
import logging
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from app.core import get_logger, ValidationError, DatabaseError
from app.db import get_db_pool
from .model_storage import ModelStorage


logger = get_logger(__name__)
warnings.filterwarnings('ignore', category=ConvergenceWarning)


class PredictiveMaintenanceService:
    """Service for predicting equipment failures and maintenance needs."""

    def __init__(self):
        """Initialize predictive maintenance service."""
        self.model_storage = ModelStorage()
        self._db_pool = None

        # Thresholds for risk assessment
        self.motor_temp_thresholds = {
            "critical": 95.0,
            "high": 90.0,
            "medium": 85.0,
            "low": 80.0,
        }
        self.vibration_thresholds = {
            "critical": 4.5,
            "high": 4.0,
            "medium": 3.5,
            "low": 3.0,
        }

        logger.info(
            f"Predictive maintenance service initialized (Prophet: {PROPHET_AVAILABLE})"
        )

    @property
    def db_pool(self):
        """Lazy-load database connection pool."""
        if self._db_pool is None:
            self._db_pool = get_db_pool()
        return self._db_pool

    def _fetch_time_series_data(
        self,
        well_id: str,
        metric: str,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch time-series data for a specific metric.

        Args:
            well_id: Well identifier
            metric: Metric name (motor_temp, vibration, etc.)
            days: Number of days of historical data

        Returns:
            DataFrame with timestamp and value columns

        Raises:
            ValidationError: If insufficient data
            DatabaseError: If query fails
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days)

            query = f"""
                SELECT
                    timestamp,
                    {metric} as value
                FROM esp_telemetry
                WHERE well_id = %s
                AND timestamp >= %s
                AND {metric} IS NOT NULL
                ORDER BY timestamp ASC
            """

            result = self.db_pool.execute_query(
                query,
                params=(well_id, start_time),
                fetch=True,
                return_dict=True
            )

            if not result or len(result) < 50:
                raise ValidationError(
                    message=f"Insufficient data for {metric}. Need at least 50 records, got {len(result) if result else 0}",
                    field="training_data",
                    details={"well_id": well_id, "metric": metric}
                )

            df = pd.DataFrame(result)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            logger.info(
                f"Fetched {len(df)} records for {metric}",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "metric": metric,
                        "records": len(df),
                    }
                }
            )

            return df

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch time-series data",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id, "metric": metric}}
            )
            raise DatabaseError(
                message="Failed to fetch time-series data",
                operation="SELECT",
                details={"well_id": well_id, "metric": metric}
            ) from e

    def _train_prophet_model(
        self,
        df: pd.DataFrame,
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Train Prophet model for time-series forecasting.

        Args:
            df: DataFrame with timestamp and value columns
            metric_name: Name of the metric being forecasted

        Returns:
            Dictionary with trained model and metadata
        """
        if not PROPHET_AVAILABLE:
            raise ValidationError(
                message="Prophet library not available. Install with: pip install prophet",
                details={"metric": metric_name}
            )

        try:
            # Prepare data in Prophet format
            prophet_df = df.copy()
            prophet_df.columns = ["ds", "y"]

            # Initialize and train Prophet
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0,
                interval_width=0.95,
            )

            model.fit(prophet_df)

            # Calculate training metrics
            predictions = model.predict(prophet_df)
            actual = prophet_df["y"].values
            predicted = predictions["yhat"].values

            mae = float(np.mean(np.abs(actual - predicted)))
            rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
            mape = float(np.mean(np.abs((actual - predicted) / (actual + 1e-6))) * 100)

            return {
                "model": model,
                "model_type": "prophet",
                "metrics": {
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                }
            }

        except Exception as e:
            logger.warning(
                f"Prophet training failed for {metric_name}, falling back to ARIMA",
                exc_info=e
            )
            # Fallback to ARIMA if Prophet fails
            return self._train_arima_model(df, metric_name)

    def _train_arima_model(
        self,
        df: pd.DataFrame,
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Train ARIMA model as fallback for time-series forecasting.

        Args:
            df: DataFrame with timestamp and value columns
            metric_name: Name of the metric being forecasted

        Returns:
            Dictionary with trained model and metadata
        """
        try:
            values = df["value"].values

            # Fit ARIMA model
            model = ARIMA(values, order=(2, 1, 2))
            fitted_model = model.fit()

            # Calculate training metrics
            predictions = fitted_model.fittedvalues
            actual = values[1:]  # ARIMA loses first value due to differencing

            if len(predictions) > len(actual):
                predictions = predictions[:len(actual)]

            mae = float(np.mean(np.abs(actual - predictions)))
            rmse = float(np.sqrt(np.mean((actual - predictions) ** 2)))
            mape = float(np.mean(np.abs((actual - predictions) / (actual + 1e-6))) * 100)

            return {
                "model": fitted_model,
                "model_type": "arima",
                "metrics": {
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                }
            }

        except Exception as e:
            logger.error(
                f"ARIMA training failed for {metric_name}",
                exc_info=e
            )
            raise ValidationError(
                message=f"Failed to train forecasting model for {metric_name}",
                details={"error": str(e)}
            ) from e

    def train_model(
        self,
        well_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Train predictive maintenance models for motor temp and vibration.

        Args:
            well_id: Well identifier
            days: Number of days of historical data

        Returns:
            Dictionary with training results

        Raises:
            ValidationError: If parameters invalid or insufficient data
            DatabaseError: If training fails
        """
        start_time = datetime.utcnow()

        try:
            # Validate parameters
            if days < 7:
                raise ValidationError(
                    message="Training requires at least 7 days of data",
                    field="days"
                )

            logger.info(
                f"Starting predictive maintenance training for well {well_id}",
                extra={"extra_fields": {"well_id": well_id, "days": days}}
            )

            # Train models for motor temperature and vibration
            metrics = ["motor_temp", "vibration"]
            models_trained = {}

            for metric in metrics:
                # Fetch data
                df = self._fetch_time_series_data(well_id, metric, days)

                # Train model
                model_result = self._train_prophet_model(df, metric)

                models_trained[metric] = model_result

                # Save model
                metadata = {
                    "training_date": start_time.isoformat(),
                    "metric": metric,
                    "training_records": len(df),
                    "training_days": days,
                    "model_type": model_result["model_type"],
                    "metrics": model_result["metrics"],
                }

                version = self.model_storage.save_model(
                    model=model_result["model"],
                    model_type=f"predictive_{metric}",
                    well_id=well_id,
                    metadata=metadata
                )

                logger.info(
                    f"Predictive model trained for {metric}",
                    extra={
                        "extra_fields": {
                            "well_id": well_id,
                            "metric": metric,
                            "version": version,
                            "model_type": model_result["model_type"],
                            "mae": model_result["metrics"]["mae"],
                        }
                    }
                )

            training_duration = (datetime.utcnow() - start_time).total_seconds()

            return {
                "success": True,
                "well_id": well_id,
                "training_duration_seconds": training_duration,
                "models_trained": {
                    metric: {
                        "model_type": result["model_type"],
                        "metrics": result["metrics"],
                    }
                    for metric, result in models_trained.items()
                },
            }

        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(
                "Predictive maintenance training failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Predictive maintenance training failed",
                operation="TRAIN_MODEL",
                details={"well_id": well_id}
            ) from e

    def predict_maintenance(
        self,
        well_id: str,
        forecast_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Predict maintenance needs for the next N hours.

        Args:
            well_id: Well identifier
            forecast_hours: Number of hours to forecast ahead

        Returns:
            Dictionary with predictions and maintenance recommendations

        Raises:
            DatabaseError: If models not found or prediction fails
        """
        try:
            # Check if models exist
            motor_temp_exists = self.model_storage.model_exists(
                "predictive_motor_temp", well_id
            )
            vibration_exists = self.model_storage.model_exists(
                "predictive_vibration", well_id
            )

            if not (motor_temp_exists and vibration_exists):
                raise DatabaseError(
                    message=f"No trained predictive models found for well: {well_id}",
                    operation="LOAD_MODEL",
                    details={"well_id": well_id}
                )

            # Load models
            motor_temp_model, motor_temp_metadata = self.model_storage.load_model(
                "predictive_motor_temp", well_id
            )
            vibration_model, vibration_metadata = self.model_storage.load_model(
                "predictive_vibration", well_id
            )

            # Predict motor temperature
            motor_temp_prediction = self._predict_metric(
                model=motor_temp_model,
                model_type=motor_temp_metadata.get("model_type", "prophet"),
                metric="motor_temp",
                well_id=well_id,
                forecast_hours=forecast_hours
            )

            # Predict vibration
            vibration_prediction = self._predict_metric(
                model=vibration_model,
                model_type=vibration_metadata.get("model_type", "prophet"),
                metric="vibration",
                well_id=well_id,
                forecast_hours=forecast_hours
            )

            # Assess risks
            motor_temp_risk = self._assess_risk(
                motor_temp_prediction["forecast"],
                self.motor_temp_thresholds
            )
            vibration_risk = self._assess_risk(
                vibration_prediction["forecast"],
                self.vibration_thresholds
            )

            # Generate maintenance recommendation
            recommendation = self._generate_maintenance_recommendation(
                motor_temp_risk=motor_temp_risk,
                vibration_risk=vibration_risk,
                motor_temp_forecast=motor_temp_prediction["forecast"],
                vibration_forecast=vibration_prediction["forecast"]
            )

            result = {
                "well_id": well_id,
                "forecast_hours": forecast_hours,
                "predictions": {
                    "motor_temp": {
                        "current": motor_temp_prediction["current"],
                        "forecast": motor_temp_prediction["forecast"],
                        "confidence_lower": motor_temp_prediction["confidence_lower"],
                        "confidence_upper": motor_temp_prediction["confidence_upper"],
                        "risk_level": motor_temp_risk["level"],
                        "threshold_exceeded": motor_temp_risk["threshold_exceeded"],
                    },
                    "vibration": {
                        "current": vibration_prediction["current"],
                        "forecast": vibration_prediction["forecast"],
                        "confidence_lower": vibration_prediction["confidence_lower"],
                        "confidence_upper": vibration_prediction["confidence_upper"],
                        "risk_level": vibration_risk["level"],
                        "threshold_exceeded": vibration_risk["threshold_exceeded"],
                    },
                },
                "maintenance_recommendation": recommendation,
            }

            logger.info(
                f"Predictive maintenance forecast complete",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "forecast_hours": forecast_hours,
                        "urgency": recommendation["urgency"],
                    }
                }
            )

            return result

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                "Predictive maintenance forecast failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Predictive maintenance forecast failed",
                operation="PREDICT",
                details={"well_id": well_id}
            ) from e

    def _predict_metric(
        self,
        model: Any,
        model_type: str,
        metric: str,
        well_id: str,
        forecast_hours: int
    ) -> Dict[str, Any]:
        """
        Predict a specific metric using the trained model.

        Args:
            model: Trained model
            model_type: Type of model (prophet or arima)
            metric: Metric name
            well_id: Well identifier
            forecast_hours: Hours to forecast

        Returns:
            Dictionary with prediction results
        """
        try:
            # Get current value
            current_query = f"""
                SELECT {metric} as value
                FROM esp_telemetry
                WHERE well_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            current_result = self.db_pool.execute_query(
                current_query,
                params=(well_id,),
                fetch=True,
                return_dict=True
            )
            current_value = current_result[0]["value"] if current_result else None

            # Forecast based on model type
            if model_type == "prophet":
                # Create future dataframe
                future = model.make_future_dataframe(
                    periods=forecast_hours,
                    freq='H',
                    include_history=False
                )
                forecast = model.predict(future)

                predicted_value = float(forecast["yhat"].iloc[-1])
                confidence_lower = float(forecast["yhat_lower"].iloc[-1])
                confidence_upper = float(forecast["yhat_upper"].iloc[-1])

            else:  # ARIMA
                forecast = model.forecast(steps=forecast_hours)
                predicted_value = float(forecast.iloc[-1])

                # Estimate confidence interval (ARIMA provides standard errors)
                std_error = float(np.std(model.resid))
                confidence_lower = predicted_value - 1.96 * std_error
                confidence_upper = predicted_value + 1.96 * std_error

            return {
                "current": current_value,
                "forecast": predicted_value,
                "confidence_lower": confidence_lower,
                "confidence_upper": confidence_upper,
            }

        except Exception as e:
            logger.error(
                f"Metric prediction failed for {metric}",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id, "metric": metric}}
            )
            raise

    def _assess_risk(
        self,
        predicted_value: float,
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Assess risk level based on predicted value and thresholds.

        Args:
            predicted_value: Predicted metric value
            thresholds: Dictionary of risk thresholds

        Returns:
            Dictionary with risk assessment
        """
        if predicted_value >= thresholds["critical"]:
            return {
                "level": "critical",
                "threshold_exceeded": "critical",
                "percentage_of_threshold": (predicted_value / thresholds["critical"]) * 100,
            }
        elif predicted_value >= thresholds["high"]:
            return {
                "level": "high",
                "threshold_exceeded": "high",
                "percentage_of_threshold": (predicted_value / thresholds["high"]) * 100,
            }
        elif predicted_value >= thresholds["medium"]:
            return {
                "level": "medium",
                "threshold_exceeded": "medium",
                "percentage_of_threshold": (predicted_value / thresholds["medium"]) * 100,
            }
        elif predicted_value >= thresholds["low"]:
            return {
                "level": "low",
                "threshold_exceeded": "low",
                "percentage_of_threshold": (predicted_value / thresholds["low"]) * 100,
            }
        else:
            return {
                "level": "normal",
                "threshold_exceeded": None,
                "percentage_of_threshold": 0.0,
            }

    def _generate_maintenance_recommendation(
        self,
        motor_temp_risk: Dict[str, Any],
        vibration_risk: Dict[str, Any],
        motor_temp_forecast: float,
        vibration_forecast: float
    ) -> Dict[str, Any]:
        """
        Generate maintenance recommendation based on risk assessments.

        Args:
            motor_temp_risk: Motor temperature risk assessment
            vibration_risk: Vibration risk assessment
            motor_temp_forecast: Forecasted motor temperature
            vibration_forecast: Forecasted vibration

        Returns:
            Maintenance recommendation dictionary
        """
        # Determine highest risk level
        risk_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1, "normal": 0}
        motor_temp_risk_score = risk_levels.get(motor_temp_risk["level"], 0)
        vibration_risk_score = risk_levels.get(vibration_risk["level"], 0)

        max_risk_score = max(motor_temp_risk_score, vibration_risk_score)

        # Generate recommendation based on risk
        if max_risk_score >= 4:
            action = "immediate_shutdown"
            urgency = "critical"
            estimated_days = 0
            confidence = 0.90
            details = (
                "CRITICAL: Immediate shutdown recommended. "
                f"Motor temperature forecast: {motor_temp_forecast:.1f}°C, "
                f"Vibration forecast: {vibration_forecast:.1f} mm/s. "
                "Equipment is at high risk of failure."
            )
        elif max_risk_score >= 3:
            action = "schedule_immediate_inspection"
            urgency = "high"
            estimated_days = 2
            confidence = 0.85
            details = (
                "HIGH RISK: Schedule immediate inspection. "
                f"Motor temperature forecast: {motor_temp_forecast:.1f}°C, "
                f"Vibration forecast: {vibration_forecast:.1f} mm/s. "
                "Potential failure within 2 days."
            )
        elif max_risk_score >= 2:
            action = "schedule_inspection"
            urgency = "medium"
            estimated_days = 7
            confidence = 0.75
            details = (
                "MEDIUM RISK: Schedule inspection within 7 days. "
                f"Motor temperature forecast: {motor_temp_forecast:.1f}°C, "
                f"Vibration forecast: {vibration_forecast:.1f} mm/s. "
                "Preventive maintenance recommended."
            )
        elif max_risk_score >= 1:
            action = "monitor_closely"
            urgency = "low"
            estimated_days = 14
            confidence = 0.65
            details = (
                "LOW RISK: Monitor equipment closely. "
                f"Motor temperature forecast: {motor_temp_forecast:.1f}°C, "
                f"Vibration forecast: {vibration_forecast:.1f} mm/s. "
                "Schedule routine maintenance within 14 days."
            )
        else:
            action = "continue_monitoring"
            urgency = "none"
            estimated_days = 30
            confidence = 0.60
            details = (
                "NORMAL: Equipment operating within normal parameters. "
                f"Motor temperature forecast: {motor_temp_forecast:.1f}°C, "
                f"Vibration forecast: {vibration_forecast:.1f} mm/s. "
                "Continue routine monitoring."
            )

        return {
            "action": action,
            "urgency": urgency,
            "estimated_days_until_failure": estimated_days,
            "confidence": confidence,
            "details": details,
            "risk_factors": {
                "motor_temp_risk": motor_temp_risk["level"],
                "vibration_risk": vibration_risk["level"],
            },
        }

    def get_model_info(self, well_id: str, metric: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a trained predictive model.

        Args:
            well_id: Well identifier
            metric: Metric name (motor_temp or vibration)

        Returns:
            Model metadata or None if not found
        """
        return self.model_storage.get_model_info(f"predictive_{metric}", well_id)
