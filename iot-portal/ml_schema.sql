-- ML Database Schema for INSA Advanced IIoT Platform v2.0
-- Phase 3 Feature 2: Machine Learning Anomaly Detection
-- Version: 1.0
-- Date: October 28, 2025

-- Drop existing tables if they exist (for clean install)
DROP TABLE IF EXISTS anomaly_detections CASCADE;
DROP TABLE IF EXISTS ml_models CASCADE;

-- ============================================================================
-- ML Models Table
-- ============================================================================
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'isolation_forest',
    model_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',

    -- Performance metrics
    accuracy FLOAT,
    false_positive_rate FLOAT,
    training_samples INTEGER,
    contamination FLOAT DEFAULT 0.1,
    n_estimators INTEGER DEFAULT 100,

    -- Timestamps
    trained_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure only one active model per device/metric
    CONSTRAINT unique_active_model UNIQUE(device_id, metric_name, status)
);

-- Indexes for performance
CREATE INDEX idx_ml_models_device ON ml_models(device_id, metric_name);
CREATE INDEX idx_ml_models_status ON ml_models(status);
CREATE INDEX idx_ml_models_trained_at ON ml_models(trained_at DESC);

-- ============================================================================
-- Anomaly Detections Table
-- ============================================================================
CREATE TABLE anomaly_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,

    -- Prediction data
    value FLOAT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE,
    confidence FLOAT,

    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Additional metadata (JSON)
    metadata JSONB,

    -- Link to telemetry if needed
    telemetry_id UUID
);

-- Indexes for querying anomalies
CREATE INDEX idx_anomaly_detections_device ON anomaly_detections(device_id, timestamp DESC);
CREATE INDEX idx_anomaly_detections_model ON anomaly_detections(model_id);
CREATE INDEX idx_anomaly_detections_anomaly ON anomaly_detections(is_anomaly, timestamp DESC);
CREATE INDEX idx_anomaly_detections_timestamp ON anomaly_detections(timestamp DESC);

-- ============================================================================
-- Create model storage directory (system level)
-- ============================================================================
-- Run this command manually:
-- sudo mkdir -p /var/lib/insa-iiot/ml_models
-- sudo chown -R wil:wil /var/lib/insa-iiot/ml_models
-- sudo chmod 755 /var/lib/insa-iiot/ml_models

-- ============================================================================
-- Sample Queries (for testing)
-- ============================================================================

-- Get all active models
-- SELECT * FROM ml_models WHERE status = 'active' ORDER BY trained_at DESC;

-- Get recent anomalies for a device
-- SELECT * FROM anomaly_detections
-- WHERE device_id = 'DEVICE-001' AND is_anomaly = TRUE
-- ORDER BY timestamp DESC LIMIT 10;

-- Get model performance summary
-- SELECT
--     device_id,
--     metric_name,
--     accuracy,
--     training_samples,
--     trained_at
-- FROM ml_models
-- WHERE status = 'active';

-- Count anomalies in last 24 hours
-- SELECT
--     device_id,
--     COUNT(*) as anomaly_count
-- FROM anomaly_detections
-- WHERE is_anomaly = TRUE
--     AND timestamp > NOW() - INTERVAL '24 hours'
-- GROUP BY device_id;

-- ============================================================================
-- Grants (adjust as needed)
-- ============================================================================
GRANT ALL PRIVILEGES ON TABLE ml_models TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE anomaly_detections TO iiot_user;

-- ============================================================================
-- Completion Message
-- ============================================================================
SELECT 'ML Database Schema Created Successfully!' as status;
SELECT 'Tables: ml_models, anomaly_detections' as tables_created;
SELECT 'Indexes: 7 indexes created' as indexes_created;
