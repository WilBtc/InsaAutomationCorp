#!/usr/bin/env python3
"""
ESP API Service for Alkhorayef IoT Platform
Provides REST API endpoints for ESP telemetry data and analytics
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import redis
import json
from datetime import datetime, timedelta
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for Grafana

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=5440,
        database="esp_telemetry",
        user="alkhorayef",
        password="AlkhorayefESP2025!"
    )

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6389,
    password='RedisAlkhorayef2025!',
    decode_responses=True
)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ESP API Service",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/pumps', methods=['GET'])
def get_pumps():
    """Get list of all ESP pumps"""
    pumps = [
        {"id": "ESP-001", "well": "WELL-A1", "field": "North Field"},
        {"id": "ESP-002", "well": "WELL-A2", "field": "North Field"},
        {"id": "ESP-003", "well": "WELL-B1", "field": "South Field"},
        {"id": "ESP-004", "well": "WELL-B2", "field": "South Field"},
        {"id": "ESP-005", "well": "WELL-C1", "field": "East Field"}
    ]

    # Add current status from Redis
    for pump in pumps:
        redis_key = f"esp:telemetry:{pump['id']}"
        latest = redis_client.hgetall(redis_key)
        if latest:
            pump["status"] = latest.get("pump_status", "unknown")
            pump["last_update"] = latest.get("timestamp", "")
            pump["flow_rate"] = float(latest.get("flow_rate", 0))
            pump["anomaly_score"] = float(latest.get("anomaly_score", 0))

    return jsonify(pumps)

@app.route('/api/telemetry/<pump_id>', methods=['GET'])
def get_telemetry(pump_id):
    """Get telemetry data for a specific pump"""
    hours = request.args.get('hours', 24, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT time, flow_rate, pip, motor_temp, motor_current,
               vibration, vsd_frequency, discharge_pressure,
               intake_temp, torque, power_consumption, anomaly_score
        FROM esp_telemetry
        WHERE pump_id = %s AND time > NOW() - INTERVAL '%s hours'
        ORDER BY time DESC
        LIMIT 1000
    """

    cursor.execute(query, (pump_id, hours))
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            "time": row[0].isoformat(),
            "flow_rate": row[1],
            "pip": row[2],
            "motor_temp": row[3],
            "motor_current": row[4],
            "vibration": row[5],
            "vsd_frequency": row[6],
            "discharge_pressure": row[7],
            "intake_temp": row[8],
            "torque": row[9],
            "power_consumption": row[10],
            "anomaly_score": row[11]
        })

    conn.close()
    return jsonify(data)

