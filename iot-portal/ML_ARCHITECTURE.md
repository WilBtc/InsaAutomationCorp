# Machine Learning Anomaly Detection Architecture
# Phase 3 Feature 2 - INSA Advanced IIoT Platform v2.0
# Version: 1.0
# Date: October 28, 2025

## Overview

Transform the platform from reactive monitoring to **predictive maintenance** using scikit-learn machine learning models to detect anomalies before they cause failures.

## Architecture Components

### 1. ML Model Manager (`ml_model_manager.py`)

**Purpose**: Manage ML models (training, loading, saving, scoring)

**Core Class**: `AnomalyDetector`
- Algorithm: Isolation Forest (unsupervised learning)
- Library: scikit-learn 1.6.1
- Input: Historical telemetry data
- Output: Anomaly scores (-1 = anomaly, 1 = normal)

**Methods**:
```python
class AnomalyDetector:
    def __init__(self, device_id, metric_name)
    def train(self, data: pd.DataFrame) -> dict
    def predict(self, value: float) -> dict
    def save_model(self, path: str) -> bool
    def load_model(self, path: str) -> bool
    def get_model_info() -> dict
    def retrain(self, data: pd.DataFrame) -> dict
```

### 2. API Endpoints (REST API)

**Training Endpoints**:
```
POST /api/v1/ml/models/train
    - Train new model for device/metric
    - Requires: device_id, metric_name, training_window (days)
    - Returns: model_id, accuracy, training_time

GET /api/v1/ml/models
    - List all trained models
    - Returns: models[], total, active_count

GET /api/v1/ml/models/<model_id>
    - Get model details
    - Returns: model info, metrics, status

DELETE /api/v1/ml/models/<model_id>
    - Delete model
    - Returns: success
```

**Prediction Endpoints**:
```
POST /api/v1/ml/predict
    - Score single data point
    - Requires: device_id, metric_name, value
    - Returns: is_anomaly, score, confidence

POST /api/v1/ml/predict/batch
    - Score multiple data points
    - Requires: device_id, metric_name, values[]
    - Returns: predictions[], anomaly_count

GET /api/v1/ml/anomalies
    - Get recent anomalies
    - Query params: device_id, from, to, limit
    - Returns: anomalies[], total
```

**Management Endpoints**:
```
POST /api/v1/ml/models/<model_id>/retrain
    - Retrain existing model
    - Returns: new_model_id, improvement_percentage

GET /api/v1/ml/models/<model_id>/performance
    - Get model performance metrics
    - Returns: accuracy, false_positive_rate, last_trained

PUT /api/v1/ml/models/<model_id>/threshold
    - Update anomaly threshold
    - Requires: threshold (0.0-1.0)
    - Returns: success
```

### 3. Database Schema

**New Tables**:

```sql
-- ML Models
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'isolation_forest',
    model_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    accuracy FLOAT,
    false_positive_rate FLOAT,
    training_samples INTEGER,
    trained_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(device_id, metric_name, status)
);

-- Anomaly Detections
CREATE TABLE anomaly_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id),
    device_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value FLOAT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_anomaly_detections_device ON anomaly_detections(device_id, timestamp);
CREATE INDEX idx_anomaly_detections_model ON anomaly_detections(model_id);
CREATE INDEX idx_ml_models_device ON ml_models(device_id, metric_name);
```

### 4. Model Storage

**Directory Structure**:
```
/var/lib/insa-iiot/ml_models/
├── DEVICE-001/
│   ├── temperature/
│   │   ├── model_20251028_170500.pkl
│   │   ├── scaler_20251028_170500.pkl
│   │   └── metadata.json
│   └── pressure/
│       ├── model_20251028_171200.pkl
│       ├── scaler_20251028_171200.pkl
│       └── metadata.json
└── models.db (SQLite index)
```

**Model Files**:
- `model_*.pkl`: Pickled scikit-learn IsolationForest model
- `scaler_*.pkl`: StandardScaler for normalization
- `metadata.json`: Model info (accuracy, training date, parameters)

### 5. ML Pipeline Flow

**Training Flow**:
```
1. User: POST /api/v1/ml/models/train
2. API: Validate device_id, metric_name exist
3. API: Query historical telemetry (last N days)
4. MLManager: Prepare data (clean, normalize)
5. MLManager: Train IsolationForest model
6. MLManager: Calculate performance metrics
7. MLManager: Save model to disk
8. API: Insert model record to database
9. API: Return model_id, accuracy
```

**Prediction Flow**:
```
1. Telemetry arrives: POST /api/v1/telemetry
2. API: Store telemetry in database
3. API: Check if ML model exists for device/metric
4. MLManager: Load model from cache/disk
5. MLManager: Score data point
6. MLManager: Check if anomaly (score < threshold)
7. If anomaly:
   - Store in anomaly_detections table
   - Trigger alert (email/webhook)
   - Update Grafana dashboard
8. Return result
```

**Auto-retraining Flow** (via Autonomous Orchestrator):
```
1. Orchestrator: Check model age (daily)
2. If model > 7 days old:
   - Trigger retrain: POST /api/v1/ml/models/{id}/retrain
3. If model accuracy < 90%:
   - Log warning
   - Escalate to GitHub issue
4. If model fails:
   - Disable model
   - Alert admin
   - Create GitHub issue
```

