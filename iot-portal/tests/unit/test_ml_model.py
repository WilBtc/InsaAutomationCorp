#!/usr/bin/env python3
"""
Unit Tests for ML Anomaly Detection (Phase 3 Feature 2)
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests the ML model manager using TDD approach.
These tests are written BEFORE implementation.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import os
import tempfile


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_training_data():
    """Generate sample training data (normal distribution)"""
    np.random.seed(42)

    # Normal data (95% of dataset)
    normal_data = np.random.normal(25.0, 2.0, 950)

    # Anomalies (5% of dataset)
    anomalies = np.random.normal(45.0, 5.0, 50)

    # Combine
    all_data = np.concatenate([normal_data, anomalies])
    np.random.shuffle(all_data)

    # Create DataFrame
    timestamps = [
        datetime.now() - timedelta(minutes=i)
        for i in range(len(all_data))
    ]

    return pd.DataFrame({
        'timestamp': timestamps,
        'value': all_data
    })


@pytest.fixture
def sample_test_data():
    """Generate test data for predictions"""
    return {
        'normal_values': [24.5, 25.0, 25.5, 26.0, 24.8],
        'anomaly_values': [45.0, 50.0, 55.0, 60.0, -10.0]
    }


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for model storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Test 1: Model Initialization
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestModelInitialization:
    """Test AnomalyDetector initialization"""

    def test_init_with_valid_params(self):
        """Test initialization with valid parameters"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector(
            device_id='DEVICE-001',
            metric_name='temperature'
        )

        assert detector.device_id == 'DEVICE-001'
        assert detector.metric_name == 'temperature'
        assert detector.model is None  # Not trained yet
        assert detector.scaler is None

    def test_init_with_invalid_device_id(self):
        """Test initialization with invalid device_id"""
        from ml_model_manager import AnomalyDetector

        with pytest.raises(ValueError):
            AnomalyDetector(
                device_id='',
                metric_name='temperature'
            )

    def test_init_with_invalid_metric_name(self):
        """Test initialization with invalid metric_name"""
        from ml_model_manager import AnomalyDetector

        with pytest.raises(ValueError):
            AnomalyDetector(
                device_id='DEVICE-001',
                metric_name=''
            )

    def test_init_with_custom_parameters(self):
        """Test initialization with custom model parameters"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector(
            device_id='DEVICE-001',
            metric_name='temperature',
            contamination=0.05,
            n_estimators=200
        )

        assert detector.contamination == 0.05
        assert detector.n_estimators == 200


# ============================================================================
# Test 2: Model Training
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestModelTraining:
    """Test model training functionality"""

    def test_train_with_valid_data(self, sample_training_data):
        """Test training with valid data"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        result = detector.train(sample_training_data)

        # Model should be trained
        assert detector.model is not None
        assert detector.scaler is not None

        # Result should contain metrics
        assert 'model_id' in result
        assert 'training_samples' in result
        assert 'training_time' in result
        assert result['training_samples'] == 1000

    def test_train_with_insufficient_data(self):
        """Test training with too few samples"""
        from ml_model_manager import AnomalyDetector

        # Only 5 samples (need at least 10)
        insufficient_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(5)],
            'value': [25.0, 25.5, 24.8, 25.2, 25.1]
        })

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        with pytest.raises(ValueError, match="Insufficient data"):
            detector.train(insufficient_data)

    def test_train_with_missing_columns(self):
        """Test training with missing required columns"""
        from ml_model_manager import AnomalyDetector

        # Missing 'value' column
        invalid_data = pd.DataFrame({
            'timestamp': [datetime.now()]
        })

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        with pytest.raises(ValueError, match="Missing required column"):
            detector.train(invalid_data)

    def test_train_with_nan_values(self, sample_training_data):
        """Test training with NaN values (should clean data)"""
        from ml_model_manager import AnomalyDetector

        # Add some NaN values
        dirty_data = sample_training_data.copy()
        dirty_data.loc[0:10, 'value'] = np.nan

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        result = detector.train(dirty_data)

        # Should clean NaN and train successfully
        assert result['training_samples'] < 1000  # Some removed
        assert detector.model is not None

    def test_retrain_existing_model(self, sample_training_data):
        """Test retraining an already trained model"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        # Train first time
        result1 = detector.train(sample_training_data)
        model_id_1 = result1['model_id']

        # Retrain
        new_data = sample_training_data.copy()
        new_data['value'] = new_data['value'] + 5.0  # Shift distribution

        result2 = detector.retrain(new_data)
        model_id_2 = result2['model_id']

        # Should have new model ID
        assert model_id_2 != model_id_1
        assert 'improvement' in result2


# ============================================================================
# Test 3: Anomaly Prediction
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestAnomalyPrediction:
    """Test anomaly prediction functionality"""

    def test_predict_normal_value(self, sample_training_data):
        """Test prediction with normal value"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Predict normal value
        result = detector.predict(25.0)

        assert 'is_anomaly' in result
        assert 'score' in result
        assert 'confidence' in result
        assert result['is_anomaly'] is False
        assert result['score'] > 0  # Positive score = normal

    def test_predict_anomaly_value(self, sample_training_data):
        """Test prediction with anomaly value"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Predict anomaly value (far from normal)
        result = detector.predict(100.0)

        assert result['is_anomaly'] is True
        assert result['score'] < 0  # Negative score = anomaly
        assert 0 <= result['confidence'] <= 1

    def test_predict_without_training(self):
        """Test prediction without training model first"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        with pytest.raises(RuntimeError, match="Model not trained"):
            detector.predict(25.0)

    def test_predict_batch(self, sample_training_data, sample_test_data):
        """Test batch prediction"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Predict batch
        values = sample_test_data['normal_values'] + sample_test_data['anomaly_values']
        result = detector.predict_batch(values)

        assert 'predictions' in result
        assert 'anomaly_count' in result
        assert len(result['predictions']) == len(values)
        assert result['anomaly_count'] >= 0

    def test_predict_edge_values(self, sample_training_data):
        """Test prediction with edge case values"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Test boundary values
        edge_values = [0.0, -100.0, 1000.0, float('inf')]

        for value in edge_values[:-1]:  # Skip inf for now
            result = detector.predict(value)
            assert 'is_anomaly' in result


