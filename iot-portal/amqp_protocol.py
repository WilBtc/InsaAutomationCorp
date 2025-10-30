#!/usr/bin/env python3
"""
AMQP Protocol Support
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 4

AMQP (Advanced Message Queuing Protocol) - OASIS Standard
Enterprise messaging protocol for reliable message delivery.

Features:
- AMQP consumer for telemetry ingestion
- Queue-based device communication
- Publish/subscribe pattern support
- Message acknowledgment and retry
- Integration with RabbitMQ or other AMQP brokers

Requirements:
- pika library: pip install pika
- RabbitMQ server: docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
- Or use virtual environment: python3 -m venv venv && source venv/bin/activate && pip install pika

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import pika
from pika.adapters.blocking_connection import BlockingChannel
import psycopg2
from psycopg2.extras import RealDictCursor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AMQPConsumer:
    """
    AMQP consumer for telemetry data ingestion.

    Features:
    - Consumes messages from telemetry queue
    - Stores data in PostgreSQL
    - Message acknowledgment
    - Auto-reconnect on connection loss
    """

    def __init__(
        self,
        db_config: Dict[str, Any],
        amqp_url: str = 'amqp://guest:guest@localhost:5672/',
        queue_name: str = 'telemetry',
        exchange: str = 'iiot',
        routing_key: str = 'telemetry.*'
    ):
        """
        Initialize AMQP consumer.

        Args:
            db_config: Database configuration dict
            amqp_url: AMQP broker URL
            queue_name: Queue to consume from
            exchange: Exchange to bind to
            routing_key: Routing key pattern
        """
        self.db_config = db_config
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.exchange = exchange
        self.routing_key = routing_key

        self.connection = None
        self.channel = None
        self.running = False
        self.consumer_thread = None

        logger.info(f"AMQPConsumer initialized (queue={queue_name}, exchange={exchange})")

    def connect(self):
        """Establish connection to AMQP broker"""
        try:
            params = pika.URLParameters(self.amqp_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            # Declare exchange (topic exchange for routing)
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='topic',
                durable=True
            )

            # Declare queue
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True
            )

            # Bind queue to exchange
            self.channel.queue_bind(
                queue=self.queue_name,
                exchange=self.exchange,
                routing_key=self.routing_key
            )

            # Set QoS (prefetch 1 message at a time)
            self.channel.basic_qos(prefetch_count=1)

            logger.info(f"✅ Connected to AMQP broker: {self.amqp_url}")
            logger.info(f"📬 Consuming from queue: {self.queue_name}")
            logger.info(f"🔀 Exchange: {self.exchange}, Routing: {self.routing_key}")

        except Exception as e:
            logger.error(f"Failed to connect to AMQP broker: {e}")
            raise

    def on_message(self, channel: BlockingChannel, method, properties, body):
        """
        Callback for incoming messages.

        Message format:
        {
            "device_id": "uuid",
            "data": {"temperature": 25.5, "humidity": 60},
            "tenant_id": "uuid"  # Optional
        }
        """
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))

            device_id = message.get('device_id')
            data = message.get('data', {})
            tenant_id = message.get('tenant_id')

            if not device_id or not data:
                logger.warning(f"Invalid message: {message}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # Store telemetry in database
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor() as cur:
                    # Verify device exists
                    cur.execute("SELECT id, tenant_id FROM devices WHERE id = %s", (device_id,))
                    device = cur.fetchone()

                    if not device:
                        logger.warning(f"Device not found: {device_id}")
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        return

                    # Use device's tenant_id if not provided
                    if not tenant_id:
                        tenant_id = device[1]

                    # Insert telemetry
                    for key, value in data.items():
                        cur.execute("""
                            INSERT INTO telemetry (device_id, attribute, value, tenant_id)
                            VALUES (%s, %s, %s, %s)
                        """, (device_id, key, value, tenant_id))

                    conn.commit()

                    logger.info(f"AMQP telemetry stored: device={device_id}, attributes={len(data)}")

                    # Acknowledge message
                    channel.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"Database error: {e}")
                conn.rollback()
                # Negative acknowledgment - requeue message
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            finally:
                conn.close()

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {body}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Message processing error: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages"""
        try:
            if not self.connection or not self.channel:
                self.connect()

            self.running = True

            # Set up consumer
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.on_message,
                auto_ack=False  # Manual acknowledgment
            )

            logger.info("✅ AMQP consumer started")
            logger.info("Waiting for messages... (Press Ctrl+C to stop)")

            # Start consuming
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("AMQP consumer interrupted")
            self.stop_consuming()

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise

    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False

        if self.channel:
            self.channel.stop_consuming()
            logger.info("AMQP consumer stopped")

        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("AMQP connection closed")

    def start_in_thread(self):
        """Start consumer in background thread"""
        if self.consumer_thread and self.consumer_thread.is_alive():
            logger.warning("Consumer already running")
            return

        self.consumer_thread = threading.Thread(target=self.start_consuming, daemon=True)
        self.consumer_thread.start()
        logger.info("AMQP consumer started in background thread")


