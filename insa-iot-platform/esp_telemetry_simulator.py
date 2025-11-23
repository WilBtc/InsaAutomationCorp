#!/usr/bin/env python3
"""
ESP Telemetry Simulator for Alkhorayef IoT Platform
Generates realistic ESP pump telemetry data with various operational scenarios
"""

import json
import time
import random
import psycopg2
import redis
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
import threading

class ESPTelemetrySimulator:
    def __init__(self):
        # Database connection
        self.db_conn = psycopg2.connect(
            host="localhost",
            port=5440,
            database="esp_telemetry",
            user="alkhorayef",
            password="AlkhorayefESP2025!"
        )

        # Redis connection for real-time data
        self.redis_client = redis.Redis(
            host='localhost',
            port=6389,
            password='RedisAlkhorayef2025!',
            decode_responses=True
        )

        # ESP pump configurations (simulating 5 pumps)
        self.pumps = [
            {"id": "ESP-001", "well": "WELL-A1", "field": "North Field", "status": "normal"},
            {"id": "ESP-002", "well": "WELL-A2", "field": "North Field", "status": "gas_lock"},
            {"id": "ESP-003", "well": "WELL-B1", "field": "South Field", "status": "sand_production"},
            {"id": "ESP-004", "well": "WELL-B2", "field": "South Field", "status": "hydraulic_wear"},
            {"id": "ESP-005", "well": "WELL-C1", "field": "East Field", "status": "underpumping"}
        ]

        # Normal operating ranges
        self.normal_ranges = {
            "flow_rate": (1500, 2500),      # BPD
            "pip": (800, 1200),              # PSI
            "motor_temp": (70, 100),         # Celsius
            "motor_current": (35, 55),       # Amps
            "vibration": (0.5, 1.5),         # g
            "vsd_frequency": (45, 55),       # Hz
            "discharge_pressure": (1800, 2200),  # PSI
            "intake_temp": (60, 80),        # Celsius
            "torque": (60, 80),              # Nm
            "power_consumption": (150, 250)  # kW
        }

    def init_database(self):
        """Initialize database tables if they don't exist"""
        cursor = self.db_conn.cursor()

        # Create telemetry table with TimescaleDB hypertable
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esp_telemetry (
                time TIMESTAMPTZ NOT NULL,
                pump_id TEXT NOT NULL,
                well_id TEXT NOT NULL,
                field TEXT NOT NULL,
                flow_rate DOUBLE PRECISION,
                pip DOUBLE PRECISION,
                motor_temp DOUBLE PRECISION,
                motor_current DOUBLE PRECISION,
                vibration DOUBLE PRECISION,
                vsd_frequency DOUBLE PRECISION,
                discharge_pressure DOUBLE PRECISION,
                intake_temp DOUBLE PRECISION,
                torque DOUBLE PRECISION,
                power_consumption DOUBLE PRECISION,
                pump_status TEXT,
                anomaly_score DOUBLE PRECISION,
                PRIMARY KEY (time, pump_id)
            );
        """)

        # Convert to hypertable if not already
        try:
            cursor.execute("""
                SELECT create_hypertable('esp_telemetry', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """)
        except:
            pass  # Table might already be a hypertable

        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esp_alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                pump_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                parameters JSONB,
                acknowledged BOOLEAN DEFAULT FALSE
            );
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_esp_telemetry_pump_time
            ON esp_telemetry (pump_id, time DESC);
        """)

        self.db_conn.commit()
        print("✅ Database tables initialized")

    def generate_telemetry(self, pump: Dict) -> Dict:
        """Generate telemetry data based on pump status"""
        timestamp = datetime.now()
        base_data = {
            "timestamp": timestamp.isoformat(),
            "pump_id": pump["id"],
            "well_id": pump["well"],
            "field": pump["field"],
            "pump_status": pump["status"]
        }

        if pump["status"] == "normal":
            data = self._generate_normal_data()
        elif pump["status"] == "gas_lock":
            data = self._generate_gas_lock_data()
        elif pump["status"] == "sand_production":
            data = self._generate_sand_production_data()
        elif pump["status"] == "hydraulic_wear":
            data = self._generate_hydraulic_wear_data()
        elif pump["status"] == "underpumping":
            data = self._generate_underpumping_data()
        else:
            data = self._generate_normal_data()

        # Add anomaly detection score
        data["anomaly_score"] = self._calculate_anomaly_score(data, pump["status"])

        return {**base_data, **data}

    def _generate_normal_data(self) -> Dict:
        """Generate normal operating conditions"""
        return {
            "flow_rate": random.uniform(1800, 2200),
            "pip": random.uniform(900, 1100),
            "motor_temp": random.uniform(75, 95),
            "motor_current": random.uniform(40, 50),
            "vibration": random.uniform(0.7, 1.3),
            "vsd_frequency": random.uniform(48, 52),
            "discharge_pressure": random.uniform(1900, 2100),
            "intake_temp": random.uniform(65, 75),
            "torque": random.uniform(65, 75),
            "power_consumption": random.uniform(180, 220)
        }

    def _generate_gas_lock_data(self) -> Dict:
        """Generate gas lock condition - choppy flow, erratic patterns"""
        base = self._generate_normal_data()
        # Choppy flow with high variance
        base["flow_rate"] = random.uniform(500, 2500) if random.random() > 0.3 else 0
        base["pip"] = random.uniform(400, 800)  # Low PIP
        base["vibration"] = random.uniform(2.5, 4.5)  # High vibration
        base["vsd_frequency"] = random.uniform(35, 45)  # Reduced frequency
        base["motor_current"] = random.uniform(25, 35)  # Lower current
        return base

    def _generate_sand_production_data(self) -> Dict:
        """Generate sand production condition - high flow, high torque"""
        base = self._generate_normal_data()
        base["flow_rate"] = random.uniform(2800, 3500)  # High flow
        base["torque"] = random.uniform(85, 110)  # High torque
        base["motor_current"] = random.uniform(60, 70)  # High current
        base["vibration"] = random.uniform(2.0, 3.0)  # Elevated vibration
        base["power_consumption"] = random.uniform(280, 350)  # High power
        return base

    def _generate_hydraulic_wear_data(self) -> Dict:
        """Generate hydraulic wear condition - low flow, stable but degraded"""
        base = self._generate_normal_data()
        base["flow_rate"] = random.uniform(800, 1200)  # Low flow
        base["pip"] = random.uniform(1000, 1100)  # Normal PIP
        base["discharge_pressure"] = random.uniform(1400, 1600)  # Low discharge
        base["motor_current"] = random.uniform(35, 45)  # Slightly low current
        return base

    def _generate_underpumping_data(self) -> Dict:
        """Generate underpumping condition - very low PIP"""
        base = self._generate_normal_data()
        base["pip"] = random.uniform(300, 500)  # Very low PIP
        base["flow_rate"] = random.uniform(2200, 2800)  # High flow initially
        base["motor_current"] = random.uniform(30, 40)  # Low current
        base["vsd_frequency"] = random.uniform(52, 58)  # High frequency
        return base

    def _calculate_anomaly_score(self, data: Dict, status: str) -> float:
        """Calculate anomaly score based on deviation from normal"""
        if status == "normal":
            return random.uniform(0.1, 0.3)
        elif status == "gas_lock":
            return random.uniform(0.7, 0.95)
        elif status == "sand_production":
            return random.uniform(0.6, 0.85)
        elif status == "hydraulic_wear":
            return random.uniform(0.5, 0.75)
        elif status == "underpumping":
            return random.uniform(0.6, 0.8)
        return 0.5

    def store_telemetry(self, data: Dict):
        """Store telemetry in database and Redis"""
        # Store in PostgreSQL
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO esp_telemetry (
                time, pump_id, well_id, field, flow_rate, pip,
                motor_temp, motor_current, vibration, vsd_frequency,
                discharge_pressure, intake_temp, torque, power_consumption,
                pump_status, anomaly_score
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            data["timestamp"], data["pump_id"], data["well_id"], data["field"],
            data["flow_rate"], data["pip"], data["motor_temp"], data["motor_current"],
            data["vibration"], data["vsd_frequency"], data["discharge_pressure"],
            data["intake_temp"], data["torque"], data["power_consumption"],
            data["pump_status"], data["anomaly_score"]
        ))
        self.db_conn.commit()

        # Store latest in Redis for real-time access
        redis_key = f"esp:telemetry:{data['pump_id']}"
        self.redis_client.hset(redis_key, mapping={
            k: str(v) for k, v in data.items()
        })
        self.redis_client.expire(redis_key, 3600)  # Expire after 1 hour

        # Publish to Redis channel for real-time subscribers
        self.redis_client.publish(f"esp:telemetry:stream", json.dumps(data))

    def check_and_create_alerts(self, data: Dict):
        """Check for alert conditions and create alerts"""
        alerts = []

        # Check for critical conditions
        if data["anomaly_score"] > 0.8:
            alerts.append({
                "pump_id": data["pump_id"],
                "alert_type": "CRITICAL_ANOMALY",
                "severity": "CRITICAL",
                "message": f"Critical anomaly detected on {data['pump_id']}",
                "parameters": {"anomaly_score": data["anomaly_score"]}
            })

        if data["flow_rate"] < 500:
            alerts.append({
                "pump_id": data["pump_id"],
                "alert_type": "LOW_FLOW",
                "severity": "HIGH",
                "message": f"Flow rate critically low on {data['pump_id']}: {data['flow_rate']:.1f} BPD",
                "parameters": {"flow_rate": data["flow_rate"]}
            })

        if data["motor_temp"] > 130:
            alerts.append({
                "pump_id": data["pump_id"],
                "alert_type": "HIGH_TEMPERATURE",
                "severity": "HIGH",
                "message": f"Motor temperature high on {data['pump_id']}: {data['motor_temp']:.1f}°C",
                "parameters": {"motor_temp": data["motor_temp"]}
            })

        # Store alerts
        cursor = self.db_conn.cursor()
        for alert in alerts:
            cursor.execute("""
                INSERT INTO esp_alerts (timestamp, pump_id, alert_type, severity, message, parameters)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(), alert["pump_id"], alert["alert_type"],
                alert["severity"], alert["message"], json.dumps(alert["parameters"])
            ))

            # Publish alert to Redis
            self.redis_client.publish("esp:alerts", json.dumps(alert))

        if alerts:
            self.db_conn.commit()
            print(f"⚠️  Generated {len(alerts)} alerts")

    def simulate_pump(self, pump: Dict):
        """Simulate a single pump continuously"""
        while True:
            try:
                # Generate telemetry
                telemetry = self.generate_telemetry(pump)

                # Store data
                self.store_telemetry(telemetry)

                # Check for alerts
                self.check_and_create_alerts(telemetry)

                # Random status changes (10% chance)
                if random.random() < 0.1:
                    statuses = ["normal", "gas_lock", "sand_production", "hydraulic_wear", "underpumping"]
                    pump["status"] = random.choice(statuses)
                    print(f"🔄 {pump['id']} status changed to: {pump['status']}")

                # Sleep for 5 seconds between readings
                time.sleep(5)

            except Exception as e:
                print(f"❌ Error simulating {pump['id']}: {e}")
                time.sleep(10)

    def run(self):
        """Run the simulator"""
        print("🚀 Starting ESP Telemetry Simulator")
        print(f"📊 Simulating {len(self.pumps)} ESP pumps")

        # Initialize database
        self.init_database()

        # Start a thread for each pump
        threads = []
        for pump in self.pumps:
            thread = threading.Thread(target=self.simulate_pump, args=(pump,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            print(f"✅ Started simulation for {pump['id']} ({pump['status']})")

        print("\n📡 Telemetry streaming started!")
        print("📊 Data is being written to TimescaleDB and Redis")
        print("⚡ Real-time data available on Redis channel: esp:telemetry:stream")
        print("\nPress Ctrl+C to stop...")

        try:
            # Keep main thread alive
            while True:
                time.sleep(60)
                # Print statistics every minute
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM esp_telemetry WHERE time > NOW() - INTERVAL '1 minute'")
                count = cursor.fetchone()[0]
                print(f"📈 Generated {count} telemetry records in the last minute")
        except KeyboardInterrupt:
            print("\n👋 Stopping simulator...")
            self.db_conn.close()
            print("✅ Simulator stopped")

if __name__ == "__main__":
    simulator = ESPTelemetrySimulator()
    simulator.run()