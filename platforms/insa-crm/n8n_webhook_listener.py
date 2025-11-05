#!/usr/bin/env python3
"""
n8n Webhook Listener for Priority 1 Leads
Listens to PostgreSQL notifications and forwards them to n8n webhook
"""

import psycopg2
import psycopg2.extensions
import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/n8n_webhook_listener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_crm',
    'user': 'insa_crm_user',
    'password': '110811081108'
}

# n8n webhook URL
N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/lead-to-opportunity'

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def call_n8n_webhook(payload):
    """Forward notification to n8n webhook"""
    try:
        logger.info(f"📤 Sending to n8n webhook: {payload['lead_id']} - {payload['lead_name']}")
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"✅ n8n webhook successful: {payload['lead_id']}")
            return True
        else:
            logger.error(f"❌ n8n webhook failed: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to n8n - is n8n running on port 5678?")
        return False
    except Exception as e:
        logger.error(f"❌ Error calling n8n webhook: {e}")
        return False

def listen_for_notifications():
    """Listen for PostgreSQL notifications and forward to n8n"""
    conn = None
    cursor = None

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Listen on the priority1_lead channel
        cursor.execute("LISTEN priority1_lead;")
        logger.info("👂 Listening for Priority 1 lead notifications...")
        logger.info(f"📍 n8n webhook: {N8N_WEBHOOK_URL}")

        while True:
            # Wait for notifications (timeout every 30 seconds to check connection)
            if cursor.connection.poll() == psycopg2.extensions.POLL_OK:
                while conn.notifies:
                    notification = conn.notifies.pop(0)

                    try:
                        # Parse the JSON payload
                        payload = json.loads(notification.payload)
                        logger.info(f"🔔 Received notification for lead: {payload.get('lead_id', 'unknown')}")

                        # Forward to n8n webhook
                        call_n8n_webhook(payload)

                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in notification: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error processing notification: {e}")

            # Keep the connection alive
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down webhook listener...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("🛑 Webhook listener stopped")

if __name__ == '__main__':
    logger.info("🚀 Starting n8n Webhook Listener")
    logger.info(f"⏰ Started at: {datetime.now()}")

    # Retry connection on failure
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            listen_for_notifications()
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Connection failed (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                logger.info(f"⏳ Retrying in 10 seconds...")
                time.sleep(10)
            else:
                logger.error("❌ Max retries reached. Exiting.")
                exit(1)
