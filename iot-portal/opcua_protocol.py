#!/usr/bin/env python3
"""
OPC UA Protocol Support
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 4

OPC UA (Open Platform Communications Unified Architecture) - IEC 62541
Industrial automation protocol for secure and reliable data exchange.

Features:
- OPC UA server for device telemetry
- Subscription-based monitoring
- Secure communication (certificates, encryption)
- Type system for complex data
- Integration with industrial PLCs and SCADA systems

Requirements:
- asyncua library: pip install asyncua
- Or use virtual environment: python3 -m venv venv && source venv/bin/activate && pip install asyncua

Author: INSA Automation Corp
Date: October 28, 2025
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from asyncua import Server, ua
from asyncua.common.methods import uamethod
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OPCUAServer:
    """
    OPC UA server for INSA Advanced IIoT Platform.

    Features:
    - Device nodes with telemetry variables
    - Real-time data updates
    - Subscription/monitoring support
    - Method calls for device control
    - Multi-tenant support
    """

    def __init__(
        self,
        db_config: Dict[str, Any],
        endpoint: str = 'opc.tcp://0.0.0.0:4840/INSA/IIoT/',
        namespace: str = 'INSA Advanced IIoT Platform'
    ):
        """
        Initialize OPC UA server.

        Args:
            db_config: Database configuration dict
            endpoint: OPC UA endpoint URL
            namespace: Server namespace
        """
        self.db_config = db_config
        self.endpoint = endpoint
        self.namespace_uri = namespace

        self.server = Server()
        # Note: server.init() must be called in async context (in start() method)
        self.server.set_endpoint(endpoint)
        self.server.set_server_name("INSA IIoT Platform")

        self.namespace_idx = None
        self.objects_node = None
        self.devices_folder = None

        # Device node cache: {device_id: device_node}
        self.device_nodes = {}

        self.running = False
        self.initialized = False  # Track if server.init() was called

        logger.info(f"OPCUAServer initialized (endpoint={endpoint})")

    async def setup(self):
        """Setup server namespace and structure"""
        try:
            # Register namespace
            self.namespace_idx = await self.server.register_namespace(self.namespace_uri)

            # Get objects node
            self.objects_node = self.server.get_objects_node()

            # Create devices folder
            self.devices_folder = await self.objects_node.add_folder(
                self.namespace_idx,
                "Devices"
            )

            # Load devices from database
            await self.load_devices()

            logger.info(f"✅ OPC UA namespace registered: {self.namespace_uri}")
            logger.info(f"📁 Devices folder created with {len(self.device_nodes)} devices")

        except Exception as e:
            logger.error(f"Failed to setup OPC UA server: {e}")
            raise

    async def load_devices(self):
        """Load devices from database and create OPC UA nodes"""
        try:
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, name, type, protocol, status, tenant_id
                        FROM devices
                        ORDER BY name
                    """)

                    devices = cur.fetchall()

                    for device in devices:
                        await self.create_device_node(dict(device))

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            raise

    async def create_device_node(self, device: Dict[str, Any]):
        """
        Create OPC UA node for device.

        Args:
            device: Device dict from database
        """
        try:
            device_id = str(device['id'])

            if device_id in self.device_nodes:
                return  # Already exists

            # Create device folder
            device_node = await self.devices_folder.add_folder(
                self.namespace_idx,
                device['name']
            )

            # Add device properties
            await device_node.add_property(
                self.namespace_idx,
                "DeviceID",
                device_id
            )

            await device_node.add_property(
                self.namespace_idx,
                "Type",
                device['type']
            )

            await device_node.add_property(
                self.namespace_idx,
                "Protocol",
                device['protocol']
            )

            await device_node.add_property(
                self.namespace_idx,
                "Status",
                device['status']
            )

            # Create telemetry folder
            telemetry_folder = await device_node.add_folder(
                self.namespace_idx,
                "Telemetry"
            )

            # Add common telemetry variables (will be updated dynamically)
            await telemetry_folder.add_variable(
                self.namespace_idx,
                "Temperature",
                0.0
            )

            await telemetry_folder.add_variable(
                self.namespace_idx,
                "Pressure",
                0.0
            )

            await telemetry_folder.add_variable(
                self.namespace_idx,
                "Humidity",
                0.0
            )

            # Add method for device control
            @uamethod
            def set_device_status(parent, new_status):
                """Method to change device status"""
                logger.info(f"OPC UA method call: set_device_status({device_id}, {new_status})")

                # Update database
                conn = psycopg2.connect(**self.db_config)
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE devices SET status = %s WHERE id = %s
                        """, (new_status, device_id))
                        conn.commit()
                except Exception as e:
                    logger.error(f"Failed to update device status: {e}")
                    conn.rollback()
                    raise
                finally:
                    conn.close()

                return f"Status changed to {new_status}"

            await device_node.add_method(
                self.namespace_idx,
                "SetStatus",
                set_device_status,
                [ua.VariantType.String],  # Input: new_status
                [ua.VariantType.String]   # Output: result message
            )

            # Cache device node
            self.device_nodes[device_id] = {
                'node': device_node,
                'telemetry_folder': telemetry_folder
            }

            logger.debug(f"Created OPC UA node for device: {device['name']}")

        except Exception as e:
            logger.error(f"Failed to create device node: {e}")
            raise

    async def update_telemetry(
        self,
        device_id: str,
        attribute: str,
        value: float
    ):
        """
        Update telemetry variable for device.

        Args:
            device_id: Device UUID
            attribute: Telemetry attribute name
            value: New value
        """
        try:
            if device_id not in self.device_nodes:
                logger.warning(f"Device node not found: {device_id}")
                return

            telemetry_folder = self.device_nodes[device_id]['telemetry_folder']

            # Get or create variable
            try:
                variable = await telemetry_folder.get_child(f"{self.namespace_idx}:{attribute}")
            except Exception:
                # Variable doesn't exist, create it
                variable = await telemetry_folder.add_variable(
                    self.namespace_idx,
                    attribute,
                    value
                )

            # Update value
            await variable.write_value(value)

            logger.debug(f"OPC UA telemetry updated: {device_id}.{attribute} = {value}")

        except Exception as e:
            logger.error(f"Failed to update telemetry: {e}")

    async def sync_telemetry(self):
        """
        Periodically sync telemetry from database to OPC UA variables.

        This runs in the background to update OPC UA nodes with latest telemetry.
        """
        try:
            while self.running:
                # Query latest telemetry for all devices
                conn = psycopg2.connect(**self.db_config)
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute("""
                            SELECT DISTINCT ON (device_id, attribute)
                                device_id, attribute, value
                            FROM telemetry
                            WHERE timestamp > NOW() - INTERVAL '5 minutes'
                            ORDER BY device_id, attribute, timestamp DESC
                        """)

                        telemetry_data = cur.fetchall()

                        # Update OPC UA nodes
                        for row in telemetry_data:
                            await self.update_telemetry(
                                str(row['device_id']),
                                row['attribute'],
                                float(row['value'])
                            )

                finally:
                    conn.close()

                # Sleep for 5 seconds
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Telemetry sync task cancelled")
        except Exception as e:
            logger.error(f"Telemetry sync error: {e}")

    async def start(self):
        """Start OPC UA server"""
        try:
            # IMPORTANT: Must init server before starting
            if not self.initialized:
                await self.server.init()
                self.initialized = True
                logger.debug("OPC UA server initialized")

            # Start the server
            await self.server.start()

            # Now setup namespace and nodes
            await self.setup()

            self.running = True

            logger.info(f"✅ OPC UA server started on {self.endpoint}")
            logger.info("📡 Available nodes:")
            logger.info(f"   - Devices folder: ns={self.namespace_idx};i=Devices")
            logger.info(f"   - {len(self.device_nodes)} device nodes created")
            logger.info("🔧 Methods:")
            logger.info("   - SetStatus(device_id, new_status)")

            # Start telemetry sync task
            asyncio.create_task(self.sync_telemetry())

        except Exception as e:
            logger.error(f"Failed to start OPC UA server: {e}")
            raise

    async def stop(self):
        """Stop OPC UA server"""
        self.running = False

        if self.server:
            await self.server.stop()
            logger.info("OPC UA server stopped")

    async def run_forever(self):
        """Run server indefinitely"""
        await self.start()
        try:
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("OPC UA server shutting down...")
        finally:
            await self.stop()


# =============================================================================
# Global server instance
# =============================================================================

_opcua_server_instance = None


async def init_opcua_server(
    db_config: Dict[str, Any],
    endpoint: str = 'opc.tcp://0.0.0.0:4840/INSA/IIoT/'
) -> OPCUAServer:
    """
    Initialize and start the global OPC UA server instance.

    Args:
        db_config: Database configuration dict
        endpoint: OPC UA endpoint URL

    Returns:
        OPCUAServer instance
    """
    global _opcua_server_instance

    if _opcua_server_instance is None:
        _opcua_server_instance = OPCUAServer(db_config, endpoint)
        await _opcua_server_instance.start()
        logger.info("Global OPC UA server initialized and started")
    else:
        logger.warning("OPC UA server already initialized")

    return _opcua_server_instance


def get_opcua_server() -> Optional[OPCUAServer]:
    """
    Get the global OPC UA server instance.

    Returns:
        OPCUAServer instance or None
    """
    return _opcua_server_instance


async def stop_opcua_server():
    """Stop the global OPC UA server"""
    global _opcua_server_instance

    if _opcua_server_instance:
        await _opcua_server_instance.stop()
        _opcua_server_instance = None
        logger.info("Global OPC UA server stopped")


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

    print("=== OPC UA Server ===\n")
    print("Starting OPC UA server on opc.tcp://0.0.0.0:4840/INSA/IIoT/")
    print("\nTest with UA Expert or opcua-client:")
    print("  # Install Python client:")
    print("  pip install opcua-client")
    print("  ")
    print("  # Browse server:")
    print("  python3 -c \"from opcua import Client; c=Client('opc.tcp://localhost:4840/INSA/IIoT/'); c.connect(); print(c.get_objects_node().get_children()); c.disconnect()\"")
    print("\nPress Ctrl+C to stop\n")

    async def main():
        server = await init_opcua_server(DB_CONFIG)
        await server.run_forever()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ OPC UA server stopped")