@app.route('/api/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    """Get latest telemetry for all pumps"""
    pumps = ["ESP-001", "ESP-002", "ESP-003", "ESP-004", "ESP-005"]
    data = []

    for pump_id in pumps:
        redis_key = f"esp:telemetry:{pump_id}"
        latest = redis_client.hgetall(redis_key)
        if latest:
            data.append(latest)

    return jsonify(data)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    hours = request.args.get('hours', 24, type=int)
    acknowledged = request.args.get('acknowledged', None)

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, timestamp, pump_id, alert_type, severity,
               message, parameters, acknowledged
        FROM esp_alerts
        WHERE timestamp > NOW() - INTERVAL '%s hours'
    """

    params = [hours]

    if acknowledged is not None:
        query += " AND acknowledged = %s"
        params.append(acknowledged == 'true')

    query += " ORDER BY timestamp DESC LIMIT 100"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    alerts = []
    for row in rows:
        alerts.append({
            "id": row[0],
            "timestamp": row[1].isoformat(),
            "pump_id": row[2],
            "alert_type": row[3],
            "severity": row[4],
            "message": row[5],
            "parameters": row[6],
            "acknowledged": row[7]
        })

    conn.close()
    return jsonify(alerts)

@app.route('/api/statistics/<pump_id>', methods=['GET'])
def get_statistics(pump_id):
    """Get statistical analysis for a pump"""
    hours = request.args.get('hours', 24, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            AVG(flow_rate) as avg_flow_rate,
            MIN(flow_rate) as min_flow_rate,
            MAX(flow_rate) as max_flow_rate,
            STDDEV(flow_rate) as stddev_flow_rate,
            AVG(pip) as avg_pip,
            AVG(motor_temp) as avg_motor_temp,
            MAX(motor_temp) as max_motor_temp,
            AVG(vibration) as avg_vibration,
            MAX(vibration) as max_vibration,
            AVG(power_consumption) as avg_power,
            SUM(power_consumption) / 1000 as total_power_mwh,
            AVG(anomaly_score) as avg_anomaly_score,
            MAX(anomaly_score) as max_anomaly_score,
            COUNT(*) as data_points
        FROM esp_telemetry
        WHERE pump_id = %s AND time > NOW() - INTERVAL '%s hours'
    """

    cursor.execute(query, (pump_id, hours))
    row = cursor.fetchone()

    if row:
        stats = {
            "pump_id": pump_id,
            "time_range_hours": hours,
            "flow_rate": {
                "avg": row[0],
                "min": row[1],
                "max": row[2],
                "stddev": row[3]
            },
            "pip": {"avg": row[4]},
            "motor_temp": {
                "avg": row[5],
                "max": row[6]
            },
            "vibration": {
                "avg": row[7],
                "max": row[8]
            },
            "power": {
                "avg_kw": row[9],
                "total_mwh": row[10]
            },
            "anomaly": {
                "avg_score": row[11],
                "max_score": row[12]
            },
            "data_points": row[13]
        }
    else:
        stats = {"error": "No data found"}

    conn.close()
    return jsonify(stats)

@app.route('/api/diagnostics/<pump_id>', methods=['GET'])
def get_diagnostics(pump_id):
    """Get diagnostic analysis for a pump"""
    # Get latest telemetry
    redis_key = f"esp:telemetry:{pump_id}"
    latest = redis_client.hgetall(redis_key)

    if not latest:
        return jsonify({"error": "No recent data available"}), 404

    # Diagnostic rules
    diagnosis = {
        "pump_id": pump_id,
        "timestamp": latest.get("timestamp"),
        "current_status": latest.get("pump_status"),
        "diagnosis": [],
        "recommendations": []
    }

    flow_rate = float(latest.get("flow_rate", 0))
    pip = float(latest.get("pip", 0))
    vibration = float(latest.get("vibration", 0))
    motor_temp = float(latest.get("motor_temp", 0))
    anomaly_score = float(latest.get("anomaly_score", 0))

    # Diagnostic logic
    if flow_rate < 800:
        if pip < 500:
            diagnosis["diagnosis"].append("UNDERPUMPING")
            diagnosis["recommendations"].append("Reduce VSD frequency by 5-10 Hz")
        else:
            diagnosis["diagnosis"].append("POSSIBLE HYDRAULIC WEAR")
            diagnosis["recommendations"].append("Plan pump inspection/replacement")

    if vibration > 3.0:
        if flow_rate < 1000 or flow_rate > 3000:
            diagnosis["diagnosis"].append("GAS LOCK SUSPECTED")
            diagnosis["recommendations"].append("Reduce frequency, apply backpressure")
        else:
            diagnosis["diagnosis"].append("HIGH VIBRATION")
            diagnosis["recommendations"].append("Check mechanical alignment")

    if motor_temp > 120:
        diagnosis["diagnosis"].append("HIGH MOTOR TEMPERATURE")
        diagnosis["recommendations"].append("Reduce load, check cooling system")

    if anomaly_score > 0.7:
        diagnosis["diagnosis"].append("ANOMALY DETECTED")
        diagnosis["recommendations"].append("Immediate inspection required")

    if not diagnosis["diagnosis"]:
        diagnosis["diagnosis"].append("NORMAL OPERATION")
        diagnosis["recommendations"].append("Continue monitoring")

    return jsonify(diagnosis)

# Grafana Simple JSON endpoints
@app.route('/', methods=['GET'])
def grafana_root():
    """Grafana Simple JSON root endpoint"""
    return jsonify({"message": "ESP API Service - Grafana Ready"})

@app.route('/search', methods=['POST'])
def grafana_search():
    """Grafana search endpoint"""
    metrics = [
        "flow_rate",
        "pip",
        "motor_temp",
        "motor_current",
        "vibration",
        "vsd_frequency",
        "discharge_pressure",
        "power_consumption",
        "anomaly_score"
    ]
    return jsonify(metrics)

@app.route('/query', methods=['POST'])
def grafana_query():
    """Grafana query endpoint"""
    req = request.get_json()

    data = []
    for target in req.get('targets', []):
        metric = target.get('target')
        pump_id = target.get('data', {}).get('pump_id', 'ESP-001')

        # Get time range
        time_from = datetime.fromisoformat(req['range']['from'].replace('Z', '+00:00'))
        time_to = datetime.fromisoformat(req['range']['to'].replace('Z', '+00:00'))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT time, {metric}
            FROM esp_telemetry
            WHERE pump_id = %s
            AND time BETWEEN %s AND %s
            ORDER BY time
        """

        cursor.execute(query, (pump_id, time_from, time_to))
        rows = cursor.fetchall()

        datapoints = []
        for row in rows:
            datapoints.append([row[1], int(row[0].timestamp() * 1000)])

        data.append({
            "target": f"{pump_id}_{metric}",
            "datapoints": datapoints
        })

        conn.close()

    return jsonify(data)

@app.route('/annotations', methods=['POST'])
def grafana_annotations():
    """Grafana annotations endpoint"""
    req = request.get_json()

    # Get time range
    time_from = datetime.fromisoformat(req['range']['from'].replace('Z', '+00:00'))
    time_to = datetime.fromisoformat(req['range']['to'].replace('Z', '+00:00'))

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT timestamp, pump_id, alert_type, message
        FROM esp_alerts
        WHERE timestamp BETWEEN %s AND %s
        ORDER BY timestamp
    """

    cursor.execute(query, (time_from, time_to))
    rows = cursor.fetchall()

    annotations = []
    for row in rows:
        annotations.append({
            "time": int(row[0].timestamp() * 1000),
            "title": f"{row[1]}: {row[2]}",
            "text": row[3],
            "tags": [row[1], row[2]]
        })

    conn.close()
    return jsonify(annotations)

if __name__ == '__main__':
    print("🚀 Starting ESP API Service on http://localhost:8096")
    print("📊 Grafana Simple JSON endpoints available")
    print("🔌 Connect Grafana to http://localhost:8096")
    app.run(host='0.0.0.0', port=8096, debug=False)