#!/usr/bin/env python3
"""
Alkhorayef ESP AI RAG System - ML Service
Handles machine learning predictions and anomaly detection
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import redis.asyncio as redis
import asyncpg
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alkhorayef:AlkhorayefESP2025!@localhost:5432/esp_telemetry")
REDIS_URL = os.getenv("REDIS_URL", "redis://:RedisAlkhorayef2025!@localhost:6379")
ML_SERVICE_PORT = int(os.getenv("ML_SERVICE_PORT", "8001"))
MODEL_PATH = os.getenv("ML_MODELS_PATH", "/app/models")

# Global instances
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None

class PredictionRequest(BaseModel):
    well_id: str
    horizon: int = 24  # hours
    features: Optional[Dict[str, float]] = None

class AnomalyRequest(BaseModel):
    well_id: str
    window: int = 1  # hours
    sensitivity: float = 0.1

class TrainingRequest(BaseModel):
    well_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    model_type: str = "isolation_forest"

# Create FastAPI app
app = FastAPI(
    title="Alkhorayef ESP ML Service",
    description="Machine Learning Service for ESP Pump Diagnostics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ESPAnomalyDetector:
    """Anomaly detection for ESP telemetry"""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, data: List[Dict]) -> np.ndarray:
        """Prepare features for anomaly detection"""
        features = []
        for record in data:
            features.append([
                record.get('flow_rate', 0),
                record.get('pip', 0),
                record.get('motor_current', 0),
                record.get('motor_temp', 0),
                record.get('vibration', 0),
                record.get('vsd_frequency', 0),
                record.get('flow_variance', 0),
                record.get('torque', 0)
            ])
        return np.array(features)

    def train(self, data: List[Dict]):
        """Train the anomaly detection model"""
        if len(data) < 100:
            raise ValueError("Need at least 100 samples for training")

        features = self.prepare_features(data)
        features_scaled = self.scaler.fit_transform(features)
        self.model.fit(features_scaled)
        self.is_trained = True

    def predict(self, data: List[Dict]) -> List[Dict]:
        """Predict anomalies"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)

        # Get predictions (-1 for anomaly, 1 for normal)
        predictions = self.model.predict(features_scaled)
        scores = self.model.score_samples(features_scaled)

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            results.append({
                "timestamp": data[i].get('timestamp'),
                "is_anomaly": pred == -1,
                "anomaly_score": float(-score),  # Convert to positive score
                "confidence": float(1 - np.exp(score))
            })

        return results

    def save(self, path: str):
        """Save model to disk"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)

    def load(self, path: str):
        """Load model from disk"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']

# Global anomaly detector
anomaly_detector = ESPAnomalyDetector()

@app.on_event("startup")
async def startup_event():
    """Initialize ML service"""
    global redis_client, db_pool

    print("🚀 Starting Alkhorayef ESP ML Service...")

    # Connect to Redis
    redis_client = await redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    # Connect to PostgreSQL
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=10)

    # Load pre-trained models if available
    model_file = os.path.join(MODEL_PATH, "anomaly_detector.pkl")
    if os.path.exists(model_file):
        anomaly_detector.load(model_file)
        print("✅ Loaded pre-trained anomaly detection model")
    else:
        print("⚠️  No pre-trained model found, training required")

    print("✅ ML Service initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    if redis_client:
        await redis_client.close()
    if db_pool:
        await db_pool.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ml-service",
        "timestamp": datetime.now().isoformat(),
        "model_trained": anomaly_detector.is_trained
    }

