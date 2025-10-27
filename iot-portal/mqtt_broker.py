#!/usr/bin/env python3
"""
INSA Advanced IIoT Platform - MQTT Broker Integration
Handles MQTT publish/subscribe, device connectivity, and telemetry ingestion

Version: 2.0
Date: October 27, 2025
Author: INSA Automation Corp
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from threading import Thread
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class MQTTBroker:
    """MQTT Broker integration for IIoT platform"""

    def __init__(self, db_config, host='localhost', port=1883):
        self.db_config = db_config
        self.host = host
        self.port = port
        self.client = None
        self.connected = False
        self.telemetry_callbacks = []

        # MQTT topics
        self.topics = {
            'telemetry': 'insa/devices/+/telemetry',  # insa/devices/{device_id}/telemetry
            'status': 'insa/devices/+/status',         # insa/devices/{device_id}/status
            'commands': 'insa/devices/+/commands',     # insa/devices/{device_id}/commands
            'alerts': 'insa/alerts/#'                  # All alerts
        }

        logger.info(f"MQTT Broker initialized - {host}:{port}")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id=f"insa_platform_{datetime.now().timestamp()}")

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect

            # Connect
            self.client.connect(self.host, self.port, 60)

            # Start network loop in background
            self.client.loop_start()

            logger.info("MQTT client started successfully")
            return True

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker successfully")

            # Subscribe to all topics
            for topic_name, topic_path in self.topics.items():
                client.subscribe(topic_path)
                logger.info(f"Subscribed to topic: {topic_path}")
        else:
            logger.error(f"MQTT connection failed with code: {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Code: {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.info(f"Received MQTT message - Topic: {topic}, Size: {len(payload)} bytes")

            # Route message based on topic
            if '/telemetry' in topic:
                self._handle_telemetry(topic, payload)
            elif '/status' in topic:
                self._handle_status(topic, payload)
            elif '/commands' in topic:
                self._handle_command(topic, payload)
            elif '/alerts' in topic:
                self._handle_alert(topic, payload)

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_telemetry(self, topic, payload):
        """Handle telemetry data from devices"""
        try:
            # Extract device_id from topic: insa/devices/{device_id}/telemetry
            device_id = topic.split('/')[2]

            # Parse payload
            data = json.loads(payload)

            # Insert telemetry into database
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            timestamp = data.get('timestamp', datetime.now().isoformat())
            telemetry = data.get('telemetry', {})

            # Insert each telemetry point
            for key, value_data in telemetry.items():
                if isinstance(value_data, dict):
                    value = value_data.get('value')
                    unit = value_data.get('unit', '')
                    quality = value_data.get('quality', 100)
                else:
                    value = value_data
                    unit = ''
                    quality = 100

                cur.execute("""
                    INSERT INTO telemetry (timestamp, device_id, key, value, unit, quality)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (timestamp, device_id, key, value, unit, quality))

            # Update device last_seen
            cur.execute("""
                UPDATE devices
                SET last_seen = %s, status = 'online'
                WHERE id = %s
            """, (timestamp, device_id))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Telemetry stored for device {device_id}: {len(telemetry)} points")

            # Call registered callbacks
            for callback in self.telemetry_callbacks:
                callback(device_id, telemetry)

        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")

    def _handle_status(self, topic, payload):
        """Handle device status updates"""
        try:
            device_id = topic.split('/')[2]
            data = json.loads(payload)
            status = data.get('status', 'unknown')

            # Update device status in database
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            cur.execute("""
                UPDATE devices
                SET status = %s, last_seen = NOW()
                WHERE id = %s
            """, (status, device_id))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Status updated for device {device_id}: {status}")

        except Exception as e:
            logger.error(f"Error handling status: {e}")

    def _handle_command(self, topic, payload):
        """Handle commands sent to devices"""
        try:
            device_id = topic.split('/')[2]
            data = json.loads(payload)

            logger.info(f"Command received for device {device_id}: {data}")
            # Command handling logic here

        except Exception as e:
            logger.error(f"Error handling command: {e}")

    def _handle_alert(self, topic, payload):
        """Handle alert messages"""
        try:
            data = json.loads(payload)
            logger.info(f"Alert received: {data}")
            # Alert handling logic here

        except Exception as e:
            logger.error(f"Error handling alert: {e}")

    def publish(self, topic, payload, qos=1, retain=False):
        """Publish message to MQTT broker"""
        try:
            if not self.connected:
                logger.warning("Cannot publish - not connected to MQTT broker")
                return False

            if isinstance(payload, dict):
                payload = json.dumps(payload)

            result = self.client.publish(topic, payload, qos=qos, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: {len(str(payload))} bytes")
                return True
            else:
                logger.error(f"Publish failed with code: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    def register_telemetry_callback(self, callback):
        """Register callback for telemetry data"""
        self.telemetry_callbacks.append(callback)
        logger.info("Telemetry callback registered")

    def send_command_to_device(self, device_id, command, parameters=None):
        """Send command to specific device"""
        topic = f"insa/devices/{device_id}/commands"
        payload = {
            'command': command,
            'parameters': parameters or {},
            'timestamp': datetime.now().isoformat()
        }
        return self.publish(topic, payload)

    def publish_telemetry(self, device_id, telemetry_data):
        """Publish telemetry data on behalf of device (for testing)"""
        topic = f"insa/devices/{device_id}/telemetry"
        payload = {
            'timestamp': datetime.now().isoformat(),
            'telemetry': telemetry_data
        }
        return self.publish(topic, payload)

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")

    def get_connection_info(self):
        """Get MQTT connection information"""
        return {
            'host': self.host,
            'port': self.port,
            'connected': self.connected,
            'topics': self.topics
        }

# Global broker instance (initialized by app)
_broker_instance = None

def get_broker():
    """Get global MQTT broker instance"""
    return _broker_instance

def init_broker(db_config, host='localhost', port=1883):
    """Initialize global MQTT broker instance"""
    global _broker_instance
    _broker_instance = MQTTBroker(db_config, host, port)
    _broker_instance.connect()
    return _broker_instance
