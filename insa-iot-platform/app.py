#!/usr/bin/env python3
"""
Alkhorayef ESP AI RAG System - Main Application Server
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import redis.asyncio as redis
import asyncpg
from contextlib import asynccontextmanager

# Import our diagnostic system
from run_alkhorayef_rag_system import (
    AlkhorayefESPDiagnosticSystem,
    ESPTelemetry,
    DiagnosisType,
    simulate_esp_telemetry
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alkhorayef:AlkhorayefESP2025!@localhost:5432/esp_telemetry")
REDIS_URL = os.getenv("REDIS_URL", "redis://:RedisAlkhorayef2025!@localhost:6379")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Global instances
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None
diagnostic_system = AlkhorayefESPDiagnosticSystem()

# Pydantic models
class TelemetryData(BaseModel):
    well_id: str
    timestamp: Optional[datetime] = None
    flow_rate: float
    pip: float
    motor_current: float
    motor_temp: float
    vibration: float
    vsd_frequency: float
    flow_variance: float
    torque: float
    gor: float

class DiagnosticRequest(BaseModel):
    well_id: str
    flow_stable: bool
    production_below_target: bool
    pip_low: bool
    flow_level: str
    telemetry: TelemetryData

class NaturalLanguageQuery(BaseModel):
    query: str
    well_id: Optional[str] = None
    include_history: bool = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global redis_client, db_pool

    # Startup
    print("🚀 Starting Alkhorayef ESP AI RAG System...")

    # Connect to Redis
    redis_client = await redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    # Connect to PostgreSQL
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=10, max_size=20)

    # Initialize database tables
    await init_database()

    print("✅ System initialized successfully")

    yield

    # Shutdown
    print("🔄 Shutting down...")
    if redis_client:
        await redis_client.close()
    if db_pool:
        await db_pool.close()
    print("👋 Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Alkhorayef ESP AI RAG System",
    description="Intelligent ESP Pump Diagnostics with Graphiti Knowledge Graph",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def init_database():
    """Initialize database tables"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS esp_telemetry (
                id SERIAL PRIMARY KEY,
                well_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                flow_rate FLOAT,
                pip FLOAT,
                motor_current FLOAT,
                motor_temp FLOAT,
                vibration FLOAT,
                vsd_frequency FLOAT,
                flow_variance FLOAT,
                torque FLOAT,
                gor FLOAT
            );

            CREATE INDEX IF NOT EXISTS idx_telemetry_well_time
            ON esp_telemetry(well_id, timestamp DESC);

            CREATE TABLE IF NOT EXISTS diagnostic_results (
                id SERIAL PRIMARY KEY,
                well_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                diagnosis VARCHAR(100),
                confidence FLOAT,
                severity VARCHAR(20),
                actions JSONB,
                telemetry_snapshot JSONB,
                resolution_time VARCHAR(50)
            );

            CREATE INDEX IF NOT EXISTS idx_diagnosis_well_time
            ON diagnostic_results(well_id, timestamp DESC);
        """)

@app.get("/")
async def root():
    """Root endpoint - serve platform HTML"""
    with open("alkhorayef_platform.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis
        await redis_client.ping()

        # Check PostgreSQL
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryData):
    """Ingest ESP telemetry data"""
    try:
        # Store in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO esp_telemetry (
                    well_id, timestamp, flow_rate, pip, motor_current,
                    motor_temp, vibration, vsd_frequency, flow_variance, torque, gor
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, data.well_id, data.timestamp or datetime.now(),
            data.flow_rate, data.pip, data.motor_current,
            data.motor_temp, data.vibration, data.vsd_frequency,
            data.flow_variance, data.torque, data.gor)

        # Cache latest reading in Redis
        cache_key = f"telemetry:{data.well_id}:latest"
        await redis_client.setex(
            cache_key,
            300,  # 5 minutes TTL
            data.json()
        )

        # Publish to real-time channel
        await redis_client.publish(f"telemetry:{data.well_id}", data.json())

        return {"status": "success", "well_id": data.well_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/diagnostics/decision_tree")
async def run_diagnostics(request: DiagnosticRequest):
    """Run diagnostic decision tree"""
    try:
        # Convert to ESP telemetry object
        telemetry = ESPTelemetry(
            timestamp=request.telemetry.timestamp or datetime.now(),
            flow_rate=request.telemetry.flow_rate,
            pip=request.telemetry.pip,
            motor_current=request.telemetry.motor_current,
            motor_temp=request.telemetry.motor_temp,
            vibration=request.telemetry.vibration,
            vsd_frequency=request.telemetry.vsd_frequency,
            flow_variance=request.telemetry.flow_variance,
            torque=request.telemetry.torque,
            gor=request.telemetry.gor
        )

        # Run diagnostic
        report = diagnostic_system.run_decision_tree(telemetry)

        # Store result in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO diagnostic_results (
                    well_id, diagnosis, confidence, severity,
                    actions, telemetry_snapshot, resolution_time
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, request.well_id,
            report['diagnosis']['type'],
            report['diagnosis']['confidence'],
            report['diagnosis']['severity'],
            json.dumps(report['recommended_actions']),
            json.dumps(report['telemetry_snapshot']),
            report['expected_resolution_time'])

        # Cache result
        cache_key = f"diagnosis:{request.well_id}:latest"
        await redis_client.setex(cache_key, 3600, json.dumps(report))

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/diagnostics/nlp_query")
async def natural_language_query(query: NaturalLanguageQuery):
    """Process natural language diagnostic query"""
    try:
        # Process query
        response = diagnostic_system.natural_language_query(query.query)

        # If well_id provided, get latest telemetry
        context = {}
        if query.well_id:
            cache_key = f"telemetry:{query.well_id}:latest"
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                context["latest_telemetry"] = json.loads(cached_data)

        # Get historical data if requested
        if query.include_history and query.well_id:
            async with db_pool.acquire() as conn:
                history = await conn.fetch("""
                    SELECT diagnosis, confidence, timestamp
                    FROM diagnostic_results
                    WHERE well_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, query.well_id)
                context["recent_diagnoses"] = [dict(r) for r in history]

        return {
            "query": query.query,
            "response": response,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/wells/{well_id}/telemetry")
async def get_telemetry_history(well_id: str, hours: int = 24):
    """Get telemetry history for a well"""
    try:
        async with db_pool.acquire() as conn:
            data = await conn.fetch("""
                SELECT * FROM esp_telemetry
                WHERE well_id = $1
                AND timestamp > NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
            """, well_id, hours)

        return {"well_id": well_id, "data": [dict(r) for r in data]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/wells/{well_id}/diagnostics")
async def get_diagnostic_history(well_id: str, limit: int = 10):
    """Get diagnostic history for a well"""
    try:
        async with db_pool.acquire() as conn:
            data = await conn.fetch("""
                SELECT * FROM diagnostic_results
                WHERE well_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, well_id, limit)

        return {"well_id": well_id, "diagnostics": [dict(r) for r in data]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/telemetry/{well_id}")
async def telemetry_websocket(websocket: WebSocket, well_id: str):
    """WebSocket for real-time telemetry"""
    await websocket.accept()

    # Subscribe to Redis channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"telemetry:{well_id}")

    try:
        while True:
            # Get message from Redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['data']:
                await websocket.send_text(message['data'])
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(f"telemetry:{well_id}")
        await websocket.close()

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        async with db_pool.acquire() as conn:
            metrics = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT well_id) as total_wells,
                    COUNT(*) as total_readings,
                    AVG(flow_rate) as avg_flow_rate
                FROM esp_telemetry
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)

            diagnoses = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_diagnoses,
                    AVG(confidence) as avg_confidence
                FROM diagnostic_results
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)

        return {
            "telemetry": dict(metrics),
            "diagnostics": dict(diagnoses),
            "system": {
                "total_diagnoses": diagnostic_system.decision_tree_stats["total_diagnoses"],
                "accuracy": diagnostic_system.decision_tree_stats["accuracy"],
                "avg_resolution_time": diagnostic_system.decision_tree_stats["avg_resolution_time"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info",
        access_log=True
    )