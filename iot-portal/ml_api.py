#!/usr/bin/env python3
"""
ML API Endpoints for INSA Advanced IIoT Platform v2.0
Phase 3 Feature 2: Machine Learning Anomaly Detection
Version: 1.0
Date: October 28, 2025

REST API endpoints for ML model management and predictions.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import pandas as pd
import os
import logging

from ml_model_manager import AnomalyDetector

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/v1/ml')

# Model storage directory
MODEL_STORAGE_DIR = os.environ.get('ML_MODEL_STORAGE_DIR', '/var/lib/insa-iiot/ml_models')

# Database connection helper
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', 5432),
            database=os.environ.get('DB_NAME', 'insa_iiot'),
            user=os.environ.get('DB_USER', 'iiot_user'),
            password=os.environ.get('DB_PASSWORD', 'iiot_secure_2025')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


# ============================================================================
# Training Endpoints
# ============================================================================

@ml_api.route('/models/train', methods=['POST'])
@jwt_required()
def train_model():
    """
    Train new ML model for device/metric.

    Request JSON:
    {
        "device_id": "DEVICE-001",
        "metric_name": "temperature",
        "training_window_days": 7
    }

    Returns:
    {
        "model_id": "uuid",
        "training_samples": 1000,
        "training_time": 1.5,
        "accuracy": 0.95
    }
    """
    try:
        data = request.get_json()

        device_id = data.get('device_id')
        metric_name = data.get('metric_name')
        training_window_days = data.get('training_window_days', 7)

        if not device_id or not metric_name:
            return jsonify({'error': 'device_id and metric_name required'}), 400

        # Get historical telemetry data
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT timestamp, value
                FROM telemetry
                WHERE device_id = %s AND metric_name = %s
                    AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (device_id, metric_name, training_window_days))
            rows = cursor.fetchall()

        conn.close()

        if len(rows) < 10:
            return jsonify({
                'error': f'Insufficient data: {len(rows)} samples (minimum 10 required)'
            }), 400

        # Convert to DataFrame
        df = pd.DataFrame(rows)

        # Train model
        detector = AnomalyDetector(device_id, metric_name)
        result = detector.train(df)

        # Save model
        model_dir = os.path.join(MODEL_STORAGE_DIR, device_id, metric_name)
        os.makedirs(model_dir, exist_ok=True)

        model_filename = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        model_path = os.path.join(model_dir, model_filename)

        detector.save_model(model_path)

        # Save model metadata to database
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Deactivate old models
            cursor.execute("""
                UPDATE ml_models
                SET status = 'inactive', updated_at = NOW()
                WHERE device_id = %s AND metric_name = %s AND status = 'active'
            """, (device_id, metric_name))

            # Insert new model
            cursor.execute("""
                INSERT INTO ml_models (
                    id, device_id, metric_name, model_path,
                    training_samples, trained_at, status
                )
                VALUES (%s, %s, %s, %s, %s, NOW(), 'active')
                RETURNING id
            """, (result['model_id'], device_id, metric_name, model_path,
                  result['training_samples']))

            conn.commit()

        conn.close()

        logger.info(f"Model trained: {result['model_id']} for {device_id}/{metric_name}")

        return jsonify({
            'success': True,
            'model_id': result['model_id'],
            'device_id': device_id,
            'metric_name': metric_name,
            'training_samples': result['training_samples'],
            'training_time': result['training_time'],
            'message': 'Model trained successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error training model: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Prediction Endpoints
# ============================================================================

@ml_api.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Predict if a value is anomalous.

    Request JSON:
    {
        "device_id": "DEVICE-001",
        "metric_name": "temperature",
        "value": 45.0
    }

    Returns:
    {
        "is_anomaly": true,
        "score": -0.85,
        "confidence": 0.92,
        "model_id": "uuid"
    }
    """
    try:
        data = request.get_json()

        device_id = data.get('device_id')
        metric_name = data.get('metric_name')
        value = data.get('value')

        if device_id is None or metric_name is None or value is None:
            return jsonify({'error': 'device_id, metric_name, and value required'}), 400

        # Get active model from database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, model_path
                FROM ml_models
                WHERE device_id = %s AND metric_name = %s AND status = 'active'
                ORDER BY trained_at DESC
                LIMIT 1
            """, (device_id, metric_name))

            model_row = cursor.fetchone()

        if not model_row:
            conn.close()
            return jsonify({
                'error': f'No trained model found for {device_id}/{metric_name}'
            }), 404

        model_id = model_row['id']
        model_path = model_row['model_path']

        # Load and predict
        detector = AnomalyDetector(device_id, metric_name)
        detector.load_model(model_path)

        result = detector.predict(value)

        # Save prediction to database
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO anomaly_detections (
                    model_id, device_id, metric_name,
                    value, anomaly_score, is_anomaly, confidence
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (model_id, device_id, metric_name, value,
                  result['score'], result['is_anomaly'], result['confidence']))

            # Update model last_used_at
            cursor.execute("""
                UPDATE ml_models SET last_used_at = NOW()
                WHERE id = %s
            """, (model_id,))

            conn.commit()

        conn.close()

        logger.info(f"Prediction: {device_id}/{metric_name} = {value} → anomaly={result['is_anomaly']}")

        return jsonify({
            'success': True,
            'model_id': str(model_id),
            'is_anomaly': result['is_anomaly'],
            'score': result['score'],
            'confidence': result['confidence'],
            'value': value,
            'timestamp': result['timestamp']
        }), 200

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return jsonify({'error': str(e)}), 500


@ml_api.route('/predict/batch', methods=['POST'])
@jwt_required()
def predict_batch():
    """
    Predict anomalies for multiple values.

    Request JSON:
    {
        "device_id": "DEVICE-001",
        "metric_name": "temperature",
        "values": [25.0, 25.5, 45.0, 50.0]
    }

    Returns:
    {
        "predictions": [...],
        "anomaly_count": 2,
        "total": 4
    }
    """
    try:
        data = request.get_json()

        device_id = data.get('device_id')
        metric_name = data.get('metric_name')
        values = data.get('values', [])

        if not device_id or not metric_name or not values:
            return jsonify({'error': 'device_id, metric_name, and values required'}), 400

        # Get model
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, model_path
                FROM ml_models
                WHERE device_id = %s AND metric_name = %s AND status = 'active'
                LIMIT 1
            """, (device_id, metric_name))

            model_row = cursor.fetchone()

        if not model_row:
            conn.close()
            return jsonify({'error': 'No trained model found'}), 404

        model_id = model_row['id']
        model_path = model_row['model_path']

        # Load and predict
        detector = AnomalyDetector(device_id, metric_name)
        detector.load_model(model_path)

        result = detector.predict_batch(values)

        conn.close()

        return jsonify({
            'success': True,
            'model_id': str(model_id),
            'predictions': result['predictions'],
            'anomaly_count': result['anomaly_count'],
            'total': result['total']
        }), 200

    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Model Management Endpoints
