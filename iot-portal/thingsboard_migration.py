#!/usr/bin/env python3
"""
ThingsBoard to INSA IIoT Platform Migration Tool
Extracts devices and telemetry from ThingsBoard backup and imports to IIoT platform
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
import sys
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configurations
THINGSBOARD_DB = {
    'host': 'localhost',
    'port': 5432,
    'database': 'thingsboard_temp',  # Temporary database for restore
    'user': 'postgres',
    'password': None  # Will use peer authentication
}

IIOT_DB = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_iiot',
    'user': 'iiot_user',
    'password': 'iiot_secure_2025'
}

# Default tenant for imported data
DEFAULT_TENANT = "INSA Automation Corp"


class ThingsBoardMigration:
    """Migrates data from ThingsBoard to INSA IIoT Platform"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.tb_conn = None
        self.iiot_conn = None
        self.tenant_id = None
        self.stats = {
            'devices_migrated': 0,
            'telemetry_migrated': 0,
            'errors': 0,
            'skipped': 0
        }

    def connect_databases(self):
        """Connect to both databases"""
        try:
            # Connect to ThingsBoard temp database
            logger.info("Connecting to ThingsBoard database...")
            self.tb_conn = psycopg2.connect(
                host=THINGSBOARD_DB['host'],
                port=THINGSBOARD_DB['port'],
                database=THINGSBOARD_DB['database'],
                user=THINGSBOARD_DB['user']
            )

            # Connect to IIoT database
            logger.info("Connecting to IIoT platform database...")
            self.iiot_conn = psycopg2.connect(
                host=IIOT_DB['host'],
                port=IIOT_DB['port'],
                database=IIOT_DB['database'],
                user=IIOT_DB['user'],
                password=IIOT_DB['password']
            )

            logger.info("✅ Database connections established")
            return True

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def get_or_create_tenant(self):
        """Get or create the default tenant"""
        try:
            cur = self.iiot_conn.cursor(cursor_factory=RealDictCursor)

            # Check if tenant exists
            cur.execute("SELECT id FROM tenants WHERE name = %s", (DEFAULT_TENANT,))
            result = cur.fetchone()

            if result:
                self.tenant_id = result['id']
                logger.info(f"✅ Using existing tenant: {DEFAULT_TENANT} ({self.tenant_id})")
            else:
                # Create tenant
                self.tenant_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenants (id, name, tier, created_at)
                    VALUES (%s, %s, 'enterprise', NOW())
                    RETURNING id
                """, (self.tenant_id, DEFAULT_TENANT))
                self.iiot_conn.commit()
                logger.info(f"✅ Created tenant: {DEFAULT_TENANT} ({self.tenant_id})")

            return True

        except Exception as e:
            logger.error(f"❌ Tenant setup failed: {e}")
            return False

    def extract_devices(self):
        """Extract devices from ThingsBoard"""
        try:
            cur = self.tb_conn.cursor(cursor_factory=RealDictCursor)

            # Get devices from ThingsBoard
            cur.execute("""
                SELECT
                    id,
                    name,
                    type,
                    label,
                    created_time,
                    additional_info
                FROM device
                WHERE type IS NOT NULL
                ORDER BY created_time DESC
                LIMIT 100
            """)

            devices = cur.fetchall()
            logger.info(f"📊 Found {len(devices)} devices in ThingsBoard backup")

            return devices

        except Exception as e:
            logger.error(f"❌ Device extraction failed: {e}")
            return []

    def import_device(self, tb_device):
        """Import a single device to IIoT platform"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would import device: {tb_device['name']}")
                self.stats['devices_migrated'] += 1
                return str(tb_device['id'])

            cur = self.iiot_conn.cursor()

            # Parse additional_info JSON
            additional_info = {}
            if tb_device.get('additional_info'):
                try:
                    additional_info = json.loads(tb_device['additional_info'])
                except:
                    pass

            # Map ThingsBoard fields to IIoT platform
            device_id = str(tb_device['id'])
            name = tb_device.get('name', 'Unknown Device')
            device_type = tb_device.get('type', 'sensor')
            label = tb_device.get('label', '')
            location = additional_info.get('location', 'Unknown')

            # Check if device already exists
            cur.execute("SELECT id FROM devices WHERE id = %s", (device_id,))
            if cur.fetchone():
                logger.info(f"⏭️  Device already exists: {name}")
                self.stats['skipped'] += 1
                return device_id

            # Insert device
            cur.execute("""
                INSERT INTO devices (
                    id, tenant_id, name, type, location, area,
                    protocol, status, metadata, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                device_id,
                self.tenant_id,
                name,
                device_type,
                location,
                label or '',
                'mqtt',  # Default protocol
                'online',  # Assume online
                json.dumps(additional_info),
                tb_device.get('created_time', datetime.now())
            ))

            self.iiot_conn.commit()
            self.stats['devices_migrated'] += 1
            logger.info(f"✅ Imported device: {name} ({device_type})")

            return device_id

        except Exception as e:
            logger.error(f"❌ Device import failed: {e}")
            self.stats['errors'] += 1
            self.iiot_conn.rollback()
            return None

    def extract_telemetry(self, device_id, limit=1000):
        """Extract telemetry for a device from ThingsBoard"""
        try:
            cur = self.tb_conn.cursor(cursor_factory=RealDictCursor)

            # Get telemetry from ts_kv tables (try all months)
            tables = ['ts_kv', 'ts_kv_2025_10', 'ts_kv_2025_09', 'ts_kv_2025_08']
            all_telemetry = []

            for table in tables:
                try:
                    cur.execute(f"""
                        SELECT
                            ts,
                            key,
                            str_v,
                            long_v,
                            dbl_v,
                            bool_v
                        FROM {table}
                        WHERE entity_id = %s
                        ORDER BY ts DESC
                        LIMIT %s
                    """, (str(device_id), limit))

                    telemetry = cur.fetchall()
                    all_telemetry.extend(telemetry)

                except Exception as e:
                    # Table might not exist, continue
                    continue

            logger.info(f"📊 Found {len(all_telemetry)} telemetry points for device {device_id}")
            return all_telemetry

        except Exception as e:
            logger.error(f"❌ Telemetry extraction failed: {e}")
            return []

    def import_telemetry(self, device_id, tb_telemetry):
        """Import telemetry points to IIoT platform"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would import {len(tb_telemetry)} telemetry points")
                self.stats['telemetry_migrated'] += len(tb_telemetry)
                return

            cur = self.iiot_conn.cursor()
            imported = 0

            for point in tb_telemetry:
                try:
                    # Extract value (ThingsBoard stores different types in different columns)
                    value = None
                    if point['dbl_v'] is not None:
                        value = float(point['dbl_v'])
                    elif point['long_v'] is not None:
                        value = float(point['long_v'])
                    elif point['bool_v'] is not None:
                        value = 1.0 if point['bool_v'] else 0.0
                    else:
                        continue  # Skip string values

                    # Convert timestamp (ThingsBoard uses milliseconds)
                    timestamp = datetime.fromtimestamp(point['ts'] / 1000.0)

                    # Insert telemetry
                    cur.execute("""
                        INSERT INTO telemetry (
                            device_id, tenant_id, timestamp, key, value, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        device_id,
                        self.tenant_id,
                        timestamp,
                        point['key'],
                        value,
                        json.dumps({'migrated_from': 'thingsboard'})
                    ))

                    imported += 1

                except Exception as e:
                    logger.warning(f"⚠️  Telemetry point skipped: {e}")
                    continue

            self.iiot_conn.commit()
            self.stats['telemetry_migrated'] += imported
            logger.info(f"✅ Imported {imported} telemetry points")

        except Exception as e:
            logger.error(f"❌ Telemetry import failed: {e}")
            self.stats['errors'] += 1
            self.iiot_conn.rollback()

    def migrate(self):
        """Run full migration"""
        logger.info("=" * 60)
        logger.info("ThingsBoard to INSA IIoT Platform Migration")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No data will be modified")

        # Connect to databases
        if not self.connect_databases():
            return False

        # Setup tenant
        if not self.get_or_create_tenant():
            return False

        # Extract and import devices
        logger.info("\n📦 Extracting devices from ThingsBoard...")
        devices = self.extract_devices()

        if not devices:
            logger.warning("⚠️  No devices found in backup")
            return False

        logger.info(f"\n🔄 Importing {len(devices)} devices...")
        for tb_device in devices:
            device_id = self.import_device(tb_device)

            if device_id:
                # Extract and import telemetry for this device
                logger.info(f"\n📊 Extracting telemetry for device: {tb_device['name']}")
                telemetry = self.extract_telemetry(device_id, limit=1000)

                if telemetry:
                    self.import_telemetry(device_id, telemetry)

        # Print statistics
        logger.info("\n" + "=" * 60)
        logger.info("Migration Statistics")
        logger.info("=" * 60)
        logger.info(f"Devices migrated: {self.stats['devices_migrated']}")
        logger.info(f"Devices skipped: {self.stats['skipped']}")
        logger.info(f"Telemetry points migrated: {self.stats['telemetry_migrated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)

        return True

    def cleanup(self):
        """Close database connections"""
        if self.tb_conn:
            self.tb_conn.close()
        if self.iiot_conn:
            self.iiot_conn.close()
        logger.info("✅ Database connections closed")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate ThingsBoard data to INSA IIoT Platform')
    parser.add_argument('--dry-run', action='store_true', help='Test migration without modifying data')
    args = parser.parse_args()

    migration = ThingsBoardMigration(dry_run=args.dry_run)

    try:
        success = migration.migrate()
        sys.exit(0 if success else 1)
    finally:
        migration.cleanup()


if __name__ == '__main__':
    main()