# ============================================================================
# Test 4: Model Persistence
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestModelPersistence:
    """Test model save/load functionality"""

    def test_save_model(self, sample_training_data, temp_model_dir):
        """Test saving trained model"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Save model
        model_path = os.path.join(temp_model_dir, 'model.pkl')
        result = detector.save_model(model_path)

        assert result is True
        assert os.path.exists(model_path)
        assert os.path.exists(model_path.replace('.pkl', '_scaler.pkl'))

    def test_load_model(self, sample_training_data, temp_model_dir):
        """Test loading saved model"""
        from ml_model_manager import AnomalyDetector

        # Train and save
        detector1 = AnomalyDetector('DEVICE-001', 'temperature')
        detector1.train(sample_training_data)

        model_path = os.path.join(temp_model_dir, 'model.pkl')
        detector1.save_model(model_path)

        # Load in new detector
        detector2 = AnomalyDetector('DEVICE-001', 'temperature')
        result = detector2.load_model(model_path)

        assert result is True
        assert detector2.model is not None
        assert detector2.scaler is not None

    def test_save_untrained_model(self, temp_model_dir):
        """Test saving model before training"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        model_path = os.path.join(temp_model_dir, 'model.pkl')

        with pytest.raises(RuntimeError, match="No model to save"):
            detector.save_model(model_path)

    def test_load_nonexistent_model(self, temp_model_dir):
        """Test loading model that doesn't exist"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        model_path = os.path.join(temp_model_dir, 'nonexistent.pkl')

        with pytest.raises(FileNotFoundError):
            detector.load_model(model_path)

    def test_model_persistence_consistency(self, sample_training_data, temp_model_dir):
        """Test that loaded model makes same predictions"""
        from ml_model_manager import AnomalyDetector

        # Train and save
        detector1 = AnomalyDetector('DEVICE-001', 'temperature')
        detector1.train(sample_training_data)

        model_path = os.path.join(temp_model_dir, 'model.pkl')
        detector1.save_model(model_path)

        # Predict with original
        result1 = detector1.predict(25.0)

        # Load and predict
        detector2 = AnomalyDetector('DEVICE-001', 'temperature')
        detector2.load_model(model_path)
        result2 = detector2.predict(25.0)

        # Should be identical
        assert result1['is_anomaly'] == result2['is_anomaly']
        assert abs(result1['score'] - result2['score']) < 0.001


# ============================================================================
# Test 5: Model Metadata
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestModelMetadata:
    """Test model metadata and info"""

    def test_get_model_info(self, sample_training_data):
        """Test getting model information"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        info = detector.get_model_info()

        assert 'model_id' in info
        assert 'device_id' in info
        assert 'metric_name' in info
        assert 'model_type' in info
        assert 'training_samples' in info
        assert 'trained_at' in info
        assert info['model_type'] == 'isolation_forest'

    def test_model_info_before_training(self):
        """Test getting info before training"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        info = detector.get_model_info()

        assert info['status'] == 'untrained'
        assert info['training_samples'] == 0


# ============================================================================
# Test 6: Performance Metrics
# ============================================================================

@pytest.mark.unit
@pytest.mark.ml
class TestPerformanceMetrics:
    """Test model performance calculation"""

    def test_calculate_accuracy(self, sample_training_data):
        """Test accuracy calculation on test set"""
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Calculate performance on holdout set
        test_data = sample_training_data.sample(n=100)
        metrics = detector.calculate_performance(test_data)

        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 0 <= metrics['accuracy'] <= 1

    @pytest.mark.slow
    def test_training_time_benchmark(self, sample_training_data):
        """Test that training completes within time budget"""
        import time
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')

        start = time.time()
        detector.train(sample_training_data)
        elapsed = time.time() - start

        # Should train in <30 seconds for 1000 samples
        assert elapsed < 30.0

    def test_prediction_latency(self, sample_training_data):
        """Test prediction latency"""
        import time
        from ml_model_manager import AnomalyDetector

        detector = AnomalyDetector('DEVICE-001', 'temperature')
        detector.train(sample_training_data)

        # Measure 100 predictions
        start = time.time()
        for _ in range(100):
            detector.predict(25.0)
        elapsed = time.time() - start

        avg_latency = elapsed / 100

        # Should be <50ms per prediction
        assert avg_latency < 0.05
