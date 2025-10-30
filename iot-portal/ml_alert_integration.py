#!/usr/bin/env python3
"""
ML-Alerting Integration Module
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8 Week 2

Automatically creates alerts from ML anomaly detections.

Integration Flow:
1. ML detects anomaly with prediction
2. Determine severity based on confidence
3. Create alert via alerting system
4. Auto-escalate high-confidence anomalies

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any, Optional

from alert_state_machine import AlertStateMachine
from escalation_engine import EscalationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLAlertIntegration:
    """
    Integrates ML anomaly detection with alerting system.

    Automatically creates alerts when anomalies are detected with
    appropriate severity levels based on confidence scores.
    """

    # Confidence thresholds for severity mapping
    SEVERITY_THRESHOLDS = {
        'critical': 0.90,  # 90%+ confidence
        'high': 0.75,      # 75-89% confidence
        'medium': 0.60,    # 60-74% confidence
        'low': 0.45,       # 45-59% confidence
        'info': 0.0        # <45% confidence
    }

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize ML-Alert integration.

        Args:
            db_config: Database configuration dictionary
        """
        self.db_config = db_config
        logger.info("ML-Alert integration initialized")

    def map_confidence_to_severity(self, confidence: float) -> str:
        """
        Map ML confidence score to alert severity.

        Args:
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Severity level (critical/high/medium/low/info)

        Example:
            >>> integration.map_confidence_to_severity(0.95)
            'critical'
            >>> integration.map_confidence_to_severity(0.72)
            'medium'
        """
        if confidence >= self.SEVERITY_THRESHOLDS['critical']:
            return 'critical'
        elif confidence >= self.SEVERITY_THRESHOLDS['high']:
            return 'high'
        elif confidence >= self.SEVERITY_THRESHOLDS['medium']:
            return 'medium'
        elif confidence >= self.SEVERITY_THRESHOLDS['low']:
            return 'low'
        else:
            return 'info'

    def create_alert_from_anomaly(
        self,
        device_id: str,
        metric_name: str,
        value: float,
        anomaly_score: float,
        confidence: float,
        model_id: str
    ) -> Optional[str]:
        """
        Create alert from ML anomaly detection.

        Args:
            device_id: Device UUID
            metric_name: Metric name (e.g., 'temperature')
            value: Anomalous value detected
            anomaly_score: Anomaly score from ML model
            confidence: Prediction confidence (0.0 to 1.0)
            model_id: ML model UUID

        Returns:
            Alert UUID if created, None otherwise

        Example:
            alert_id = integration.create_alert_from_anomaly(
                device_id='device-123',
                metric_name='temperature',
                value=95.0,
                anomaly_score=-0.85,
                confidence=0.92,
                model_id='model-456'
            )
        """
        try:
            # Map confidence to severity
            severity = self.map_confidence_to_severity(confidence)

            # Build alert message
            message = (
                f"ML Anomaly Detected: {metric_name} = {value:.2f} "
                f"(score: {anomaly_score:.3f}, confidence: {confidence*100:.1f}%)"
            )

            # Get or create "ML Anomaly Detection" rule
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if ML anomaly rule exists
                    cursor.execute("""
                        SELECT id FROM rules
                        WHERE name = 'ML Anomaly Detection'
                        AND device_id = %s
                    """, (device_id,))

                    rule_row = cursor.fetchone()

                    if rule_row:
                        rule_id = rule_row['id']
                    else:
                        # Create ML anomaly rule
                        rule_id = str(uuid.uuid4())
                        cursor.execute("""
                            INSERT INTO rules (
                                id, device_id, name, rule_type,
                                enabled, conditions, actions
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            rule_id,
                            device_id,
                            'ML Anomaly Detection',
                            'ml_anomaly',
                            True,
                            psycopg2.extras.Json({
                                'metric': metric_name,
                                'model_id': model_id,
                                'min_confidence': 0.7
                            }),
                            psycopg2.extras.Json([
                                {'type': 'alert', 'severity': 'auto'}
                            ])
                        ))

                    # Create alert
                    alert_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO alerts (
                            id, device_id, rule_id, severity, message,
                            value, threshold, status, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
                        RETURNING id
                    """, (
                        alert_id,
                        device_id,
                        rule_id,
                        severity,
                        message,
                        value,
                        None,  # No fixed threshold for ML anomalies
                        psycopg2.extras.Json({
                            'source': 'ml_anomaly_detection',
                            'model_id': model_id,
                            'anomaly_score': anomaly_score,
                            'confidence': confidence,
                            'metric_name': metric_name
                        })
                    ))

                conn.commit()

                logger.info(
                    f"Alert created from ML anomaly: {alert_id} "
                    f"(device={device_id}, metric={metric_name}, "
                    f"severity={severity}, confidence={confidence*100:.1f}%)"
                )

                # Auto-escalate critical and high severity alerts
                if severity in ['critical', 'high']:
                    self._auto_escalate_alert(alert_id, severity)

                return alert_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error creating alert from anomaly: {e}")
            return None

    def _auto_escalate_alert(self, alert_id: str, severity: str):
        """
        Auto-escalate high-priority ML-generated alerts.

        Args:
            alert_id: Alert UUID
            severity: Alert severity
        """
        try:
            with EscalationEngine(self.db_config) as engine:
                # Get matching escalation policy
                policy = engine.get_policy_for_alert(alert_id)

                if policy:
                    # Check if escalation needed
                    should_escalate = engine.should_escalate(alert_id)

                    if should_escalate:
                        result = engine.escalate_alert(alert_id)
                        logger.info(
                            f"Auto-escalated alert {alert_id} to tier "
                            f"{result.get('tier', 'unknown')}"
                        )
                else:
                    logger.warning(
                        f"No escalation policy found for ML alert {alert_id} "
                        f"(severity={severity})"
                    )

        except Exception as e:
            logger.error(f"Error auto-escalating alert {alert_id}: {e}")

    def process_anomaly_detection(
        self,
        device_id: str,
        metric_name: str,
        value: float,
        prediction_result: Dict[str, Any],
        model_id: str,
        min_confidence_for_alert: float = 0.70
    ) -> Optional[str]:
        """
        Process ML anomaly detection and optionally create alert.

        This is the main entry point for ML-to-Alerting integration.
        Call this after ML prediction is complete.

        Args:
            device_id: Device UUID
            metric_name: Metric name
            value: Measured value
            prediction_result: ML prediction result dict with keys:
                              is_anomaly, score, confidence
            model_id: ML model UUID
            min_confidence_for_alert: Minimum confidence to create alert (default: 0.70)

        Returns:
            Alert UUID if created, None otherwise

        Example:
            prediction = detector.predict(value)
            alert_id = integration.process_anomaly_detection(
                device_id='device-123',
                metric_name='temperature',
                value=95.0,
                prediction_result=prediction,
                model_id='model-456',
                min_confidence_for_alert=0.70
            )
        """
        try:
            is_anomaly = prediction_result.get('is_anomaly', False)
            confidence = prediction_result.get('confidence', 0.0)
            anomaly_score = prediction_result.get('score', 0.0)

            # Only create alert if:
            # 1. It's an anomaly
            # 2. Confidence meets minimum threshold
            if is_anomaly and confidence >= min_confidence_for_alert:
                alert_id = self.create_alert_from_anomaly(
                    device_id=device_id,
                    metric_name=metric_name,
                    value=value,
                    anomaly_score=anomaly_score,
                    confidence=confidence,
                    model_id=model_id
                )

                return alert_id
            else:
                logger.debug(
                    f"Anomaly not alerting: is_anomaly={is_anomaly}, "
                    f"confidence={confidence*100:.1f}% "
                    f"(threshold={min_confidence_for_alert*100:.1f}%)"
                )
                return None

        except Exception as e:
            logger.error(f"Error processing anomaly detection: {e}")
            return None

    def get_ml_generated_alerts(
        self,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        Get alerts generated from ML anomaly detection.

        Args:
            device_id: Filter by device (optional)
            metric_name: Filter by metric (optional)
            severity: Filter by severity (optional)
            limit: Maximum results (default: 50)

        Returns:
            List of alert dictionaries
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT
                            a.*,
                            d.name as device_name,
                            r.name as rule_name
                        FROM alerts a
                        LEFT JOIN devices d ON a.device_id = d.id
                        LEFT JOIN rules r ON a.rule_id = r.id
                        WHERE a.metadata->>'source' = 'ml_anomaly_detection'
                    """
                    params = []

                    if device_id:
                        query += " AND a.device_id = %s"
                        params.append(device_id)

                    if metric_name:
                        query += " AND a.metadata->>'metric_name' = %s"
                        params.append(metric_name)

                    if severity:
                        query += " AND a.severity = %s"
                        params.append(severity)

                    query += " ORDER BY a.created_at DESC LIMIT %s"
                    params.append(limit)

                    cursor.execute(query, params)
                    alerts = cursor.fetchall()

                return [dict(a) for a in alerts]

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error getting ML-generated alerts: {e}")
            return []


# =============================================================================
# Helper function for easy integration
# =============================================================================

def create_alert_from_ml_prediction(
    db_config: Dict[str, Any],
    device_id: str,
    metric_name: str,
    value: float,
    prediction: Dict[str, Any],
    model_id: str
) -> Optional[str]:
    """
    Convenience function to create alert from ML prediction.

    Args:
        db_config: Database configuration
        device_id: Device UUID
        metric_name: Metric name
        value: Measured value
        prediction: ML prediction result
        model_id: ML model UUID

    Returns:
        Alert UUID if created, None otherwise

    Example:
        prediction = detector.predict(temperature_value)
        alert_id = create_alert_from_ml_prediction(
            DB_CONFIG, device_id, 'temperature', temperature_value,
            prediction, model_id
        )
    """
    integration = MLAlertIntegration(db_config)
    return integration.process_anomaly_detection(
        device_id, metric_name, value, prediction, model_id
    )


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    print("=== ML-Alerting Integration ===\n")

    # Example: Map confidence to severity
    integration = MLAlertIntegration(DB_CONFIG)

    print("Confidence to Severity Mapping:")
    for confidence in [0.95, 0.85, 0.70, 0.55, 0.40]:
        severity = integration.map_confidence_to_severity(confidence)
        print(f"  {confidence*100:.0f}% confidence → {severity} severity")

    print("\n✓ ML-Alerting integration ready")
