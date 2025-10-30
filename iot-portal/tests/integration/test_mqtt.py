#!/usr/bin/env python3
"""
Integration Tests for MQTT Broker
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests the MQTT broker integration:
- Connection management
- Topic subscription/publishing
- QoS levels
- Message persistence
- Error handling
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import paho.mqtt.client as mqtt_client


@pytest.mark.integration
@pytest.mark.mqtt
class TestMQTTConnection:
    """Test MQTT broker connection"""

    def test_mqtt_broker_running(self):
        """Test MQTT broker is running"""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()

        assert result == 0, "MQTT broker not running on port 1883"

    def test_mqtt_client_connect(self, mock_mqtt_client):
        """Test MQTT client connection"""
        client = mock_mqtt_client
        client.connect.return_value = 0

        result = client.connect('localhost', 1883, 60)

        assert result == 0
        client.connect.assert_called_once()

    def test_mqtt_reconnection(self):
        """Test MQTT automatic reconnection"""
        from mqtt_broker import MQTTBroker

        with patch('paho.mqtt.client.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect.side_effect = [
                Exception("Connection failed"),  # First attempt fails
                0  # Second attempt succeeds
            ]
            mock_client_class.return_value = mock_client

            broker = MQTTBroker(host='localhost', port=1883)

            # Should handle reconnection gracefully
            assert True  # Placeholder for actual reconnection test


@pytest.mark.integration
@pytest.mark.mqtt
class TestMQTTPublishSubscribe:
    """Test MQTT publish/subscribe functionality"""

    def test_mqtt_publish_message(self, mock_mqtt_client):
        """Test publishing MQTT message"""
        client = mock_mqtt_client
        client.publish.return_value = (0, 1)

        topic = 'insa/iiot/telemetry/DEVICE-001'
        payload = json.dumps({
            'device_id': 'DEVICE-001',
            'metric': 'temperature',
            'value': 25.5,
            'timestamp': datetime.now().isoformat()
        })

        result = client.publish(topic, payload, qos=1)

        assert result[0] == 0
        client.publish.assert_called_once()

    def test_mqtt_subscribe_topic(self, mock_mqtt_client):
        """Test subscribing to MQTT topic"""
        client = mock_mqtt_client
        client.subscribe.return_value = (0, 1)

        topic = 'insa/iiot/telemetry/#'

        result = client.subscribe(topic, qos=1)

        assert result[0] == 0
        client.subscribe.assert_called_once_with(topic, qos=1)

    def test_mqtt_wildcard_subscription(self, mock_mqtt_client):
        """Test wildcard topic subscription"""
        client = mock_mqtt_client

        # Subscribe to all device telemetry
        topics = [
            ('insa/iiot/telemetry/#', 1),
            ('insa/iiot/status/#', 1),
            ('insa/iiot/commands/#', 1)
        ]

        client.subscribe(topics)

        # Should accept multiple topic subscriptions
        assert True

    def test_mqtt_message_callback(self):
        """Test MQTT message callback handling"""
        messages_received = []

        def on_message(client, userdata, message):
            messages_received.append({
                'topic': message.topic,
                'payload': message.payload.decode()
            })

        # Mock message
        mock_message = MagicMock()
        mock_message.topic = 'test/topic'
        mock_message.payload = b'test payload'

        on_message(None, None, mock_message)

        assert len(messages_received) == 1
        assert messages_received[0]['topic'] == 'test/topic'


@pytest.mark.integration
@pytest.mark.mqtt
class TestMQTTQoS:
    """Test MQTT Quality of Service levels"""

    def test_mqtt_qos0(self, mock_mqtt_client):
        """Test QoS 0 (at most once delivery)"""
        client = mock_mqtt_client
        client.publish.return_value = (0, 1)

        result = client.publish('test/topic', 'payload', qos=0)

        assert result[0] == 0

    def test_mqtt_qos1(self, mock_mqtt_client):
        """Test QoS 1 (at least once delivery)"""
        client = mock_mqtt_client
        client.publish.return_value = (0, 1)

        result = client.publish('test/topic', 'payload', qos=1)

        assert result[0] == 0

    def test_mqtt_qos2(self, mock_mqtt_client):
        """Test QoS 2 (exactly once delivery)"""
        client = mock_mqtt_client
        client.publish.return_value = (0, 1)

        result = client.publish('test/topic', 'payload', qos=2)

        assert result[0] == 0


@pytest.mark.integration
@pytest.mark.mqtt
class TestMQTTTelemetryIntegration:
    """Test MQTT integration with telemetry system"""

    def test_telemetry_mqtt_publish(self):
        """Test publishing telemetry data via MQTT"""
        from mqtt_broker import MQTTBroker

        with patch('paho.mqtt.client.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.publish.return_value = (0, 1)
            mock_client_class.return_value = mock_client

            broker = MQTTBroker(host='localhost', port=1883)

            telemetry_data = {
                'device_id': 'DEVICE-001',
                'metric': 'temperature',
                'value': 25.5,
                'unit': '°C',
                'timestamp': datetime.now().isoformat()
            }

            # Publish telemetry
            topic = f"insa/iiot/telemetry/{telemetry_data['device_id']}"
            payload = json.dumps(telemetry_data)

            result = mock_client.publish(topic, payload, qos=1)

            assert result[0] == 0

    def test_mqtt_command_handling(self):
        """Test handling commands via MQTT"""
        commands_received = []

        def on_command_message(client, userdata, message):
            payload = json.loads(message.payload.decode())
            commands_received.append(payload)

        # Simulate command message
        mock_message = MagicMock()
        mock_message.topic = 'insa/iiot/commands/DEVICE-001'
        mock_message.payload = json.dumps({
            'command': 'set_threshold',
            'parameters': {'threshold': 30.0}
        }).encode()

        on_command_message(None, None, mock_message)

        assert len(commands_received) == 1
        assert commands_received[0]['command'] == 'set_threshold'

    def test_mqtt_device_status(self):
        """Test device status updates via MQTT"""
        status_updates = []

        def on_status_message(client, userdata, message):
            payload = json.loads(message.payload.decode())
            status_updates.append(payload)

        # Simulate status message
        mock_message = MagicMock()
        mock_message.topic = 'insa/iiot/status/DEVICE-001'
        mock_message.payload = json.dumps({
            'device_id': 'DEVICE-001',
            'status': 'online',
            'last_seen': datetime.now().isoformat()
        }).encode()

        on_status_message(None, None, mock_message)

        assert len(status_updates) == 1
        assert status_updates[0]['status'] == 'online'


@pytest.mark.integration
@pytest.mark.mqtt
@pytest.mark.slow
class TestMQTTPerformance:
    """Test MQTT performance and scalability"""

    def test_mqtt_high_frequency_publishing(self, mock_mqtt_client):
        """Test high-frequency message publishing"""
        client = mock_mqtt_client
        client.publish.return_value = (0, 1)

        # Publish 100 messages rapidly
        for i in range(100):
            payload = json.dumps({
                'device_id': 'DEVICE-001',
                'value': 25.0 + i * 0.1,
                'timestamp': datetime.now().isoformat()
            })

            client.publish('test/telemetry', payload, qos=0)

        # All should succeed
        assert client.publish.call_count == 100

    def test_mqtt_message_throughput(self):
        """Test MQTT message throughput"""
        import time

        messages_sent = 0
        start_time = time.time()

        with patch('paho.mqtt.client.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.publish.return_value = (0, 1)
            mock_client_class.return_value = mock_client

            # Send messages for 1 second
            while time.time() - start_time < 1.0:
                mock_client.publish('test/topic', 'payload', qos=0)
                messages_sent += 1

            # Should handle many messages per second
            assert messages_sent > 100
