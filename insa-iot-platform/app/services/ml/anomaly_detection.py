"""
Anomaly detection service using Isolation Forest algorithm.

This module provides multivariate anomaly detection for ESP telemetry data
with feature engineering and automated retraining capabilities.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core import get_logger, ValidationError, DatabaseError
from app.db import get_db_pool, ESPTelemetry
from .model_storage import ModelStorage


logger = get_logger(__name__)


class AnomalyDetectionService:
    """Service for detecting anomalies in ESP telemetry data."""

    def __init__(self):
        """Initialize anomaly detection service."""
        self.model_storage = ModelStorage()
        self._db_pool = None
        self.feature_names = [
            # Raw features
            "flow_rate", "pip", "motor_current", "motor_temp", "vibration",
            "vsd_frequency", "flow_variance", "torque", "gor",
            # Rate of change features
            "flow_rate_change", "motor_temp_change", "vibration_change",
            # Rolling statistics
            "flow_rate_std", "motor_temp_std", "vibration_std",
            # Cross-correlations
            "temp_current_ratio", "flow_vibration_ratio"
        ]
        logger.info("Anomaly detection service initialized")

    @property
    def db_pool(self):
        """Lazy-load database connection pool."""
        if self._db_pool is None:
            self._db_pool = get_db_pool()
        return self._db_pool

    def _fetch_training_data(
        self,
        well_id: str,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical telemetry data for training.

        Args:
            well_id: Well identifier
            days: Number of days of historical data

        Returns:
            DataFrame with telemetry data

        Raises:
            ValidationError: If insufficient data available
            DatabaseError: If query fails
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days)

            query = """
                SELECT
                    timestamp,
                    flow_rate,
                    pip,
                    motor_current,
                    motor_temp,
                    vibration,
                    vsd_frequency,
                    flow_variance,
                    torque,
                    gor
                FROM esp_telemetry
                WHERE well_id = %s
                AND timestamp >= %s
                ORDER BY timestamp ASC
            """

            result = self.db_pool.execute_query(
                query,
                params=(well_id, start_time),
                fetch=True,
                return_dict=True
            )

            if not result or len(result) < 100:
                raise ValidationError(
                    message=f"Insufficient data for training. Need at least 100 records, got {len(result) if result else 0}",
                    field="training_data",
                    details={"well_id": well_id, "days": days}
                )

            df = pd.DataFrame(result)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            logger.info(
                f"Fetched {len(df)} training records",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "days": days,
                        "records": len(df),
                    }
                }
            )

            return df

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch training data",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Failed to fetch training data",
                operation="SELECT",
                details={"well_id": well_id}
            ) from e

    def _engineer_features(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Engineer features for anomaly detection.

        Args:
            df: DataFrame with raw telemetry data

        Returns:
            DataFrame with engineered features
        """
        try:
            # Make a copy to avoid modifying original
            features_df = df.copy()

            # Rate of change features (1st derivative)
            features_df["flow_rate_change"] = features_df["flow_rate"].diff().fillna(0)
            features_df["motor_temp_change"] = features_df["motor_temp"].diff().fillna(0)
            features_df["vibration_change"] = features_df["vibration"].diff().fillna(0)

            # Rolling statistics (5-point window)
            window = 5
            features_df["flow_rate_std"] = (
                features_df["flow_rate"]
                .rolling(window=window, min_periods=1)
                .std()
                .fillna(0)
            )
            features_df["motor_temp_std"] = (
                features_df["motor_temp"]
                .rolling(window=window, min_periods=1)
                .std()
                .fillna(0)
            )
            features_df["vibration_std"] = (
                features_df["vibration"]
                .rolling(window=window, min_periods=1)
                .std()
                .fillna(0)
            )

            # Cross-correlations
            features_df["temp_current_ratio"] = (
                features_df["motor_temp"] / (features_df["motor_current"] + 1e-6)
            )
            features_df["flow_vibration_ratio"] = (
                features_df["flow_rate"] / (features_df["vibration"] + 1e-6)
            )

            # Replace infinities with 0
            features_df = features_df.replace([np.inf, -np.inf], 0)

            # Fill any remaining NaN values
            features_df = features_df.fillna(0)

            logger.debug(
                f"Engineered {len(self.feature_names)} features",
                extra={
                    "extra_fields": {
                        "features": self.feature_names,
                        "rows": len(features_df),
                    }
                }
            )

            return features_df

        except Exception as e:
            logger.error("Feature engineering failed", exc_info=e)
            raise ValidationError(
                message="Feature engineering failed",
                details={"error": str(e)}
            ) from e

    def train_model(
        self,
        well_id: str,
        days: int = 30,
        contamination: float = 0.1,
        n_estimators: int = 100
    ) -> Dict[str, Any]:
        """
        Train anomaly detection model for a well.

        Args:
            well_id: Well identifier
            days: Number of days of historical data for training
            contamination: Expected proportion of anomalies (0.0-0.5)
            n_estimators: Number of base estimators in the ensemble

        Returns:
            Dictionary with training results and metrics

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

            if not 0.0 < contamination <= 0.5:
                raise ValidationError(
                    message="Contamination must be between 0.0 and 0.5",
                    field="contamination"
                )

            # Fetch training data
            logger.info(
                f"Starting model training for well {well_id}",
                extra={"extra_fields": {"well_id": well_id, "days": days}}
            )

            df = self._fetch_training_data(well_id, days)

            # Engineer features
            features_df = self._engineer_features(df)

            # Extract feature matrix
            X = features_df[self.feature_names].values

            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train Isolation Forest
            model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                max_samples="auto",
                random_state=42,
                n_jobs=-1,
                verbose=0
            )

            model.fit(X_scaled)

            # Calculate training metrics
            predictions = model.predict(X_scaled)
            scores = model.score_samples(X_scaled)

            # Count anomalies in training data
            anomalies = (predictions == -1).sum()
            anomaly_rate = anomalies / len(predictions)

            # Calculate score statistics
            score_mean = float(np.mean(scores))
            score_std = float(np.std(scores))
            score_min = float(np.min(scores))
            score_max = float(np.max(scores))

            # Prepare metadata
            training_duration = (datetime.utcnow() - start_time).total_seconds()
            metadata = {
                "training_date": start_time.isoformat(),
                "training_duration_seconds": training_duration,
                "training_records": len(df),
                "training_days": days,
                "contamination": contamination,
                "n_estimators": n_estimators,
                "features": self.feature_names,
                "n_features": len(self.feature_names),
                "anomalies_in_training": int(anomalies),
                "anomaly_rate": anomaly_rate,
                "score_statistics": {
                    "mean": score_mean,
                    "std": score_std,
                    "min": score_min,
                    "max": score_max,
                },
                "model_params": model.get_params(),
            }

            # Save model and scaler together
            model_bundle = {
                "model": model,
                "scaler": scaler,
                "feature_names": self.feature_names,
            }

            version = self.model_storage.save_model(
                model=model_bundle,
                model_type="anomaly",
                well_id=well_id,
                metadata=metadata
            )

            logger.info(
                f"Model trained successfully for well {well_id}",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "version": version,
                        "training_duration": training_duration,
                        "records": len(df),
                        "anomaly_rate": anomaly_rate,
                    }
                }
            )

            return {
                "success": True,
                "well_id": well_id,
                "version": version,
                "training_records": len(df),
                "training_duration_seconds": training_duration,
                "anomaly_rate": anomaly_rate,
                "score_statistics": metadata["score_statistics"],
            }

        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(
                "Model training failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Model training failed",
                operation="TRAIN_MODEL",
                details={"well_id": well_id}
            ) from e

    def detect_anomaly(
        self,
        telemetry: ESPTelemetry,
        well_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect anomaly in a single telemetry reading.

        Args:
            telemetry: ESP telemetry data
            well_id: Optional well ID override

        Returns:
            Dictionary with anomaly detection results

        Raises:
            DatabaseError: If model not found or prediction fails
        """
        try:
            well_id = well_id or telemetry.well_id

            # Load model
            if not self.model_storage.model_exists("anomaly", well_id):
                raise DatabaseError(
                    message=f"No trained model found for well: {well_id}",
                    operation="LOAD_MODEL",
                    details={"well_id": well_id}
                )

            model_bundle, metadata = self.model_storage.load_model(
                "anomaly", well_id
            )

            model = model_bundle["model"]
            scaler = model_bundle["scaler"]

            # Prepare single-row DataFrame for feature engineering
            # We need at least a few rows for rolling stats, so we fetch recent history
            recent_data = self._fetch_recent_telemetry(well_id, hours=1)
            recent_data.append(telemetry.to_dict())

            df = pd.DataFrame(recent_data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            # Engineer features
            features_df = self._engineer_features(df)

            # Extract features for the latest (target) row
            X = features_df[self.feature_names].iloc[-1:].values
            X_scaled = scaler.transform(X)

            # Predict
            prediction = model.predict(X_scaled)[0]
            score = model.score_samples(X_scaled)[0]

            # Convert score to 0-1 range (higher = more anomalous)
            # Isolation Forest scores are typically in range [-0.5, 0.5]
            # We normalize to [0, 1] where 1 is most anomalous
            anomaly_score = 1.0 - (score + 0.5)  # Simple normalization
            anomaly_score = max(0.0, min(1.0, anomaly_score))  # Clamp to [0, 1]

            is_anomaly = prediction == -1
            confidence = float(anomaly_score)

            # Determine severity based on score
            if anomaly_score >= 0.9:
                severity = "critical"
            elif anomaly_score >= 0.8:
                severity = "high"
            elif anomaly_score >= 0.7:
                severity = "medium"
            else:
                severity = "low"

            result = {
                "well_id": well_id,
                "timestamp": telemetry.timestamp.isoformat(),
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": confidence,
                "severity": severity,
                "raw_score": float(score),
                "model_version": metadata.get("version", "unknown"),
                "features_analyzed": self.feature_names,
            }

            if is_anomaly:
                logger.warning(
                    f"Anomaly detected for well {well_id}",
                    extra={
                        "extra_fields": {
                            "well_id": well_id,
                            "anomaly_score": confidence,
                            "severity": severity,
                        }
                    }
                )

            return result

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                "Anomaly detection failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Anomaly detection failed",
                operation="PREDICT",
                details={"well_id": well_id}
            ) from e

    def detect_batch_anomalies(
        self,
        well_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in a batch of recent telemetry data.

        Args:
            well_id: Well identifier
            hours: Number of hours of history to analyze

        Returns:
            List of anomaly detection results

        Raises:
            DatabaseError: If detection fails
        """
        try:
            # Load model
            if not self.model_storage.model_exists("anomaly", well_id):
                raise DatabaseError(
                    message=f"No trained model found for well: {well_id}",
                    operation="LOAD_MODEL",
                    details={"well_id": well_id}
                )

            model_bundle, metadata = self.model_storage.load_model(
                "anomaly", well_id
            )

            model = model_bundle["model"]
            scaler = model_bundle["scaler"]

            # Fetch recent telemetry
            df_dict = self._fetch_recent_telemetry(well_id, hours)
            if not df_dict:
                return []

            df = pd.DataFrame(df_dict)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            # Engineer features
            features_df = self._engineer_features(df)

            # Extract features
            X = features_df[self.feature_names].values
            X_scaled = scaler.transform(X)

            # Predict
            predictions = model.predict(X_scaled)
            scores = model.score_samples(X_scaled)

            # Convert scores to anomaly scores
            anomaly_scores = 1.0 - (scores + 0.5)
            anomaly_scores = np.clip(anomaly_scores, 0.0, 1.0)

            # Build results
            results = []
            for idx, (pred, score, anomaly_score) in enumerate(
                zip(predictions, scores, anomaly_scores)
            ):
                is_anomaly = pred == -1

                if anomaly_score >= 0.9:
                    severity = "critical"
                elif anomaly_score >= 0.8:
                    severity = "high"
                elif anomaly_score >= 0.7:
                    severity = "medium"
                else:
                    severity = "low"

                result = {
                    "timestamp": df.iloc[idx]["timestamp"].isoformat(),
                    "is_anomaly": bool(is_anomaly),
                    "anomaly_score": float(anomaly_score),
                    "severity": severity,
                    "raw_score": float(score),
                }
                results.append(result)

            anomaly_count = sum(1 for r in results if r["is_anomaly"])

            logger.info(
                f"Batch anomaly detection complete",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "hours": hours,
                        "total_records": len(results),
                        "anomalies_detected": anomaly_count,
                    }
                }
            )

            return results

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                "Batch anomaly detection failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Batch anomaly detection failed",
                operation="BATCH_PREDICT",
                details={"well_id": well_id}
            ) from e

    def _fetch_recent_telemetry(
        self,
        well_id: str,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent telemetry data.

        Args:
            well_id: Well identifier
            hours: Number of hours of history

        Returns:
            List of telemetry dictionaries
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            query = """
                SELECT
                    timestamp,
                    flow_rate,
                    pip,
                    motor_current,
                    motor_temp,
                    vibration,
                    vsd_frequency,
                    flow_variance,
                    torque,
                    gor
                FROM esp_telemetry
                WHERE well_id = %s
                AND timestamp >= %s
                ORDER BY timestamp ASC
                LIMIT 100
            """

            result = self.db_pool.execute_query(
                query,
                params=(well_id, start_time),
                fetch=True,
                return_dict=True
            )

            return result or []

        except Exception as e:
            logger.warning(
                "Failed to fetch recent telemetry",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            return []

    def get_model_info(self, well_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about the trained model.

        Args:
            well_id: Well identifier

        Returns:
            Model metadata or None if not found
        """
        return self.model_storage.get_model_info("anomaly", well_id)