@app.post("/ml/anomaly/detect")
async def detect_anomalies(request: AnomalyRequest):
    """Detect anomalies in recent telemetry"""
    try:
        # Get recent telemetry data
        async with db_pool.acquire() as conn:
            data = await conn.fetch("""
                SELECT * FROM esp_telemetry
                WHERE well_id = $1
                AND timestamp > NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
            """, request.well_id, request.window)

        if not data:
            raise HTTPException(status_code=404, detail="No telemetry data found")

        # Convert to dict format
        telemetry = [dict(r) for r in data]

        # Check if model is trained
        if not anomaly_detector.is_trained:
            # Auto-train if we have enough historical data
            historical = await conn.fetch("""
                SELECT * FROM esp_telemetry
                WHERE well_id = $1
                ORDER BY timestamp DESC
                LIMIT 1000
            """, request.well_id)

            if len(historical) >= 100:
                anomaly_detector.train([dict(r) for r in historical])
                # Save the trained model
                os.makedirs(MODEL_PATH, exist_ok=True)
                anomaly_detector.save(os.path.join(MODEL_PATH, "anomaly_detector.pkl"))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Model not trained and insufficient data for auto-training"
                )

        # Detect anomalies
        results = anomaly_detector.predict(telemetry)

        # Filter by sensitivity
        anomalies = [r for r in results if r['confidence'] > request.sensitivity]

        # Cache results
        cache_key = f"anomalies:{request.well_id}:latest"
        await redis_client.setex(cache_key, 300, json.dumps(anomalies))

        return {
            "well_id": request.well_id,
            "window_hours": request.window,
            "total_readings": len(telemetry),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[:10],  # Return top 10
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/anomaly/train")
async def train_anomaly_model(request: TrainingRequest):
    """Train anomaly detection model"""
    try:
        # Build query
        query = "SELECT * FROM esp_telemetry WHERE well_id = $1"
        params = [request.well_id]

        if request.start_date:
            query += " AND timestamp >= $2"
            params.append(request.start_date)

        if request.end_date:
            query += f" AND timestamp <= ${len(params) + 1}"
            params.append(request.end_date)

        query += " ORDER BY timestamp DESC"

        # Get training data
        async with db_pool.acquire() as conn:
            data = await conn.fetch(query, *params)

        if len(data) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for training. Found {len(data)} samples, need at least 100"
            )

        # Train model
        training_data = [dict(r) for r in data]
        anomaly_detector.train(training_data)

        # Save model
        os.makedirs(MODEL_PATH, exist_ok=True)
        model_file = os.path.join(MODEL_PATH, f"anomaly_detector_{request.well_id}.pkl")
        anomaly_detector.save(model_file)

        return {
            "status": "success",
            "well_id": request.well_id,
            "samples_used": len(data),
            "model_type": request.model_type,
            "model_path": model_file,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/predict/failure")
async def predict_failure(request: PredictionRequest):
    """Predict potential pump failure"""
    try:
        # Get historical data
        async with db_pool.acquire() as conn:
            data = await conn.fetch("""
                SELECT * FROM esp_telemetry
                WHERE well_id = $1
                ORDER BY timestamp DESC
                LIMIT 168
            """, request.well_id)  # Last week of data

        if len(data) < 24:
            raise HTTPException(
                status_code=400,
                detail="Insufficient historical data for prediction"
            )

        # Simple failure prediction based on trends
        telemetry = [dict(r) for r in data]

        # Calculate trend indicators
        recent = telemetry[:24]  # Last 24 hours
        older = telemetry[24:48] if len(telemetry) > 48 else telemetry[24:]

        avg_vibration_recent = np.mean([r['vibration'] for r in recent if r['vibration']])
        avg_vibration_older = np.mean([r['vibration'] for r in older if r['vibration']])

        avg_temp_recent = np.mean([r['motor_temp'] for r in recent if r['motor_temp']])
        avg_temp_older = np.mean([r['motor_temp'] for r in older if r['motor_temp']])

        # Simple rule-based prediction
        risk_factors = []
        risk_score = 0

        if avg_vibration_recent > avg_vibration_older * 1.2:
            risk_factors.append("Increasing vibration trend")
            risk_score += 0.3

        if avg_temp_recent > avg_temp_older * 1.1:
            risk_factors.append("Rising motor temperature")
            risk_score += 0.3

        if avg_vibration_recent > 7:
            risk_factors.append("High vibration levels")
            risk_score += 0.2

        if avg_temp_recent > 80:
            risk_factors.append("High motor temperature")
            risk_score += 0.2

        # Determine failure probability
        failure_probability = min(risk_score, 1.0)

        # Estimate time to failure (simple linear extrapolation)
        if failure_probability > 0.5:
            hours_to_failure = int((1 - failure_probability) * 168)  # Max 1 week
        else:
            hours_to_failure = None

        return {
            "well_id": request.well_id,
            "failure_probability": float(failure_probability),
            "risk_level": "high" if failure_probability > 0.7 else "medium" if failure_probability > 0.4 else "low",
            "risk_factors": risk_factors,
            "estimated_hours_to_failure": hours_to_failure,
            "recommendation": "Schedule immediate maintenance" if failure_probability > 0.7
                           else "Monitor closely" if failure_probability > 0.4
                           else "Normal operation",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/models")
async def list_models():
    """List available ML models"""
    models = []

    if os.path.exists(MODEL_PATH):
        for file in os.listdir(MODEL_PATH):
            if file.endswith('.pkl'):
                file_path = os.path.join(MODEL_PATH, file)
                models.append({
                    "name": file.replace('.pkl', ''),
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })

    return {
        "models": models,
        "count": len(models),
        "model_path": MODEL_PATH
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ML_SERVICE_PORT,
        log_level="info"
    )