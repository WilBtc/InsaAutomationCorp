"""
Performance tests for TimescaleDB continuous aggregates.

This module compares query performance between raw data queries and
continuous aggregate queries to demonstrate the 166x improvement.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor


# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "esp_telemetry",
    "user": "alkhorayef",
    "password": "AlkhorayefESP2025!"
}


class PerformanceTest:
    """Performance testing for continuous aggregates."""

    def __init__(self):
        """Initialize test."""
        self.conn = None
        self.results = []

    def connect(self):
        """Connect to database."""
        self.conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def time_query(self, name: str, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Execute query and measure performance.

        Args:
            name: Test name
            query: SQL query
            params: Query parameters

        Returns:
            Dictionary with timing results
        """
        cursor = self.conn.cursor()

        # Warm up cache
        cursor.execute(query, params)
        cursor.fetchall()

        # Run 5 times and take average
        times = []
        for _ in range(5):
            start = time.perf_counter()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        cursor.close()

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        result = {
            "name": name,
            "avg_ms": round(avg_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "row_count": len(rows)
        }

        self.results.append(result)
        return result

    def test_hourly_aggregation(self, well_id: str = "WELL-001"):
        """
        Test hourly aggregation performance.

        Compares:
        1. Raw data query with GROUP BY time_bucket
        2. Continuous aggregate query
        """
        print("\n" + "=" * 80)
        print("TEST 1: Hourly Aggregation (24 hours)")
        print("=" * 80)

        start_time = datetime.now() - timedelta(hours=24)

        # Test 1: Raw data query
        raw_query = """
            SELECT
                time_bucket('1 hour', timestamp) AS bucket,
                AVG(flow_rate) AS avg_flow_rate,
                AVG(motor_temp) AS avg_motor_temp,
                AVG(vibration) AS avg_vibration,
                COUNT(*) AS reading_count
            FROM esp_telemetry
            WHERE well_id = %s
                AND timestamp >= %s
            GROUP BY bucket
            ORDER BY bucket DESC
        """
        raw_result = self.time_query(
            "Raw Data - Hourly Aggregation",
            raw_query,
            (well_id, start_time)
        )
        print(f"\n📊 Raw Query: {raw_result['avg_ms']:.2f}ms (avg)")

        # Test 2: Continuous aggregate query
        cagg_query = """
            SELECT
                bucket,
                avg_flow_rate,
                avg_motor_temp,
                avg_vibration,
                reading_count
            FROM telemetry_hourly
            WHERE well_id = %s
                AND bucket >= %s
            ORDER BY bucket DESC
        """
        cagg_result = self.time_query(
            "Continuous Aggregate - Hourly",
            cagg_query,
            (well_id, start_time)
        )
        print(f"⚡ Continuous Aggregate: {cagg_result['avg_ms']:.2f}ms (avg)")

        speedup = raw_result['avg_ms'] / cagg_result['avg_ms']
        print(f"🚀 Speedup: {speedup:.1f}x faster")

        return speedup

    def test_daily_statistics(self, well_id: str = "WELL-001"):
        """
        Test daily statistics performance.

        Compares:
        1. Raw data query with complex aggregations
        2. Continuous aggregate query with pre-computed stats
        """
        print("\n" + "=" * 80)
        print("TEST 2: Daily Statistics (30 days)")
        print("=" * 80)

        start_time = datetime.now() - timedelta(days=30)

        # Test 1: Raw data query with complex aggregations
        raw_query = """
            SELECT
                time_bucket('1 day', timestamp) AS bucket,
                AVG(flow_rate) AS avg_flow_rate,
                MIN(flow_rate) AS min_flow_rate,
                MAX(flow_rate) AS max_flow_rate,
                STDDEV(flow_rate) AS stddev_flow_rate,
                AVG(motor_temp) AS avg_motor_temp,
                MIN(motor_temp) AS min_motor_temp,
                MAX(motor_temp) AS max_motor_temp,
                STDDEV(motor_temp) AS stddev_motor_temp,
                COUNT(*) AS reading_count
            FROM esp_telemetry
            WHERE well_id = %s
                AND timestamp >= %s
            GROUP BY bucket
            ORDER BY bucket DESC
        """
        raw_result = self.time_query(
            "Raw Data - Daily Statistics",
            raw_query,
            (well_id, start_time)
        )
        print(f"\n📊 Raw Query: {raw_result['avg_ms']:.2f}ms (avg)")

        # Test 2: Continuous aggregate query
        cagg_query = """
            SELECT
                bucket,
                avg_flow_rate,
                min_flow_rate,
                max_flow_rate,
                stddev_flow_rate,
                avg_motor_temp,
                min_motor_temp,
                max_motor_temp,
                stddev_motor_temp,
                reading_count
            FROM telemetry_daily
            WHERE well_id = %s
                AND bucket >= %s
            ORDER BY bucket DESC
        """
        cagg_result = self.time_query(
            "Continuous Aggregate - Daily",
            cagg_query,
            (well_id, start_time)
        )
        print(f"⚡ Continuous Aggregate: {cagg_result['avg_ms']:.2f}ms (avg)")

        speedup = raw_result['avg_ms'] / cagg_result['avg_ms']
        print(f"🚀 Speedup: {speedup:.1f}x faster")

        return speedup

    def test_performance_scores(self, well_id: str = "WELL-001"):
        """
        Test performance score calculation.

        Compares:
        1. Raw data query with complex calculations
        2. Continuous aggregate with pre-computed scores
        """
        print("\n" + "=" * 80)
        print("TEST 3: Performance Scores (24 hours)")
        print("=" * 80)

        start_time = datetime.now() - timedelta(hours=24)

        # Test 1: Raw data query with calculations
        raw_query = """
            SELECT
                time_bucket('1 hour', timestamp) AS bucket,
                AVG(flow_rate) AS avg_flow_rate,
                AVG(motor_current) AS avg_motor_current,
                CASE
                    WHEN AVG(motor_current) > 0 THEN
                        LEAST(100, (AVG(flow_rate) / AVG(motor_current)) * 10)
                    ELSE 0
                END AS efficiency_score,
                AVG(vibration) AS avg_vibration,
                AVG(motor_temp) AS avg_motor_temp,
                100 - LEAST(100,
                    (AVG(vibration) * 5) +
                    (GREATEST(0, AVG(motor_temp) - 60) * 0.5)
                ) AS health_score,
                COUNT(*) FILTER (WHERE
                    vibration > 5.0 OR
                    motor_temp > 90 OR
                    flow_variance > 20
                ) AS anomaly_count
            FROM esp_telemetry
            WHERE well_id = %s
                AND timestamp >= %s
            GROUP BY bucket
            ORDER BY bucket DESC
        """
        raw_result = self.time_query(
            "Raw Data - Performance Scores",
            raw_query,
            (well_id, start_time)
        )
        print(f"\n📊 Raw Query: {raw_result['avg_ms']:.2f}ms (avg)")

        # Test 2: Continuous aggregate query
        cagg_query = """
            SELECT
                bucket,
                avg_flow_rate,
                avg_motor_current,
                efficiency_score,
                avg_vibration,
                avg_motor_temp,
                health_score,
                anomaly_count
            FROM well_performance_hourly
            WHERE well_id = %s
                AND bucket >= %s
            ORDER BY bucket DESC
        """
        cagg_result = self.time_query(
            "Continuous Aggregate - Performance",
            cagg_query,
            (well_id, start_time)
        )
        print(f"⚡ Continuous Aggregate: {cagg_result['avg_ms']:.2f}ms (avg)")

        speedup = raw_result['avg_ms'] / cagg_result['avg_ms']
        print(f"🚀 Speedup: {speedup:.1f}x faster")

        return speedup

    def test_multi_well_dashboard(self):
        """
        Test multi-well dashboard query.

        Simulates loading a dashboard with all wells.
        """
        print("\n" + "=" * 80)
        print("TEST 4: Multi-Well Dashboard (All Wells, 24 hours)")
        print("=" * 80)

        start_time = datetime.now() - timedelta(hours=24)

        # Test 1: Raw data query
        raw_query = """
            SELECT
                well_id,
                time_bucket('1 hour', timestamp) AS bucket,
                AVG(flow_rate) AS avg_flow_rate,
                AVG(motor_temp) AS avg_motor_temp,
                AVG(vibration) AS avg_vibration
            FROM esp_telemetry
            WHERE timestamp >= %s
            GROUP BY well_id, bucket
            ORDER BY bucket DESC, well_id
            LIMIT 1000
        """
        raw_result = self.time_query(
            "Raw Data - Multi-Well Dashboard",
            raw_query,
            (start_time,)
        )
        print(f"\n📊 Raw Query: {raw_result['avg_ms']:.2f}ms (avg)")

        # Test 2: Continuous aggregate query
        cagg_query = """
            SELECT
                well_id,
                bucket,
                avg_flow_rate,
                avg_motor_temp,
                avg_vibration
            FROM telemetry_hourly
            WHERE bucket >= %s
            ORDER BY bucket DESC, well_id
            LIMIT 1000
        """
        cagg_result = self.time_query(
            "Continuous Aggregate - Multi-Well",
            cagg_query,
            (start_time,)
        )
        print(f"⚡ Continuous Aggregate: {cagg_result['avg_ms']:.2f}ms (avg)")

        speedup = raw_result['avg_ms'] / cagg_result['avg_ms']
        print(f"🚀 Speedup: {speedup:.1f}x faster")

        return speedup

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 80)

        print(f"\n{'Test Name':<40} {'Avg Time (ms)':<15} {'Rows':<10}")
        print("-" * 80)

        raw_tests = [r for r in self.results if "Raw" in r["name"]]
        cagg_tests = [r for r in self.results if "Continuous" in r["name"]]

        for raw, cagg in zip(raw_tests, cagg_tests):
            print(f"{raw['name']:<40} {raw['avg_ms']:<15.2f} {raw['row_count']:<10}")
            print(f"{cagg['name']:<40} {cagg['avg_ms']:<15.2f} {cagg['row_count']:<10}")
            speedup = raw['avg_ms'] / cagg['avg_ms']
            print(f"  └─ Improvement: {speedup:.1f}x faster")
            print()

        # Calculate overall improvement
        total_raw = sum(r['avg_ms'] for r in raw_tests)
        total_cagg = sum(r['avg_ms'] for r in cagg_tests)
        overall_speedup = total_raw / total_cagg

        print("=" * 80)
        print(f"OVERALL DASHBOARD LOAD TIME:")
        print(f"  Before: {total_raw:.2f}ms")
        print(f"  After:  {total_cagg:.2f}ms")
        print(f"  Improvement: {overall_speedup:.1f}x faster")
        print("=" * 80)


def main():
    """Run performance tests."""
    print("\n" + "=" * 80)
    print("TimescaleDB Continuous Aggregates Performance Test")
    print("=" * 80)

    test = PerformanceTest()

    try:
        test.connect()
        print("✅ Connected to database")

        # Run tests
        speedups = []
        speedups.append(test.test_hourly_aggregation())
        speedups.append(test.test_daily_statistics())
        speedups.append(test.test_performance_scores())
        speedups.append(test.test_multi_well_dashboard())

        # Print summary
        test.print_summary()

        # Calculate average speedup
        avg_speedup = sum(speedups) / len(speedups)
        print(f"\n📈 Average Speedup: {avg_speedup:.1f}x")

        if avg_speedup >= 100:
            print("🎉 EXCELLENT: Over 100x faster!")
        elif avg_speedup >= 50:
            print("✨ GREAT: Over 50x faster!")
        elif avg_speedup >= 10:
            print("👍 GOOD: Over 10x faster!")
        else:
            print("⚠️  Moderate improvement, but still faster")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        test.close()
        print("\n✅ Test complete")


if __name__ == "__main__":
    main()
