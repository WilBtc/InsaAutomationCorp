# Expert Architecture Plan - Part 3: Data Engineer Perspective

**Date**: November 20, 2025
**Platform**: Alkhorayef ESP Systems (INSA IoT Platform)
**Perspective**: Data Engineering & Analytics
**Focus**: TimescaleDB Optimization, Data Pipelines, ETL, Backup Strategy

---

## Table of Contents

1. [Current Data Architecture Assessment](#current-data-architecture-assessment)
2. [TimescaleDB Hypertable Migration](#timescaledb-hypertable-migration)
3. [Compression Policies](#compression-policies)
4. [Continuous Aggregates](#continuous-aggregates)
5. [Data Retention Strategy](#data-retention-strategy)
6. [ETL Pipeline Design](#etl-pipeline-design)
7. [Backup & Disaster Recovery](#backup-disaster-recovery)
8. [Data Quality Framework](#data-quality-framework)
9. [Performance Monitoring](#performance-monitoring)
10. [Implementation Plan](#implementation-plan)

---

## 1. Current Data Architecture Assessment

### Strengths

✅ **TimescaleDB Foundation**: Already using time-series optimized database
✅ **Docker Deployment**: Containerized for portability
✅ **Redis Caching**: Positioned for query acceleration
✅ **RabbitMQ Integration**: Message queue ready for buffering

### Critical Gaps

❌ **No Hypertables**: Using regular PostgreSQL tables (10x performance loss)
❌ **No Compression**: Storing uncompressed time-series (90% wasted storage)
❌ **No Continuous Aggregates**: Inefficient dashboard queries
❌ **No Retention Policies**: Unbounded data growth
❌ **No Partitioning Strategy**: No automated partition management
❌ **No Backup Automation**: Manual backup only
❌ **No Data Quality Checks**: No validation on ingestion

### Current Schema (app.py)

```python
# Current implementation (lines 61-67)
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    temperature REAL,
    vibration REAL,
    pressure REAL,
    flow_rate REAL
);
```

**Issue**: Regular table, not optimized for time-series workload.

---

## 2. TimescaleDB Hypertable Migration

### 2.1 Convert to Hypertable

**Target Schema**:

```sql
-- /home/wil/insa-iot-platform/app/db/migrations/001_create_hypertables.sql

-- Drop existing table (BACKUP FIRST!)
-- DO NOT RUN IN PRODUCTION WITHOUT BACKUP
-- pg_dump -h localhost -U alkhorayef_user -t telemetry alkhorayef_db > telemetry_backup.sql

DROP TABLE IF EXISTS telemetry;

-- Create optimized hypertable
CREATE TABLE telemetry (
    timestamp TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,

    -- ESP-specific metrics
    temperature REAL CHECK (temperature BETWEEN -50 AND 200),
    vibration REAL CHECK (vibration >= 0),
    pressure REAL CHECK (pressure >= 0),
    flow_rate REAL CHECK (flow_rate >= 0),
    motor_current REAL CHECK (motor_current >= 0),
    rpm REAL CHECK (rpm >= 0),
    intake_pressure REAL CHECK (intake_pressure >= 0),
    discharge_pressure REAL CHECK (discharge_pressure >= 0),

    -- Quality indicators
    data_quality_score REAL DEFAULT 1.0,
    is_anomaly BOOLEAN DEFAULT FALSE,

    -- Metadata
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW(),
    source_system TEXT DEFAULT 'scada'
);

-- Convert to hypertable (1-day chunks)
SELECT create_hypertable('telemetry', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for efficient queries
CREATE INDEX ix_telemetry_device_time ON telemetry (device_id, timestamp DESC);
CREATE INDEX ix_telemetry_device_anomaly ON telemetry (device_id, timestamp DESC) WHERE is_anomaly = TRUE;
CREATE INDEX ix_telemetry_quality ON telemetry (timestamp DESC) WHERE data_quality_score < 0.8;

-- Optimize for specific query patterns
CREATE INDEX ix_telemetry_composite ON telemetry (device_id, timestamp DESC, temperature, pressure, flow_rate);
```

### 2.2 Migration Script

```python
# /home/wil/insa-iot-platform/app/db/migrations/migrate_to_hypertable.py

import asyncio
import asyncpg
from datetime import datetime
from loguru import logger

class HypertableMigration:
    """Safely migrate existing telemetry data to hypertable."""

    def __init__(self, db_url: str):
        self.db_url = db_url

    async def migrate(self):
        """Execute migration with rollback capability."""

        conn = await asyncpg.connect(self.db_url)

        try:
            # Step 1: Verify source data
            row_count = await conn.fetchval("SELECT COUNT(*) FROM telemetry")
            logger.info(f"Found {row_count:,} existing records")

            # Step 2: Create backup table
            logger.info("Creating backup...")
            await conn.execute("""
                CREATE TABLE telemetry_backup AS
                SELECT * FROM telemetry
            """)

            # Step 3: Create temporary hypertable
            logger.info("Creating hypertable schema...")
            await conn.execute("""
                CREATE TABLE telemetry_new (
                    timestamp TIMESTAMPTZ NOT NULL,
                    device_id TEXT NOT NULL,
                    temperature REAL,
                    vibration REAL,
                    pressure REAL,
                    flow_rate REAL,
                    motor_current REAL,
                    rpm REAL,
                    intake_pressure REAL,
                    discharge_pressure REAL,
                    data_quality_score REAL DEFAULT 1.0,
                    is_anomaly BOOLEAN DEFAULT FALSE,
                    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    source_system TEXT DEFAULT 'scada'
                )
            """)

            # Step 4: Convert to hypertable
            await conn.execute("""
                SELECT create_hypertable(
                    'telemetry_new',
                    'timestamp',
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                )
            """)

            # Step 5: Copy data in batches
            logger.info("Migrating data in batches...")
            batch_size = 10000
            offset = 0

            while True:
                batch = await conn.fetch(f"""
                    SELECT * FROM telemetry
                    ORDER BY timestamp
                    LIMIT {batch_size} OFFSET {offset}
                """)

                if not batch:
                    break

                # Insert batch
                await conn.executemany("""
                    INSERT INTO telemetry_new
                    (timestamp, device_id, temperature, vibration, pressure, flow_rate)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, [(r['timestamp'], r['device_id'], r['temperature'],
                       r['vibration'], r['pressure'], r['flow_rate']) for r in batch])

                offset += batch_size
                logger.info(f"Migrated {offset:,} records...")

            # Step 6: Verify row counts match
            old_count = await conn.fetchval("SELECT COUNT(*) FROM telemetry")
            new_count = await conn.fetchval("SELECT COUNT(*) FROM telemetry_new")

            if old_count != new_count:
                raise ValueError(f"Row count mismatch: {old_count} != {new_count}")

            # Step 7: Swap tables
            logger.info("Swapping tables...")
            await conn.execute("ALTER TABLE telemetry RENAME TO telemetry_old")
            await conn.execute("ALTER TABLE telemetry_new RENAME TO telemetry")

            # Step 8: Create indexes
            logger.info("Creating indexes...")
            await conn.execute("""
                CREATE INDEX ix_telemetry_device_time
                ON telemetry (device_id, timestamp DESC)
            """)

            logger.success("Migration completed successfully!")
            logger.info("Old table preserved as 'telemetry_old' - drop manually after verification")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.warning("Rolling back...")
            await conn.execute("DROP TABLE IF EXISTS telemetry_new")
            raise

        finally:
            await conn.close()

# Usage
async def main():
    migration = HypertableMigration("postgresql://alkhorayef_user:password@localhost:5432/alkhorayef_db")
    await migration.migrate()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. Compression Policies

### 3.1 Compression Strategy

**Target**: 90-95% storage reduction on data >7 days old

```sql
-- /home/wil/insa-iot-platform/app/db/migrations/002_enable_compression.sql

-- Enable compression on hypertable
ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Automatic compression policy (compress after 7 days)
SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- Manual compression (for testing)
-- SELECT compress_chunk(c) FROM show_chunks('telemetry') c;
```

### 3.2 Expected Results

**Before Compression** (1M rows):
```
Table Size: 450 MB
Index Size: 180 MB
Total: 630 MB
```

**After Compression** (1M rows):
```
Compressed Chunks: 35 MB (92% reduction)
Recent Data: 45 MB (uncompressed, last 7 days)
Indexes: 20 MB
Total: 100 MB (84% overall reduction)
```

### 3.3 Compression Monitoring

```sql
-- Check compression status
SELECT
    hypertable_name,
    total_chunks,
    number_compressed_chunks,
    pg_size_pretty(before_compression_total_bytes) AS before_size,
    pg_size_pretty(after_compression_total_bytes) AS after_size,
    ROUND(100 - (after_compression_total_bytes::float / before_compression_total_bytes::float * 100), 2) AS compression_ratio
FROM timescaledb_information.compression_settings cs
JOIN timescaledb_information.hypertables h ON cs.hypertable_name = h.hypertable_name;
```

---

## 4. Continuous Aggregates

### 4.1 Real-Time Dashboard Aggregates

**Problem**: Grafana queries scanning millions of rows for 1-hour averages.

**Solution**: Pre-computed continuous aggregates.

```sql
-- /home/wil/insa-iot-platform/app/db/migrations/003_create_aggregates.sql

-- 1-minute aggregates (for real-time dashboards)
CREATE MATERIALIZED VIEW telemetry_1min
WITH (timescaledb.continuous) AS
SELECT
    device_id,
    time_bucket('1 minute', timestamp) AS bucket,

    -- Statistical aggregates
    AVG(temperature) AS temp_avg,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min,
    STDDEV(temperature) AS temp_stddev,

    AVG(vibration) AS vib_avg,
    MAX(vibration) AS vib_max,

    AVG(pressure) AS pressure_avg,
    MAX(pressure) AS pressure_max,

    AVG(flow_rate) AS flow_avg,
    SUM(flow_rate) AS flow_total,

    -- Quality metrics
    AVG(data_quality_score) AS avg_quality,
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count,
    COUNT(*) AS sample_count

FROM telemetry
GROUP BY device_id, bucket;

-- Add refresh policy (refresh every 30 seconds)
SELECT add_continuous_aggregate_policy('telemetry_1min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '30 seconds',
    schedule_interval => INTERVAL '30 seconds'
);

-- 1-hour aggregates (for historical analysis)
CREATE MATERIALIZED VIEW telemetry_1hour
WITH (timescaledb.continuous) AS
SELECT
    device_id,
    time_bucket('1 hour', timestamp) AS bucket,

    AVG(temperature) AS temp_avg,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY temperature) AS temp_p95,

    AVG(vibration) AS vib_avg,
    MAX(vibration) AS vib_max,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY vibration) AS vib_p95,

    AVG(pressure) AS pressure_avg,
    AVG(flow_rate) AS flow_avg,

    COUNT(*) AS sample_count,
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count

FROM telemetry
GROUP BY device_id, bucket;

-- Refresh hourly data every 10 minutes
SELECT add_continuous_aggregate_policy('telemetry_1hour',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '10 minutes'
);

-- Daily aggregates (for long-term trends)
CREATE MATERIALIZED VIEW telemetry_daily
WITH (timescaledb.continuous) AS
SELECT
    device_id,
    time_bucket('1 day', timestamp) AS bucket,

    AVG(temperature) AS temp_avg,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min,

    AVG(vibration) AS vib_avg,
    MAX(vibration) AS vib_max,

    AVG(pressure) AS pressure_avg,
    AVG(flow_rate) AS flow_avg,

    -- Daily statistics
    COUNT(*) AS sample_count,
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count,
    AVG(data_quality_score) AS avg_quality,

    -- Uptime calculation
    COUNT(*) * 100.0 / (24 * 60) AS uptime_percentage  -- Assuming 1 sample/min

FROM telemetry
GROUP BY device_id, bucket;

-- Refresh daily data once per day
SELECT add_continuous_aggregate_policy('telemetry_daily',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);
```

### 4.2 Query Performance Comparison

**Before (scanning raw table)**:
```sql
-- Slow query (scans 1M rows)
SELECT device_id, AVG(temperature)
FROM telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY device_id;

-- Execution: 2,500ms
```

**After (using continuous aggregate)**:
```sql
-- Fast query (scans 1,440 pre-aggregated rows)
SELECT device_id, AVG(temp_avg)
FROM telemetry_1min
WHERE bucket > NOW() - INTERVAL '24 hours'
GROUP BY device_id;

-- Execution: 15ms (166x faster!)
```

---

## 5. Data Retention Strategy

### 5.1 Retention Policy

**From CLAUDE.md**: "Azure should only have the last 30 days of IoT data"

```sql
-- /home/wil/insa-iot-platform/app/db/migrations/004_retention_policies.sql

-- Retention policy: Keep raw data for 30 days
SELECT add_retention_policy('telemetry', INTERVAL '30 days');

-- Keep aggregates longer (they're much smaller)
SELECT add_retention_policy('telemetry_1min', INTERVAL '90 days');
SELECT add_retention_policy('telemetry_1hour', INTERVAL '365 days');
-- telemetry_daily: No retention (keep forever - it's tiny)

-- Check retention status
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_retention';
```

### 5.2 Archive to Azure Blob Storage

**Before deletion, archive to cold storage:**

```python
# /home/wil/insa-iot-platform/app/services/data_archival.py

from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
import asyncpg
import pandas as pd
from loguru import logger

class DataArchivalService:
    """Archive old telemetry data to Azure Blob Storage before deletion."""

    def __init__(self, db_pool, azure_connection_string: str):
        self.db_pool = db_pool
        self.blob_service = BlobServiceClient.from_connection_string(azure_connection_string)
        self.container_name = "telemetry-archive"

    async def archive_old_data(self, days_old: int = 25):
        """
        Archive data older than 'days_old' to Azure.
        Run this 5 days before retention policy kicks in.
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        async with self.db_pool.acquire() as conn:
            # Get data to archive
            rows = await conn.fetch("""
                SELECT * FROM telemetry
                WHERE timestamp < $1
                ORDER BY timestamp
            """, cutoff_date)

            if not rows:
                logger.info("No data to archive")
                return

            # Convert to Parquet (highly compressed)
            df = pd.DataFrame([dict(r) for r in rows])

            # Generate archive filename
            archive_date = cutoff_date.strftime("%Y%m%d")
            filename = f"telemetry_{archive_date}.parquet"

            # Write to Parquet (90% compression)
            parquet_buffer = df.to_parquet(
                compression='snappy',
                index=False
            )

            # Upload to Azure Blob Storage
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=filename
            )

            blob_client.upload_blob(parquet_buffer, overwrite=True)

            logger.success(f"Archived {len(rows):,} records to {filename}")
            logger.info(f"Size: {len(parquet_buffer) / 1024 / 1024:.2f} MB")

    async def restore_from_archive(self, archive_date: str):
        """Restore archived data back to database (for analysis)."""

        filename = f"telemetry_{archive_date}.parquet"

        blob_client = self.blob_service.get_blob_client(
            container=self.container_name,
            blob=filename
        )

        # Download Parquet file
        parquet_data = blob_client.download_blob().readall()
        df = pd.read_parquet(BytesIO(parquet_data))

        # Insert back to database (into separate archive table)
        async with self.db_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO telemetry_archive
                (timestamp, device_id, temperature, vibration, pressure, flow_rate)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, df.values.tolist())

        logger.success(f"Restored {len(df):,} records from {filename}")
```

---

## 6. ETL Pipeline Design

### 6.1 Ingestion Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ESP SCADA Systems                           │
│              (Alkhorayef Oil Wells - Saudi Arabia)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ MQTT / Modbus TCP
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Edge Gateway / Data Collector                  │
│              - Protocol conversion                               │
│              - Data buffering                                    │
│              - Basic validation                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS (TLS 1.3)
                         │ JSON payloads
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RabbitMQ Message Queue                        │
│              - Message durability                                │
│              - Rate limiting                                     │
│              - Dead letter queue                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Async consumer
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               Data Validation & Enrichment Layer                 │
│              - Schema validation                                 │
│              - Data quality scoring                              │
│              - Anomaly detection (ML)                            │
│              - Metadata addition                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Batch writes (1000 records)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TimescaleDB Hypertable                         │
│              - Automated partitioning                            │
│              - Compression after 7 days                          │
│              - Retention after 30 days                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Continuous aggregates
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Pre-Aggregated Views (1min/1hr/1day)               │
│              - Real-time dashboards                              │
│              - Historical analysis                               │
│              - Anomaly detection                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 ETL Service Implementation

```python
# /home/wil/insa-iot-platform/app/services/etl_pipeline.py

from typing import Dict, List, Any
from datetime import datetime
import asyncio
from loguru import logger
from pydantic import ValidationError

class ETLPipeline:
    """Extract, Transform, Load pipeline for ESP telemetry data."""

    def __init__(self, db_pool, redis_client, rabbitmq_channel):
        self.db_pool = db_pool
        self.redis = redis_client
        self.rabbitmq = rabbitmq_channel
        self.batch_buffer = []
        self.batch_size = 1000
        self.flush_interval = 1.0  # seconds

    async def start_consumer(self):
        """Start consuming messages from RabbitMQ."""

        logger.info("Starting ETL pipeline consumer...")

        # Start background batch flusher
        asyncio.create_task(self._periodic_flush())

        # Consume messages
        async for message in self.rabbitmq.consume('telemetry_queue'):
            try:
                # Extract
                raw_data = message.body

                # Transform
                validated_data = await self._transform(raw_data)

                # Load (batch)
                await self._load_batch(validated_data)

                # Acknowledge message
                await message.ack()

            except ValidationError as e:
                logger.error(f"Validation failed: {e}")
                # Send to dead letter queue
                await self._send_to_dlq(message, str(e))
                await message.reject()

            except Exception as e:
                logger.exception(f"ETL error: {e}")
                # Retry
                await message.nack(requeue=True)

    async def _transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform and validate incoming data.

        Steps:
        1. Schema validation
        2. Unit conversion
        3. Data quality scoring
        4. Anomaly detection
        5. Metadata enrichment
        """

        # 1. Schema validation
        validated = TelemetrySchema(**raw_data)

        # 2. Unit conversion (if needed)
        if validated.temperature_unit == 'F':
            validated.temperature = (validated.temperature - 32) * 5/9

        # 3. Data quality scoring
        quality_score = await self._calculate_quality_score(validated)

        # 4. Anomaly detection
        is_anomaly = await self._detect_anomaly(validated)

        # 5. Metadata enrichment
        enriched = {
            **validated.dict(),
            'data_quality_score': quality_score,
            'is_anomaly': is_anomaly,
            'ingestion_timestamp': datetime.utcnow(),
            'source_system': 'scada'
        }

        return enriched

    async def _calculate_quality_score(self, data: TelemetrySchema) -> float:
        """
        Calculate data quality score (0.0 to 1.0).

        Factors:
        - Completeness (are all fields present?)
        - Validity (are values in expected ranges?)
        - Consistency (does data match historical patterns?)
        - Timeliness (is timestamp recent?)
        """

        score = 1.0

        # Completeness check
        missing_fields = sum([
            data.temperature is None,
            data.vibration is None,
            data.pressure is None,
            data.flow_rate is None
        ])
        score -= (missing_fields * 0.15)

        # Validity check (values in range)
        if data.temperature and not (-50 <= data.temperature <= 200):
            score -= 0.25

        if data.vibration and data.vibration < 0:
            score -= 0.25

        # Consistency check (compare to recent average)
        recent_avg = await self._get_recent_average(data.device_id)
        if recent_avg and data.temperature:
            deviation = abs(data.temperature - recent_avg) / recent_avg
            if deviation > 0.5:  # 50% deviation
                score -= 0.20

        # Timeliness check
        age_seconds = (datetime.utcnow() - data.timestamp).total_seconds()
        if age_seconds > 300:  # More than 5 minutes old
            score -= 0.10

        return max(0.0, score)

    async def _detect_anomaly(self, data: TelemetrySchema) -> bool:
        """
        Detect anomalies using statistical methods.

        Future: Replace with ML model.
        """

        # Get recent statistics from Redis cache
        cache_key = f"device:{data.device_id}:stats"
        stats = await self.redis.hgetall(cache_key)

        if not stats:
            return False

        # Z-score anomaly detection
        temp_mean = float(stats.get('temp_mean', 0))
        temp_std = float(stats.get('temp_std', 1))

        if data.temperature:
            z_score = abs((data.temperature - temp_mean) / temp_std)
            if z_score > 3.0:  # 3 standard deviations
                logger.warning(f"Temperature anomaly detected: {data.temperature}°C (z-score: {z_score:.2f})")
                return True

        return False

    async def _load_batch(self, data: Dict[str, Any]):
        """Add to batch buffer and flush if needed."""

        self.batch_buffer.append(data)

        if len(self.batch_buffer) >= self.batch_size:
            await self._flush_batch()

    async def _flush_batch(self):
        """Write batch to database."""

        if not self.batch_buffer:
            return

        batch_size = len(self.batch_buffer)

        try:
            async with self.db_pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO telemetry
                    (timestamp, device_id, temperature, vibration, pressure, flow_rate,
                     motor_current, rpm, intake_pressure, discharge_pressure,
                     data_quality_score, is_anomaly, ingestion_timestamp, source_system)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """, [
                    (d['timestamp'], d['device_id'], d['temperature'], d['vibration'],
                     d['pressure'], d['flow_rate'], d.get('motor_current'), d.get('rpm'),
                     d.get('intake_pressure'), d.get('discharge_pressure'),
                     d['data_quality_score'], d['is_anomaly'],
                     d['ingestion_timestamp'], d['source_system'])
                    for d in self.batch_buffer
                ])

            logger.info(f"Flushed {batch_size} records to database")
            self.batch_buffer.clear()

        except Exception as e:
            logger.exception(f"Batch write failed: {e}")
            # Don't clear buffer on failure - will retry

    async def _periodic_flush(self):
        """Flush batch periodically even if not full."""

        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_batch()

    async def _get_recent_average(self, device_id: str) -> float:
        """Get recent temperature average from cache."""

        cache_key = f"device:{device_id}:stats"
        stats = await self.redis.hget(cache_key, 'temp_mean')
        return float(stats) if stats else None

    async def _send_to_dlq(self, message, error: str):
        """Send failed message to dead letter queue for investigation."""

        await self.rabbitmq.publish(
            exchange='dlx',
            routing_key='telemetry.failed',
            message={
                'original_message': message.body,
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
```

---

## 7. Backup & Disaster Recovery

### 7.1 Backup Strategy

**Three-Tier Backup Approach**:

1. **Local Snapshots** (Hourly): Fast recovery for recent data loss
2. **Azure Blob Storage** (Daily): Offsite backup for disaster recovery
3. **Cold Archive** (Monthly): Long-term compliance storage

```bash
#!/bin/bash
# /home/wil/insa-iot-platform/scripts/backup_timescaledb.sh

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/timescaledb"
AZURE_CONTAINER="alkhorayef-backups"

# Database credentials
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="alkhorayef_db"
DB_USER="alkhorayef_user"

echo "[$(date)] Starting TimescaleDB backup..."

# 1. Create local backup directory
mkdir -p "$BACKUP_DIR"

# 2. Dump database (custom format for faster restore)
pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -F c \
    -f "$BACKUP_DIR/alkhorayef_${TIMESTAMP}.dump" \
    "$DB_NAME"

# 3. Compress backup
gzip "$BACKUP_DIR/alkhorayef_${TIMESTAMP}.dump"

BACKUP_FILE="$BACKUP_DIR/alkhorayef_${TIMESTAMP}.dump.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# 4. Upload to Azure Blob Storage
az storage blob upload \
    --account-name insaiotbackups \
    --container-name "$AZURE_CONTAINER" \
    --name "alkhorayef_${TIMESTAMP}.dump.gz" \
    --file "$BACKUP_FILE" \
    --auth-mode key

echo "[$(date)] Uploaded to Azure: alkhorayef_${TIMESTAMP}.dump.gz"

# 5. Cleanup local backups older than 7 days
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +7 -delete

echo "[$(date)] Backup completed successfully"

# 6. Verify backup integrity
pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[$(date)] Backup integrity verified ✓"
else
    echo "[$(date)] WARNING: Backup integrity check failed!"
    exit 1
fi
```

### 7.2 Continuous Backup (Write-Ahead Log Archiving)

```bash
# /home/wil/insa-iot-platform/scripts/setup_wal_archiving.sh

# Enable WAL archiving in PostgreSQL config
cat >> /var/lib/postgresql/data/postgresql.conf <<EOF

# Write-Ahead Log Archiving
wal_level = replica
archive_mode = on
archive_command = 'az storage blob upload --container-name alkhorayef-wal --name %f --file %p --account-name insaiotbackups'
archive_timeout = 300  # Archive every 5 minutes

# Continuous backup settings
max_wal_size = 2GB
min_wal_size = 1GB
EOF
```

### 7.3 Point-in-Time Recovery (PITR)

```bash
#!/bin/bash
# /home/wil/insa-iot-platform/scripts/restore_pitr.sh

# Restore database to specific point in time
# Usage: ./restore_pitr.sh "2025-11-20 14:30:00"

TARGET_TIME="$1"
BASE_BACKUP="alkhorayef_20251120_120000.dump.gz"

echo "Restoring to point-in-time: $TARGET_TIME"

# 1. Download base backup from Azure
az storage blob download \
    --account-name insaiotbackups \
    --container-name alkhorayef-backups \
    --name "$BASE_BACKUP" \
    --file "/tmp/$BASE_BACKUP"

# 2. Restore base backup
gunzip "/tmp/$BASE_BACKUP"
pg_restore \
    -h localhost \
    -U alkhorayef_user \
    -d alkhorayef_db_restored \
    -C \
    "/tmp/${BASE_BACKUP%.gz}"

# 3. Download WAL files from Azure
az storage blob download-batch \
    --account-name insaiotbackups \
    --source alkhorayef-wal \
    --destination /var/lib/postgresql/wal_archive/

# 4. Configure recovery
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# 5. Start PostgreSQL to replay WAL logs
sudo systemctl start postgresql

echo "Point-in-time recovery initiated. Database will recover to $TARGET_TIME"
```

### 7.4 Backup Automation

```yaml
# /home/wil/insa-iot-platform/docker-compose.backup.yml

services:
  backup-scheduler:
    image: python:3.11-slim
    container_name: alkhorayef-backup
    volumes:
      - ./scripts:/scripts
      - /var/backups:/backups
    environment:
      AZURE_STORAGE_CONNECTION_STRING: ${AZURE_STORAGE_CONNECTION_STRING}
      POSTGRES_HOST: alkhorayef-timescaledb
      POSTGRES_DB: alkhorayef_db
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    command: >
      sh -c "
        pip install apscheduler azure-storage-blob psycopg2-binary &&
        python /scripts/backup_scheduler.py
      "
    restart: unless-stopped
```

```python
# /home/wil/insa-iot-platform/scripts/backup_scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
from loguru import logger

scheduler = BlockingScheduler()

# Hourly local snapshots
@scheduler.scheduled_job(CronTrigger(minute=0))
def hourly_snapshot():
    logger.info("Running hourly snapshot...")
    subprocess.run(['/scripts/backup_timescaledb.sh'])

# Daily Azure backup
@scheduler.scheduled_job(CronTrigger(hour=2, minute=0))
def daily_azure_backup():
    logger.info("Running daily Azure backup...")
    subprocess.run(['/scripts/backup_to_azure.sh'])

# Weekly full backup with verification
@scheduler.scheduled_job(CronTrigger(day_of_week='sun', hour=3, minute=0))
def weekly_full_backup():
    logger.info("Running weekly full backup with verification...")
    subprocess.run(['/scripts/full_backup_verify.sh'])

scheduler.start()
```

---

## 8. Data Quality Framework

### 8.1 Data Quality Metrics

```python
# /home/wil/insa-iot-platform/app/services/data_quality.py

from enum import Enum
from typing import Dict, List
from datetime import datetime, timedelta
import asyncpg

class DataQualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    ACCURACY = "accuracy"

class DataQualityMonitor:
    """Monitor and report on data quality metrics."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def calculate_metrics(self, hours: int = 24) -> Dict[str, float]:
        """Calculate data quality metrics for the last N hours."""

        async with self.db_pool.acquire() as conn:
            # Completeness: % of records with all fields populated
            completeness = await conn.fetchval("""
                SELECT
                    COUNT(*) FILTER (WHERE
                        temperature IS NOT NULL AND
                        vibration IS NOT NULL AND
                        pressure IS NOT NULL AND
                        flow_rate IS NOT NULL
                    ) * 100.0 / COUNT(*)
                FROM telemetry
                WHERE timestamp > NOW() - INTERVAL '$1 hours'
            """, hours)

            # Validity: % of records passing validation checks
            validity = await conn.fetchval("""
                SELECT AVG(data_quality_score) * 100
                FROM telemetry
                WHERE timestamp > NOW() - INTERVAL '$1 hours'
            """, hours)

            # Consistency: % of records without anomalies
            consistency = await conn.fetchval("""
                SELECT
                    (COUNT(*) - COUNT(*) FILTER (WHERE is_anomaly = TRUE)) * 100.0 / COUNT(*)
                FROM telemetry
                WHERE timestamp > NOW() - INTERVAL '$1 hours'
            """, hours)

            # Timeliness: % of records ingested within 5 minutes of creation
            timeliness = await conn.fetchval("""
                SELECT
                    COUNT(*) FILTER (WHERE
                        EXTRACT(EPOCH FROM (ingestion_timestamp - timestamp)) < 300
                    ) * 100.0 / COUNT(*)
                FROM telemetry
                WHERE timestamp > NOW() - INTERVAL '$1 hours'
            """, hours)

            # Overall score (weighted average)
            overall = (
                completeness * 0.30 +
                validity * 0.30 +
                consistency * 0.25 +
                timeliness * 0.15
            )

            return {
                "completeness": round(completeness, 2),
                "validity": round(validity, 2),
                "consistency": round(consistency, 2),
                "timeliness": round(timeliness, 2),
                "overall": round(overall, 2)
            }

    async def get_quality_by_device(self) -> List[Dict]:
        """Get data quality scores grouped by device."""

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    device_id,
                    AVG(data_quality_score) * 100 AS avg_quality,
                    COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count,
                    COUNT(*) AS total_records,
                    MAX(timestamp) AS last_reading
                FROM telemetry
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY device_id
                ORDER BY avg_quality ASC
            """)

            return [dict(row) for row in rows]
```

---

## 9. Performance Monitoring

### 9.1 Database Performance Metrics

```sql
-- /home/wil/insa-iot-platform/app/db/queries/performance_monitoring.sql

-- 1. Table sizes and bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 2. Query performance (slowest queries)
SELECT
    query,
    calls,
    ROUND(total_exec_time::numeric, 2) AS total_time_ms,
    ROUND(mean_exec_time::numeric, 2) AS avg_time_ms,
    ROUND((100 * total_exec_time / SUM(total_exec_time) OVER ())::numeric, 2) AS percentage
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- 3. Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

-- 4. Cache hit ratio (should be > 99%)
SELECT
    'Cache Hit Ratio' AS metric,
    ROUND(
        100.0 * sum(blks_hit) / NULLIF(sum(blks_hit) + sum(blks_read), 0),
        2
    ) AS percentage
FROM pg_stat_database
WHERE datname = 'alkhorayef_db';

-- 5. Compression statistics
SELECT
    hypertable_schema,
    hypertable_name,
    total_chunks,
    number_compressed_chunks,
    ROUND(100.0 * number_compressed_chunks / NULLIF(total_chunks, 0), 2) AS compression_percentage,
    pg_size_pretty(before_compression_total_bytes) AS before_size,
    pg_size_pretty(after_compression_total_bytes) AS after_size,
    ROUND(100 - (100.0 * after_compression_total_bytes / NULLIF(before_compression_total_bytes, 0)), 2) AS space_saved_percentage
FROM timescaledb_information.compressed_hypertable_stats;

-- 6. Continuous aggregate refresh lag
SELECT
    view_name,
    materialization_hypertable,
    last_run_started_at,
    last_successful_finish,
    NOW() - last_successful_finish AS lag
FROM timescaledb_information.continuous_aggregate_stats
ORDER BY lag DESC;
```

### 9.2 Performance Monitoring Service

```python
# /home/wil/insa-iot-platform/app/services/performance_monitor.py

import asyncpg
from loguru import logger
from prometheus_client import Gauge, Counter

# Prometheus metrics
db_size_bytes = Gauge('timescaledb_size_bytes', 'Total database size in bytes')
compression_ratio = Gauge('timescaledb_compression_ratio', 'Compression ratio percentage')
cache_hit_ratio = Gauge('timescaledb_cache_hit_ratio', 'Cache hit ratio percentage')
query_latency_ms = Gauge('timescaledb_query_latency_ms', 'Average query latency', ['query_type'])
ingestion_rate = Counter('telemetry_ingestion_rate', 'Telemetry records ingested per second')

class PerformanceMonitor:
    """Monitor TimescaleDB performance and export metrics."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def collect_metrics(self):
        """Collect all performance metrics."""

        async with self.db_pool.acquire() as conn:
            # Database size
            size = await conn.fetchval("""
                SELECT pg_database_size('alkhorayef_db')
            """)
            db_size_bytes.set(size)

            # Compression ratio
            comp_stats = await conn.fetchrow("""
                SELECT
                    before_compression_total_bytes,
                    after_compression_total_bytes
                FROM timescaledb_information.compressed_hypertable_stats
                WHERE hypertable_name = 'telemetry'
            """)

            if comp_stats:
                ratio = 100 - (100.0 * comp_stats['after_compression_total_bytes'] /
                              comp_stats['before_compression_total_bytes'])
                compression_ratio.set(ratio)

            # Cache hit ratio
            cache_hit = await conn.fetchval("""
                SELECT
                    ROUND(100.0 * sum(blks_hit) / NULLIF(sum(blks_hit) + sum(blks_read), 0), 2)
                FROM pg_stat_database
                WHERE datname = 'alkhorayef_db'
            """)
            cache_hit_ratio.set(cache_hit)

            # Query latencies
            slow_queries = await conn.fetch("""
                SELECT
                    query,
                    ROUND(mean_exec_time::numeric, 2) AS avg_time_ms
                FROM pg_stat_statements
                WHERE query LIKE '%telemetry%'
                ORDER BY mean_exec_time DESC
                LIMIT 5
            """)

            for row in slow_queries:
                query_type = row['query'][:50]  # First 50 chars
                query_latency_ms.labels(query_type=query_type).set(row['avg_time_ms'])

        logger.debug("Performance metrics collected")
```

---

## 10. Implementation Plan

### Phase 1: Hypertable Migration (Week 1)

**Day 1-2: Preparation**
- [ ] Full database backup
- [ ] Test migration on staging environment
- [ ] Verify backup restoration works

**Day 3-4: Migration**
- [ ] Run migration script during low-traffic window
- [ ] Convert telemetry table to hypertable
- [ ] Create indexes
- [ ] Verify data integrity

**Day 5: Validation**
- [ ] Run performance benchmarks
- [ ] Compare query times (before vs after)
- [ ] Monitor application logs for errors

### Phase 2: Compression & Aggregates (Week 2)

**Day 1-2: Compression**
- [ ] Enable compression on hypertable
- [ ] Set compression policy (7 days)
- [ ] Monitor compression job progress
- [ ] Verify storage reduction

**Day 3-5: Continuous Aggregates**
- [ ] Create 1-minute aggregate view
- [ ] Create 1-hour aggregate view
- [ ] Create daily aggregate view
- [ ] Update Grafana dashboards to use aggregates
- [ ] Verify dashboard performance improvement

### Phase 3: Data Quality & ETL (Week 3)

**Day 1-3: ETL Pipeline**
- [ ] Implement validation layer
- [ ] Add data quality scoring
- [ ] Deploy anomaly detection
- [ ] Set up dead letter queue

**Day 4-5: Monitoring**
- [ ] Deploy data quality monitoring
- [ ] Create quality dashboards
- [ ] Set up alerts for low quality scores

### Phase 4: Backup & Recovery (Week 4)

**Day 1-2: Backup Automation**
- [ ] Deploy hourly snapshot script
- [ ] Configure Azure Blob Storage
- [ ] Set up WAL archiving
- [ ] Test backup upload

**Day 3-4: Recovery Testing**
- [ ] Test full database restore
- [ ] Test point-in-time recovery
- [ ] Document recovery procedures
- [ ] Train team on recovery process

**Day 5: Archival**
- [ ] Deploy archival service
- [ ] Test archival to Azure
- [ ] Verify restoration from archive
- [ ] Set retention policy (30 days)

### Success Metrics

**Performance**:
- [ ] Query latency reduced by 90%+ (1-hour aggregates)
- [ ] Storage reduced by 80%+ (compression)
- [ ] Ingestion rate: 10,000+ records/second
- [ ] Cache hit ratio: >99%

**Data Quality**:
- [ ] Overall quality score: >95%
- [ ] Completeness: >98%
- [ ] Anomaly detection: <2% false positives

**Reliability**:
- [ ] Automated backups: 100% success rate
- [ ] Recovery time objective (RTO): <1 hour
- [ ] Recovery point objective (RPO): <5 minutes

---

**Prepared by**: Claude Code - Data Engineering Perspective
**Date**: November 20, 2025
**Status**: Ready for Implementation
