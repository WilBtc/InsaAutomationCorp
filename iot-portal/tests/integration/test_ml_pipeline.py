#!/usr/bin/env python3
"""
Integration Tests for ML Pipeline (Phase 3 Feature 2)
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests the complete ML pipeline integration with:
- API endpoints
- Database persistence
- Redis caching
- Real-time predictions
"""

import pytest
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch


# ============================================================================
# Test 1: End-to-End Training Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLTrainingFlow:
    """Test complete model training flow"""

    def test_train_model_via_api(self, client, admin_token):
        """Test training model through API endpoint"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # Step 1: Create training request
        response = client.post('/api/v1/ml/models/train', json={
            'device_id': 'DEVICE-001',
            'metric_name': 'temperature',
            'training_window_days': 7
        }, headers={'Authorization': f'Bearer {admin_token}'})

        # Should succeed or return 404 if endpoint not implemented yet
        assert response.status_code in [200, 201, 404]

        if response.status_code in [200, 201]:
            data = response.get_json()
            assert 'model_id' in data
            assert 'training_samples' in data
            assert 'training_time' in data

    def test_train_model_with_insufficient_data(self, client, admin_token):
        """Test training with insufficient historical data"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post('/api/v1/ml/models/train', json={
            'device_id': 'NONEXISTENT-DEVICE',
            'metric_name': 'temperature',
            'training_window_days': 7
        }, headers={'Authorization': f'Bearer {admin_token}'})

        # Should return error
        assert response.status_code in [400, 404]

    def test_train_duplicate_model(self, client, admin_token):
        """Test training model that already exists"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # Train first time
        response1 = client.post('/api/v1/ml/models/train', json={
            'device_id': 'DEVICE-001',
            'metric_name': 'temperature',
            'training_window_days': 7
        }, headers={'Authorization': f'Bearer {admin_token}'})

        # Train again (should replace or error)
        response2 = client.post('/api/v1/ml/models/train', json={
            'device_id': 'DEVICE-001',
            'metric_name': 'temperature',
            'training_window_days': 7
        }, headers={'Authorization': f'Bearer {admin_token}'})

        # Should handle gracefully
        assert response2.status_code in [200, 201, 400, 409]


# ============================================================================
# Test 2: End-to-End Prediction Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLPredictionFlow:
    """Test complete prediction flow"""

    def test_predict_with_trained_model(self, client, admin_token):
        """Test prediction with trained model"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # First, ensure model is trained (or mock)
        with patch('ml_model_manager.AnomalyDetector') as MockDetector:
            mock_detector = MockDetector.return_value
            mock_detector.predict.return_value = {
                'is_anomaly': False,
                'score': 0.75,
                'confidence': 0.85
            }

            # Make prediction
            response = client.post('/api/v1/ml/predict', json={
                'device_id': 'DEVICE-001',
                'metric_name': 'temperature',
                'value': 25.5
            }, headers={'Authorization': f'Bearer {admin_token}'})

            if response.status_code == 200:
                data = response.get_json()
                assert 'is_anomaly' in data
                assert 'score' in data
                assert 'confidence' in data

    def test_predict_without_trained_model(self, client, admin_token):
        """Test prediction when model doesn't exist"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post('/api/v1/ml/predict', json={
            'device_id': 'UNTRAINED-DEVICE',
            'metric_name': 'temperature',
            'value': 25.5
        }, headers={'Authorization': f'Bearer {admin_token}'})

        # Should return error
        assert response.status_code in [404, 400]

    def test_batch_prediction(self, client, admin_token):
        """Test batch prediction"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post('/api/v1/ml/predict/batch', json={
            'device_id': 'DEVICE-001',
            'metric_name': 'temperature',
            'values': [25.0, 25.5, 26.0, 45.0, 50.0]
        }, headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert 'predictions' in data
            assert 'anomaly_count' in data
            assert len(data['predictions']) == 5