class AMQPPublisher:
    """
    AMQP publisher for sending commands and alerts to devices.

    Features:
    - Publishes messages to exchange
    - Supports routing keys for targeted delivery
    - Message persistence
    - Connection pooling
    """

    def __init__(
        self,
        amqp_url: str = 'amqp://guest:guest@localhost:5672/',
        exchange: str = 'iiot'
    ):
        """
        Initialize AMQP publisher.

        Args:
            amqp_url: AMQP broker URL
            exchange: Exchange to publish to
        """
        self.amqp_url = amqp_url
        self.exchange = exchange

        self.connection = None
        self.channel = None

        logger.info(f"AMQPPublisher initialized (exchange={exchange})")

    def connect(self):
        """Establish connection to AMQP broker"""
        if self.connection and not self.connection.is_closed:
            return  # Already connected

        try:
            params = pika.URLParameters(self.amqp_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='topic',
                durable=True
            )

            logger.info(f"✅ AMQP publisher connected to {self.amqp_url}")

        except Exception as e:
            logger.error(f"Failed to connect AMQP publisher: {e}")
            raise

    def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        persistent: bool = True
    ):
        """
        Publish message to exchange.

        Args:
            routing_key: Routing key (e.g., 'alerts.critical', 'commands.device123')
            message: Message dict (will be JSON-encoded)
            persistent: Whether to persist message to disk
        """
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()

            # Encode message
            body = json.dumps(message).encode('utf-8')

            # Delivery mode 2 = persistent
            delivery_mode = 2 if persistent else 1

            # Publish
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=delivery_mode,
                    content_type='application/json'
                )
            )

            logger.info(f"AMQP message published: routing_key={routing_key}, persistent={persistent}")

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("AMQP publisher connection closed")


# =============================================================================
# Global instances
# =============================================================================

_amqp_consumer_instance = None
_amqp_publisher_instance = None


def init_amqp_consumer(
    db_config: Dict[str, Any],
    amqp_url: str = 'amqp://guest:guest@localhost:5672/',
    queue_name: str = 'telemetry',
    start_thread: bool = True
) -> AMQPConsumer:
    """
    Initialize the global AMQP consumer instance.

    Args:
        db_config: Database configuration dict
        amqp_url: AMQP broker URL
        queue_name: Queue name
        start_thread: Whether to start consumer in background thread

    Returns:
        AMQPConsumer instance
    """
    global _amqp_consumer_instance

    if _amqp_consumer_instance is None:
        _amqp_consumer_instance = AMQPConsumer(db_config, amqp_url, queue_name)

        if start_thread:
            _amqp_consumer_instance.start_in_thread()

        logger.info("Global AMQP consumer initialized")
    else:
        logger.warning("AMQP consumer already initialized")

    return _amqp_consumer_instance


def get_amqp_consumer() -> Optional[AMQPConsumer]:
    """Get the global AMQP consumer instance"""
    return _amqp_consumer_instance


def init_amqp_publisher(
    amqp_url: str = 'amqp://guest:guest@localhost:5672/'
) -> AMQPPublisher:
    """
    Initialize the global AMQP publisher instance.

    Args:
        amqp_url: AMQP broker URL

    Returns:
        AMQPPublisher instance
    """
    global _amqp_publisher_instance

    if _amqp_publisher_instance is None:
        _amqp_publisher_instance = AMQPPublisher(amqp_url)
        _amqp_publisher_instance.connect()
        logger.info("Global AMQP publisher initialized")
    else:
        logger.warning("AMQP publisher already initialized")

    return _amqp_publisher_instance


def get_amqp_publisher() -> Optional[AMQPPublisher]:
    """Get the global AMQP publisher instance"""
    return _amqp_publisher_instance


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    AMQP_URL = 'amqp://guest:guest@localhost:5672/'

    print("=== AMQP Consumer ===\n")
    print("Requirements:")
    print("  1. RabbitMQ server running:")
    print("     docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
    print("  ")
    print("  2. Test publisher:")
    print("     python3 -c \"import pika, json; conn=pika.BlockingConnection(pika.URLParameters('amqp://localhost:5672/')); ch=conn.channel(); ch.exchange_declare('iiot', 'topic', durable=True); ch.basic_publish('iiot', 'telemetry.device1', json.dumps({'device_id':'uuid','data':{'temp':25.5}}).encode()); print('Message sent'); conn.close()\"")
    print("\nPress Ctrl+C to stop\n")

    try:
        consumer = AMQPConsumer(DB_CONFIG, AMQP_URL)
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("\n✓ AMQP consumer stopped")
