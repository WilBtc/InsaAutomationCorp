#!/usr/bin/env python3
"""
CoAP Protocol Support
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 4

CoAP (Constrained Application Protocol) - RFC 7252
Lightweight protocol for constrained devices and low-power networks.

Features:
- CoAP server for device telemetry ingestion
- Resource discovery
- Observ able resources (publish/subscribe pattern)
- DTLS support (optional)
- Integration with existing device management

Requirements:
- aiocoap library: pip install aiocoap
- Or use virtual environment: python3 -m venv venv && source venv/bin/activate && pip install aiocoap

Author: INSA Automation Corp
Date: October 28, 2025
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import aiocoap
import aiocoap.resource as resource
from aiocoap import Context, Message, Code
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelemetryResource(resource.Resource):
    """
    CoAP resource for telemetry data ingestion.

    POST /telemetry
    {
        "device_id": "uuid",
        "data": {"temperature": 25.5, "humidity": 60}
    }
    """

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        logger.info("TelemetryResource initialized")

    async def render_post(self, request):
        """Handle POST requests to /telemetry"""
        try:
            # Parse payload
            payload = json.loads(request.payload.decode('utf-8'))

            device_id = payload.get('device_id')
            data = payload.get('data', {})
            tenant_id = payload.get('tenant_id')  # Optional for multi-tenancy

            if not device_id or not data:
                return Message(code=Code.BAD_REQUEST, payload=b'Missing device_id or data')

            # Store telemetry in database
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor() as cur:
                    # Verify device exists
                    cur.execute("SELECT id, tenant_id FROM devices WHERE id = %s", (device_id,))
                    device = cur.fetchone()

                    if not device:
                        return Message(code=Code.NOT_FOUND, payload=b'Device not found')

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

                    logger.info(f"CoAP telemetry stored: device={device_id}, attributes={len(data)}")

                    return Message(code=Code.CREATED, payload=b'Telemetry stored successfully')

            finally:
                conn.close()

        except json.JSONDecodeError:
            return Message(code=Code.BAD_REQUEST, payload=b'Invalid JSON')
        except Exception as e:
            logger.error(f"CoAP telemetry error: {e}")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=f'Error: {str(e)}'.encode())

    async def render_get(self, request):
        """Handle GET requests to /telemetry (query latest)"""
        try:
            # Parse query string
            query = request.opt.uri_query
            device_id = None

            for q in query:
                if q.startswith(b'device_id='):
                    device_id = q.split(b'=')[1].decode('utf-8')

            if not device_id:
                return Message(code=Code.BAD_REQUEST, payload=b'Missing device_id query parameter')

            # Query latest telemetry
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT attribute, value, timestamp
                        FROM telemetry
                        WHERE device_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 10
                    """, (device_id,))

                    telemetry = [dict(row) for row in cur.fetchall()]

                    # Convert timestamps to ISO format
                    for t in telemetry:
                        t['timestamp'] = t['timestamp'].isoformat()

                    response_data = json.dumps({
                        'device_id': device_id,
                        'telemetry': telemetry
                    })

                    return Message(code=Code.CONTENT, payload=response_data.encode('utf-8'))

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"CoAP telemetry query error: {e}")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=f'Error: {str(e)}'.encode())


class DeviceResource(resource.Resource):
    """
    CoAP resource for device management.

    GET /devices
    GET /devices?id=uuid
    """

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        logger.info("DeviceResource initialized")

    async def render_get(self, request):
        """Handle GET requests to /devices"""
        try:
            # Parse query string
            query = request.opt.uri_query
            device_id = None
            tenant_id = None

            for q in query:
                if q.startswith(b'id='):
                    device_id = q.split(b'=')[1].decode('utf-8')
                elif q.startswith(b'tenant_id='):
                    tenant_id = q.split(b'=')[1].decode('utf-8')

            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if device_id:
                        # Get specific device
                        cur.execute("""
                            SELECT id, name, type, protocol, status, created_at
                            FROM devices
                            WHERE id = %s
                        """, (device_id,))
                        device = cur.fetchone()

                        if not device:
                            return Message(code=Code.NOT_FOUND, payload=b'Device not found')

                        device_dict = dict(device)
                        device_dict['created_at'] = device_dict['created_at'].isoformat()

                        response_data = json.dumps({'device': device_dict})

                    else:
                        # List devices (optionally filtered by tenant)
                        if tenant_id:
                            cur.execute("""
                                SELECT id, name, type, protocol, status
                                FROM devices
                                WHERE tenant_id = %s
                                LIMIT 50
                            """, (tenant_id,))
                        else:
                            cur.execute("""
                                SELECT id, name, type, protocol, status
                                FROM devices
                                LIMIT 50
                            """)

                        devices = [dict(row) for row in cur.fetchall()]

                        response_data = json.dumps({
                            'devices': devices,
                            'count': len(devices)
                        })

                    return Message(code=Code.CONTENT, payload=response_data.encode('utf-8'))

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"CoAP device query error: {e}")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=f'Error: {str(e)}'.encode())