# ============================================================================

@ml_api.route('/models', methods=['GET'])
@jwt_required()
def list_models():
    """List all trained models"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id, device_id, metric_name, model_type, status,
                    training_samples, trained_at, last_used_at
                FROM ml_models
                ORDER BY trained_at DESC
            """)
            models = cursor.fetchall()

        conn.close()

        # Convert to JSON serializable
        for model in models:
            model['id'] = str(model['id'])
            if model['trained_at']:
                model['trained_at'] = model['trained_at'].isoformat()
            if model['last_used_at']:
                model['last_used_at'] = model['last_used_at'].isoformat()

        return jsonify({
            'success': True,
            'models': models,
            'total': len(models),
            'active_count': sum(1 for m in models if m['status'] == 'active')
        }), 200

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({'error': str(e)}), 500


@ml_api.route('/models/<model_id>', methods=['GET'])
@jwt_required()
def get_model(model_id):
    """Get model details"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM ml_models WHERE id = %s
            """, (model_id,))
            model = cursor.fetchone()

        conn.close()

        if not model:
            return jsonify({'error': 'Model not found'}), 404

        # Convert timestamps
        model['id'] = str(model['id'])
        if model['trained_at']:
            model['trained_at'] = model['trained_at'].isoformat()
        if model['last_used_at']:
            model['last_used_at'] = model['last_used_at'].isoformat()

        return jsonify({
            'success': True,
            'model': model
        }), 200

    except Exception as e:
        logger.error(f"Error getting model: {e}")
        return jsonify({'error': str(e)}), 500


@ml_api.route('/anomalies', methods=['GET'])
@jwt_required()
def get_anomalies():
    """
    Get recent anomalies.

    Query params:
    - device_id (optional)
    - from (optional, ISO timestamp)
    - to (optional, ISO timestamp)
    - limit (optional, default 100)
    """
    try:
        device_id = request.args.get('device_id')
        from_time = request.args.get('from')
        to_time = request.args.get('to')
        limit = int(request.args.get('limit', 100))

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        # Build query
        where_clauses = ["is_anomaly = TRUE"]
        params = []

        if device_id:
            where_clauses.append("device_id = %s")
            params.append(device_id)

        if from_time:
            where_clauses.append("timestamp >= %s")
            params.append(from_time)

        if to_time:
            where_clauses.append("timestamp <= %s")
            params.append(to_time)

        query = f"""
            SELECT
                id, model_id, device_id, metric_name,
                value, anomaly_score, confidence, timestamp
            FROM anomaly_detections
            WHERE {' AND '.join(where_clauses)}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params.append(limit)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            anomalies = cursor.fetchall()

        conn.close()

        # Convert to JSON
        for anomaly in anomalies:
            anomaly['id'] = str(anomaly['id'])
            anomaly['model_id'] = str(anomaly['model_id'])
            if anomaly['timestamp']:
                anomaly['timestamp'] = anomaly['timestamp'].isoformat()

        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'total': len(anomalies)
        }), 200

    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        return jsonify({'error': str(e)}), 500


@ml_api.route('/models/<model_id>', methods=['DELETE'])
@jwt_required()
def delete_model(model_id):
    """Delete a model"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM ml_models WHERE id = %s
            """, (model_id,))
            deleted = cursor.rowcount
            conn.commit()

        conn.close()

        if deleted == 0:
            return jsonify({'error': 'Model not found'}), 404

        return jsonify({
            'success': True,
            'message': f'Model {model_id} deleted'
        }), 200

    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return jsonify({'error': str(e)}), 500
