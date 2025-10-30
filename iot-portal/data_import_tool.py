#!/usr/bin/env python3
"""
INSA IIoT Platform - Safe Data Import Tool
Imports client IoT data from various sources with validation and rollback capability
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import csv
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/data_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataImportTool:
    """Safe data import tool with validation and rollback"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.db_config = {
            'host': 'localhost',
            'database': 'insa_iiot',
            'user': 'iiot_user',
            'password': 'iiot_secure_2025',
            'cursor_factory': RealDictCursor
        }
        self.conn = None
        self.import_session_id = str(uuid.uuid4())
        self.stats = {
            'devices_imported': 0,
            'telemetry_imported': 0,
            'errors': 0,
            'skipped': 0
        }

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("✅ Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def get_or_create_tenant(self, tenant_name: str, tier: str = "professional") -> Optional[str]:
        """Get existing tenant or create new one"""
        try:
            cur = self.conn.cursor()

            # Check if tenant exists
            cur.execute("SELECT id FROM tenants WHERE name = %s", (tenant_name,))
            tenant = cur.fetchone()

            if tenant:
                logger.info(f"Using existing tenant: {tenant_name}")
                return str(tenant['id'])

            # Create new tenant
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create tenant: {tenant_name}")
                return str(uuid.uuid4())

            tenant_id = str(uuid.uuid4())
            slug = tenant_name.lower().replace(' ', '-').replace('_', '-')

            cur.execute("""
                INSERT INTO tenants (id, name, slug, tier, status, max_devices, max_users)
                VALUES (%s, %s, %s, %s, 'active', 500, 20)
                RETURNING id
            """, (tenant_id, tenant_name, slug, tier))

            self.conn.commit()
            logger.info(f"✅ Created new tenant: {tenant_name} ({tier})")
            return tenant_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Error with tenant: {e}")
            return None

    def validate_device_data(self, device: Dict) -> Tuple[bool, str]:
        """Validate device data before import"""
        required_fields = ['name', 'type']

        for field in required_fields:
            if field not in device or not device[field]:
                return False, f"Missing required field: {field}"

        # Validate device type
        valid_types = ['sensor', 'actuator', 'gateway', 'controller', 'temperature', 'pressure', 'flow', 'level']
        if device['type'] not in valid_types:
            return False, f"Invalid device type: {device['type']}"

        # Validate protocol if provided
        if 'protocol' in device:
            valid_protocols = ['mqtt', 'http', 'coap', 'amqp', 'opcua', 'modbus']
            if device['protocol'] and device['protocol'] not in valid_protocols:
                return False, f"Invalid protocol: {device['protocol']}"

        return True, "OK"

    def import_device(self, device: Dict, tenant_id: str) -> Optional[str]:
        """Import a single device"""
        try:
            # Validate device data
            valid, error_msg = self.validate_device_data(device)
            if not valid:
                logger.warning(f"⚠️ Skipping device: {error_msg}")
                self.stats['skipped'] += 1
                return None

            cur = self.conn.cursor()

            # Check if device already exists (by name and tenant)
            cur.execute("""
                SELECT id FROM devices
                WHERE name = %s AND tenant_id = %s
            """, (device['name'], tenant_id))

            existing = cur.fetchone()
            if existing:
                logger.info(f"Device already exists: {device['name']}")
                return str(existing['id'])

            if self.dry_run:
                logger.info(f"[DRY RUN] Would import device: {device['name']}")
                self.stats['devices_imported'] += 1
                return str(uuid.uuid4())

            # Import device
            device_id = str(uuid.uuid4())

            # Use area field if description was provided
            area = device.get('area', device.get('description', ''))

            cur.execute("""
                INSERT INTO devices (
                    id, tenant_id, name, type, location, area,
                    protocol, status, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                device_id,
                tenant_id,
                device['name'],
                device['type'],
                device.get('location', 'Unknown'),
                area,
                device.get('protocol', 'http'),
                device.get('status', 'offline'),
                json.dumps(device.get('metadata', {}))
            ))

            self.conn.commit()
            self.stats['devices_imported'] += 1
            logger.info(f"✅ Imported device: {device['name']} ({device_id})")
            return device_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Error importing device: {e}")
            self.stats['errors'] += 1
            return None

    def import_telemetry(self, telemetry: Dict, device_id: str, tenant_id: str) -> bool:
        """Import telemetry data for a device"""
        try:
            if self.dry_run:
                # Count all metrics in the data dict
                data = telemetry.get('data', {})
                self.stats['telemetry_imported'] += len(data)
                return True

            cur = self.conn.cursor()

            timestamp = telemetry.get('timestamp', datetime.utcnow().isoformat())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Get telemetry data - each key becomes a separate row
            data = telemetry.get('data', {})

            if not data:
                return True

            # Insert each metric as a separate row (key-value time-series model)
            for key, value in data.items():
                try:
                    # Convert value to float
                    float_value = float(value)

                    cur.execute("""
                        INSERT INTO telemetry (
                            device_id, tenant_id, timestamp, key, value, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        device_id,
                        tenant_id,
                        timestamp,
                        key,
                        float_value,
                        json.dumps({'import_session': self.import_session_id})
                    ))

                    self.stats['telemetry_imported'] += 1
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Skipping non-numeric telemetry: {key}={value}")
                    continue

            return True

        except Exception as e:
            logger.error(f"❌ Error importing telemetry: {e}")
            self.stats['errors'] += 1
            return False

    def import_from_json(self, json_file: str, tenant_name: str) -> bool:
        """Import data from JSON file"""
        try:
            logger.info(f"📂 Reading JSON file: {json_file}")

            with open(json_file, 'r') as f:
                data = json.load(f)

            tenant_id = self.get_or_create_tenant(tenant_name)
            if not tenant_id:
                return False

            # Handle different JSON structures
            devices = data.get('devices', []) if 'devices' in data else [data]

            logger.info(f"📊 Found {len(devices)} devices to import")

            for device_data in devices:
                device_id = self.import_device(device_data, tenant_id)

                if device_id and 'telemetry' in device_data:
                    telemetry_list = device_data['telemetry']
                    logger.info(f"   📈 Importing {len(telemetry_list)} telemetry points")

                    for telemetry in telemetry_list:
                        self.import_telemetry(telemetry, device_id, tenant_id)

            if not self.dry_run:
                self.conn.commit()

            logger.info(f"✅ JSON import completed")
            return True

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ JSON import failed: {e}")
            return False

    def import_from_csv(self, csv_file: str, tenant_name: str, data_type: str = 'devices') -> bool:
        """Import data from CSV file"""
        try:
            logger.info(f"📂 Reading CSV file: {csv_file}")

            tenant_id = self.get_or_create_tenant(tenant_name)
            if not tenant_id:
                return False

            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            logger.info(f"📊 Found {len(rows)} rows to import")

            if data_type == 'devices':
                for row in rows:
                    self.import_device(row, tenant_id)

            elif data_type == 'telemetry':
                # Expects: device_id, timestamp, key1, key2, ...
                for row in rows:
                    device_id = row.pop('device_id', None)
                    if not device_id:
                        continue

                    telemetry = {
                        'timestamp': row.pop('timestamp', datetime.utcnow().isoformat()),
                        'data': row  # Remaining columns become data
                    }
                    self.import_telemetry(telemetry, device_id, tenant_id)

            if not self.dry_run:
                self.conn.commit()

            logger.info(f"✅ CSV import completed")
            return True

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ CSV import failed: {e}")
            return False

    def import_sample_data(self, tenant_name: str, num_devices: int = 5) -> bool:
        """Generate and import sample IoT data for testing"""
        try:
            logger.info(f"🧪 Generating {num_devices} sample devices")

            tenant_id = self.get_or_create_tenant(tenant_name)
            if not tenant_id:
                return False

            device_types = ['temperature', 'pressure', 'flow', 'level', 'sensor']
            locations = ['Plant A', 'Plant B', 'Warehouse', 'Office', 'Laboratory']

            for i in range(num_devices):
                device = {
                    'name': f'Sample Device {i+1}',
                    'type': device_types[i % len(device_types)],
                    'location': locations[i % len(locations)],
                    'description': f'Sample device #{i+1} for testing',
                    'protocol': 'mqtt',
                    'status': 'online',
                    'metadata': {'sample': True, 'import_session': self.import_session_id}
                }

                device_id = self.import_device(device, tenant_id)

                if device_id:
                    # Add sample telemetry
                    for j in range(5):
                        telemetry = {
                            'timestamp': datetime.utcnow().isoformat(),
                            'data': {
                                'temperature': 20 + (i * 2) + j,
                                'pressure': 100 + (i * 5) + j,
                                'humidity': 50 + i + j
                            }
                        }
                        self.import_telemetry(telemetry, device_id, tenant_id)

            if not self.dry_run:
                self.conn.commit()

            logger.info(f"✅ Sample data generated successfully")
            return True

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ Sample data generation failed: {e}")
            return False

    def print_stats(self):
        """Print import statistics"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 IMPORT STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Session ID: {self.import_session_id}")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE IMPORT'}")
        logger.info(f"Devices Imported: {self.stats['devices_imported']}")
        logger.info(f"Telemetry Points Imported: {self.stats['telemetry_imported']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info("=" * 70)
        logger.info("")

def main():
    parser = argparse.ArgumentParser(description='INSA IIoT Data Import Tool')
    parser.add_argument('--tenant', required=True, help='Tenant name')
    parser.add_argument('--source', choices=['json', 'csv', 'sample'], required=True, help='Data source type')
    parser.add_argument('--file', help='Path to JSON/CSV file')
    parser.add_argument('--data-type', choices=['devices', 'telemetry'], default='devices', help='CSV data type')
    parser.add_argument('--num-devices', type=int, default=5, help='Number of sample devices to generate')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual changes)')
    parser.add_argument('--tier', choices=['starter', 'professional', 'enterprise'], default='professional', help='Tenant tier')

    args = parser.parse_args()

    # Validate arguments
    if args.source in ['json', 'csv'] and not args.file:
        parser.error(f"--file is required for --source {args.source}")

    # Initialize tool
    tool = DataImportTool(dry_run=args.dry_run)

    if not tool.connect():
        sys.exit(1)

    try:
        logger.info("")
        logger.info("=" * 70)
        logger.info("🚀 INSA IIoT PLATFORM - DATA IMPORT TOOL")
        logger.info("=" * 70)
        logger.info(f"Tenant: {args.tenant}")
        logger.info(f"Source: {args.source}")
        logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE IMPORT'}")
        logger.info("=" * 70)
        logger.info("")

        # Execute import
        success = False

        if args.source == 'json':
            success = tool.import_from_json(args.file, args.tenant)
        elif args.source == 'csv':
            success = tool.import_from_csv(args.file, args.tenant, args.data_type)
        elif args.source == 'sample':
            success = tool.import_sample_data(args.tenant, args.num_devices)

        # Print statistics
        tool.print_stats()

        if success:
            logger.info("✅ Import completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Import failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        tool.disconnect()

if __name__ == '__main__':
    main()