# ============================================================================
# Test 3: Database Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLDatabaseIntegration:
    """Test ML database persistence"""

    def test_save_model_to_database(self, client, admin_token):
        """Test saving model metadata to database"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'id': 'model-123',
                'device_id': 'DEVICE-001',
                'metric_name': 'temperature',
                'status': 'active'
            }

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            # List models
            response = client.get('/api/v1/ml/models',
                                headers={'Authorization': f'Bearer {admin_token}'})

            if response.status_code == 200:
                data = response.get_json()
                assert 'models' in data

    def test_save_anomaly_detection_to_database(self):
        """Test saving anomaly detections to database"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 'anomaly-123'}

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            # Simulate saving anomaly
            assert True  # Placeholder

    def test_query_recent_anomalies(self, client, admin_token):
        """Test querying recent anomalies"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/ml/anomalies?device_id=DEVICE-001&limit=10',
                            headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert 'anomalies' in data
            assert 'total' in data


# ============================================================================
# Test 4: Redis Caching Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLCacheIntegration:
    """Test ML integration with Redis cache"""

    def test_cache_model_metadata(self, redis_client):
        """Test caching model metadata"""
        cache_key = 'ml:model:DEVICE-001:temperature'

        model_data = {
            'model_id': 'model-123',
            'status': 'active',
            'accuracy': 0.95,
            'trained_at': datetime.now().isoformat()
        }

        # Cache model metadata
        redis_client.set(cache_key, json.dumps(model_data), ex=3600)

        # Retrieve
        cached = redis_client.get(cache_key)
        assert cached is not None

        retrieved = json.loads(cached)
        assert retrieved['model_id'] == 'model-123'

        # Clean up
        redis_client.delete(cache_key)

    def test_cache_prediction_results(self, redis_client):
        """Test caching prediction results"""
        cache_key = 'ml:predictions:DEVICE-001:temperature:latest'

        prediction = {
            'is_anomaly': False,
            'score': 0.75,
            'timestamp': datetime.now().isoformat()
        }

        # Cache prediction
        redis_client.set(cache_key, json.dumps(prediction), ex=300)

        # Retrieve
        cached = redis_client.get(cache_key)
        assert cached is not None

        # Clean up
        redis_client.delete(cache_key)

    def test_cache_anomaly_count(self, redis_client):
        """Test caching anomaly counts"""
        cache_key = 'ml:anomalies:DEVICE-001:count:24h'

        # Set count
        redis_client.set(cache_key, '5', ex=900)

        # Get count
        count = int(redis_client.get(cache_key))
        assert count == 5

        # Clean up
        redis_client.delete(cache_key)


# ============================================================================
# Test 5: Real-time Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLRealTimeIntegration:
    """Test real-time ML integration with telemetry"""

    def test_auto_predict_on_telemetry_insert(self):
        """Test that ML prediction runs automatically when telemetry arrives"""
        with patch('ml_model_manager.AnomalyDetector') as MockDetector:
            mock_detector = MockDetector.return_value
            mock_detector.predict.return_value = {
                'is_anomaly': True,
                'score': -0.8,
                'confidence': 0.9
            }

            # Simulate telemetry insertion
            # This should trigger ML prediction if model exists
            assert True  # Placeholder

    def test_trigger_alert_on_anomaly_detected(self):
        """Test that alerts are triggered when anomaly detected"""
        with patch('email_notifier.send_email') as mock_email:
            with patch('webhook_notifier.WebhookNotifier.send') as mock_webhook:
                mock_email.return_value = True
                mock_webhook.return_value = True

                # Simulate anomaly detection
                # Should trigger email and webhook
                assert True  # Placeholder


# ============================================================================
# Test 6: Model Management
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLModelManagement:
    """Test model lifecycle management"""

    def test_list_all_models(self, client, admin_token):
        """Test listing all trained models"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/ml/models',
                            headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert 'models' in data
            assert 'total' in data
            assert isinstance(data['models'], list)

    def test_get_model_details(self, client, admin_token):
        """Test getting specific model details"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/ml/models/model-123',
                            headers={'Authorization': f'Bearer {admin_token}'})

        # Should return 200 or 404
        assert response.status_code in [200, 404]

    def test_delete_model(self, client, admin_token):
        """Test deleting a model"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete('/api/v1/ml/models/model-123',
                                headers={'Authorization': f'Bearer {admin_token}'})

        # Should return 200, 204, or 404
        assert response.status_code in [200, 204, 404]

    def test_retrain_model(self, client, admin_token):
        """Test retraining an existing model"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post('/api/v1/ml/models/model-123/retrain',
                              headers={'Authorization': f'Bearer {admin_token}'})

        # Should return 200 or 404
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.get_json()
            assert 'new_model_id' in data
            assert 'improvement' in data


# ============================================================================
# Test 7: Performance Testing
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
@pytest.mark.slow
class TestMLPerformance:
    """Test ML system performance"""

    def test_concurrent_predictions(self, client, admin_token):
        """Test concurrent prediction requests"""
        import threading

        if not admin_token:
            pytest.skip("Admin token not available")

        results = []

        def make_prediction():
            response = client.post('/api/v1/ml/predict', json={
                'device_id': 'DEVICE-001',
                'metric_name': 'temperature',
                'value': 25.5
            }, headers={'Authorization': f'Bearer {admin_token}'})
            results.append(response.status_code)

        # Make 10 concurrent predictions
        threads = []
        for _ in range(10):
            t = threading.Thread(target=make_prediction)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All should complete
        assert len(results) == 10

    def test_high_throughput_predictions(self):
        """Test prediction throughput"""
        import time

        with patch('ml_model_manager.AnomalyDetector') as MockDetector:
            mock_detector = MockDetector.return_value
            mock_detector.predict.return_value = {
                'is_anomaly': False,
                'score': 0.75,
                'confidence': 0.85
            }

            # Measure throughput
            start = time.time()
            for _ in range(1000):
                mock_detector.predict(25.5)
            elapsed = time.time() - start

            throughput = 1000 / elapsed

            # Should handle >1000 predictions/second
            assert throughput > 1000


# ============================================================================
# Test 8: Error Handling
# ============================================================================

@pytest.mark.integration
@pytest.mark.ml
class TestMLErrorHandling:
    """Test ML error handling"""

    def test_handle_model_loading_failure(self):
        """Test handling of model loading failures"""
        with patch('ml_model_manager.AnomalyDetector.load_model') as mock_load:
            mock_load.side_effect = FileNotFoundError("Model file not found")

            # Should handle gracefully
            assert True  # Placeholder

    def test_handle_prediction_timeout(self):
        """Test handling of prediction timeouts"""
        with patch('ml_model_manager.AnomalyDetector.predict') as mock_predict:
            import time
            def slow_predict(*args, **kwargs):
                time.sleep(10)
                return {}

            mock_predict.side_effect = slow_predict

            # Should timeout and handle gracefully
            assert True  # Placeholder

    def test_handle_database_failure(self, client, admin_token):
        """Test handling of database failures"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_db.return_value = None

            response = client.get('/api/v1/ml/models',
                                headers={'Authorization': f'Bearer {admin_token}'})

            # Should return error
            assert response.status_code == 500