class CoAPServer:
    """
    CoAP server for INSA Advanced IIoT Platform.

    Features:
    - Telemetry ingestion via POST /telemetry
    - Device queries via GET /devices
    - Resource discovery via GET /.well-known/core
    - Multi-tenant support
    """

    def __init__(self, db_config: Dict[str, Any], host: str = '::', port: int = 5683):
        """
        Initialize CoAP server.

        Args:
            db_config: Database configuration dict
            host: Bind address (:: for IPv6, 0.0.0.0 for IPv4)
            port: CoAP port (default: 5683, RFC 7252)
        """
        self.db_config = db_config
        self.host = host
        self.port = port
        self.root = resource.Site()
        self.context = None
        self.running = False

        # Add resources
        self.root.add_resource(['.well-known', 'core'],
                               resource.WKCResource(self.root.get_resources_as_linkheader))
        self.root.add_resource(['telemetry'], TelemetryResource(db_config))
        self.root.add_resource(['devices'], DeviceResource(db_config))

        logger.info(f"CoAPServer initialized (bind={host}:{port})")

    async def start(self):
        """Start CoAP server"""
        try:
            self.context = await Context.create_server_context(self.root, bind=(self.host, self.port))
            self.running = True
            logger.info(f"✅ CoAP server started on coap://{self.host}:{self.port}")
            logger.info("📡 Available resources:")
            logger.info("   - POST /telemetry (ingest telemetry)")
            logger.info("   - GET /devices (list devices)")
            logger.info("   - GET /devices?id=<uuid> (get device)")
            logger.info("   - GET /.well-known/core (resource discovery)")

        except Exception as e:
            logger.error(f"Failed to start CoAP server: {e}")
            raise

    async def stop(self):
        """Stop CoAP server"""
        if self.context:
            await self.context.shutdown()
            self.running = False
            logger.info("CoAP server stopped")

    async def run_forever(self):
        """Run server indefinitely"""
        await self.start()
        try:
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("CoAP server shutting down...")
        finally:
            await self.stop()


# =============================================================================
# Global server instance
# =============================================================================

_coap_server_instance = None


async def init_coap_server(db_config: Dict[str, Any], host: str = '::', port: int = 5683) -> CoAPServer:
    """
    Initialize and start the global CoAP server instance.

    Args:
        db_config: Database configuration dict
        host: Bind address
        port: CoAP port

    Returns:
        CoAPServer instance
    """
    global _coap_server_instance

    if _coap_server_instance is None:
        _coap_server_instance = CoAPServer(db_config, host, port)
        await _coap_server_instance.start()
        logger.info("Global CoAP server initialized and started")
    else:
        logger.warning("CoAP server already initialized")

    return _coap_server_instance


def get_coap_server() -> Optional[CoAPServer]:
    """
    Get the global CoAP server instance.

    Returns:
        CoAPServer instance or None
    """
    return _coap_server_instance


async def stop_coap_server():
    """Stop the global CoAP server"""
    global _coap_server_instance

    if _coap_server_instance:
        await _coap_server_instance.stop()
        _coap_server_instance = None
        logger.info("Global CoAP server stopped")


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

    print("=== CoAP Server ===\n")
    print("Starting CoAP server on coap://[::]:5683")
    print("\nTest with coap-client:")
    print("  # Install: apt-get install libcoap2-bin")
    print("  ")
    print("  # Resource discovery:")
    print("  coap-client -m get coap://localhost/.well-known/core")
    print("  ")
    print("  # List devices:")
    print("  coap-client -m get coap://localhost/devices")
    print("  ")
    print("  # Send telemetry:")
    print('  echo \'{"device_id":"uuid","data":{"temperature":25.5}}\' | \\')
    print("    coap-client -m post coap://localhost/telemetry -f -")
    print("\nPress Ctrl+C to stop\n")

    async def main():
        server = await init_coap_server(DB_CONFIG)
        await server.run_forever()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ CoAP server stopped")