## Algorithm: Isolation Forest

**Why Isolation Forest?**
- ✅ Unsupervised (no labeled data needed)
- ✅ Fast training and prediction
- ✅ Handles high-dimensional data
- ✅ Effective for outlier detection
- ✅ Built-in anomaly scoring

**Parameters**:
```python
IsolationForest(
    n_estimators=100,      # Number of trees
    contamination=0.1,     # Expected % of anomalies
    max_samples='auto',    # Samples per tree
    random_state=42        # Reproducibility
)
```

**Scoring**:
- Score range: [-1, 1]
- Score < 0: Anomaly
- Score > 0: Normal
- Confidence = abs(score)

## Performance Targets

**Training**:
- ✅ Training time: <30 seconds for 10,000 samples
- ✅ Model size: <10 MB per model
- ✅ Memory usage: <100 MB during training

**Prediction**:
- ✅ Latency: <50ms per prediction
- ✅ Throughput: >1,000 predictions/second
- ✅ Cache hit rate: >95% (Redis caching)

**Accuracy**:
- ✅ False positive rate: <5%
- ✅ True positive rate: >95%
- ✅ Precision: >90%

## Integration Points

### 1. Autonomous Orchestrator Integration

**New Task Type**: `ml_model_health_check`
```python
{
    "task_type": "ml_model_health_check",
    "frequency": "daily",
    "actions": [
        "check_model_age",
        "check_model_accuracy",
        "check_prediction_latency",
        "auto_retrain_if_needed",
        "escalate_if_degraded"
    ]
}
```

**Orchestrator Responsibilities**:
- Monitor model performance (daily)
- Auto-retrain models >7 days old
- Detect model degradation (accuracy drops)
- Escalate issues to GitHub
- Clean up old models (>30 days, inactive)

### 2. Redis Cache Integration

**Cache Keys**:
```
ml:model:DEVICE-001:temperature -> model_id
ml:predictions:DEVICE-001:temperature:latest -> {score, is_anomaly, timestamp}
ml:anomalies:DEVICE-001:count:24h -> integer
```

**Cache Strategy**:
- Model metadata: TTL 1 hour
- Latest predictions: TTL 5 minutes
- Anomaly counts: TTL 15 minutes

### 3. Grafana Dashboard

**New Panels**:
- ML Model Status (gauge: active models count)
- Anomaly Detection Rate (time series: anomalies/hour)
- Model Accuracy (bar chart: per device/metric)
- Prediction Latency (histogram: p50, p95, p99)
- False Positive Rate (gauge: last 24h)

### 4. MQTT Integration

**New Topics**:
```
insa/iiot/ml/anomaly/DEVICE-001 -> Anomaly detected
insa/iiot/ml/model/trained -> New model trained
insa/iiot/ml/model/retrained -> Model retrained
```

## Security Considerations

**Model Protection**:
- ✅ Models stored with 0600 permissions
- ✅ Model files encrypted at rest (future)
- ✅ Model training requires admin permission
- ✅ Model deletion requires admin permission

**API Security**:
- ✅ All ML endpoints require authentication
- ✅ Training/retraining require `ml:write` permission
- ✅ Prediction requires `ml:read` permission
- ✅ Rate limiting: 100 predictions/minute per user

## Testing Strategy

**Unit Tests** (30+ tests):
- Model training with valid data
- Model training with invalid data
- Prediction with trained model
- Prediction with untrained model
- Model save/load
- Model metadata
- Performance metrics calculation
- Edge cases (empty data, single point, etc.)

**Integration Tests** (20+ tests):
- End-to-end training flow
- End-to-end prediction flow
- Database persistence
- Redis caching
- MQTT notifications
- Auto-retraining
- Orchestrator integration

**Performance Tests** (10+ tests):
- Training time benchmarks
- Prediction latency benchmarks
- Memory usage profiling
- Concurrent predictions
- Large dataset handling

## Deployment Checklist

- [ ] Create `/var/lib/insa-iiot/ml_models/` directory
- [ ] Create database tables (ml_models, anomaly_detections)
- [ ] Install scikit-learn 1.6.1
- [ ] Update app_advanced.py with ML endpoints
- [ ] Deploy ml_model_manager.py
- [ ] Configure autonomous orchestrator
- [ ] Create Grafana dashboard
- [ ] Update documentation
- [ ] Run tests (target: 80%+ coverage)

## Monitoring & Alerts

**Metrics to Track**:
- Models trained per day
- Predictions per day
- Anomalies detected per day
- Model accuracy over time
- False positive rate
- Prediction latency (p50, p95, p99)
- Model storage usage

**Alerts**:
- Model accuracy < 90%
- False positive rate > 10%
- Prediction latency > 100ms
- Model training failure
- Model storage > 1GB

## Future Enhancements (Phase 4)

- [ ] Multi-metric anomaly detection (correlate multiple sensors)
- [ ] LSTM for time-series forecasting
- [ ] Auto-tuning hyperparameters
- [ ] Ensemble models (combine multiple algorithms)
- [ ] Explainable AI (SHAP values)
- [ ] Online learning (continuous retraining)
- [ ] Model versioning (A/B testing)

---

**Status**: Architecture Design Complete
**Next Step**: Write unit tests (TDD approach)
**Target Completion**: October 28, 2025 20:00 UTC
