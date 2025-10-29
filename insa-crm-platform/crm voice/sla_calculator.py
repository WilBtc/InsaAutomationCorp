#!/usr/bin/env python3
"""
SLA Calculator - INSA CRM Platform
Queries Prometheus metrics and calculates SLA compliance

Runs periodically to:
1. Query Prometheus for SLA metrics
2. Calculate compliance against targets
3. Store results in SLA database
4. Detect and record breaches
"""

import requests
import logging
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sla_database import SLADatabase, SLASeverity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PrometheusClient:
    """Client for querying Prometheus"""

    def __init__(self, base_url: str = "http://localhost:9090"):
        """
        Initialize Prometheus client

        Args:
            base_url: Prometheus server URL
        """
        self.base_url = base_url
        self.query_url = f"{base_url}/api/v1/query"
        self.range_query_url = f"{base_url}/api/v1/query_range"

    def query(self, promql: str) -> Optional[Dict]:
        """
        Execute instant Prometheus query

        Args:
            promql: PromQL query string

        Returns:
            Query result or None on error
        """
        try:
            response = requests.get(
                self.query_url,
                params={'query': promql},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'success':
                return data['data']
            else:
                logger.error(f"Prometheus query failed: {data}")
                return None

        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None

    def query_range(self, promql: str, start: datetime, end: datetime, step: str = "15s") -> Optional[Dict]:
        """
        Execute range Prometheus query

        Args:
            promql: PromQL query string
            start: Start time
            end: End time
            step: Query resolution (e.g., "15s", "1m", "5m")

        Returns:
            Query result or None on error
        """
        try:
            response = requests.get(
                self.range_query_url,
                params={
                    'query': promql,
                    'start': int(start.timestamp()),
                    'end': int(end.timestamp()),
                    'step': step
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'success':
                return data['data']
            else:
                logger.error(f"Prometheus range query failed: {data}")
                return None

        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None

    def extract_scalar_value(self, result: Dict) -> Optional[float]:
        """Extract scalar value from Prometheus result"""
        if not result or 'result' not in result:
            return None

        if len(result['result']) == 0:
            return None

        # Get first result
        first_result = result['result'][0]

        if 'value' in first_result:
            # Instant query result
            return float(first_result['value'][1])
        elif 'values' in first_result and len(first_result['values']) > 0:
            # Range query result - get latest value
            return float(first_result['values'][-1][1])

        return None


class SLACalculator:
    """Calculate SLA compliance from Prometheus metrics"""

    def __init__(self, config_path: str = "sla_thresholds.yml",
                 prometheus_url: str = "http://localhost:9090",
                 db_path: str = "/var/lib/insa-crm/sla_tracking.db"):
        """
        Initialize SLA calculator

        Args:
            config_path: Path to SLA thresholds YAML
            prometheus_url: Prometheus server URL
            db_path: SLA database path
        """
        self.config_path = config_path
        self.prometheus = PrometheusClient(prometheus_url)
        self.db = SLADatabase(db_path)

        # Load SLA configuration
        self.config = self._load_config()

        logger.info("SLA Calculator initialized")

    def _load_config(self) -> Dict:
        """Load SLA thresholds from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded SLA configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading SLA config: {e}")
            return {}

    def calculate_availability_sla(self, sla_config: Dict) -> Optional[float]:
        """
        Calculate availability SLA

        Availability = (successful_checks / total_checks) * 100

        Args:
            sla_config: SLA configuration dict

        Returns:
            Availability percentage or None
        """
        metric = sla_config['metric']
        calculation = sla_config.get('calculation', '')

        # Use custom calculation if provided
        if calculation:
            result = self.prometheus.query(calculation)
            return self.prometheus.extract_scalar_value(result)

        # Default: simple up/down metric
        # up == 1 means healthy, up == 0 means down
        promql = f"avg_over_time({metric}[5m]) * 100"
        result = self.prometheus.query(promql)
        return self.prometheus.extract_scalar_value(result)

    def calculate_performance_sla(self, sla_config: Dict) -> Optional[float]:
        """
        Calculate performance SLA (latency)

        Performance = histogram_quantile(percentile, metric)

        Args:
            sla_config: SLA configuration dict

        Returns:
            Latency value or None
        """
        metric = sla_config['metric']
        percentile = sla_config.get('percentile', 95) / 100.0  # Convert to 0-1
        calculation = sla_config.get('calculation', '')

        # Use custom calculation if provided
        if calculation:
            result = self.prometheus.query(calculation)
            return self.prometheus.extract_scalar_value(result)

        # Default: histogram quantile
        promql = f"""
        histogram_quantile({percentile},
          sum(rate({metric}_bucket[5m])) by (le)
        )
        """
        result = self.prometheus.query(promql)
        return self.prometheus.extract_scalar_value(result)

    def calculate_reliability_sla(self, sla_config: Dict) -> Optional[float]:
        """
        Calculate reliability SLA (error rate)

        Error Rate = (errors / total_requests) * 100

        Args:
            sla_config: SLA configuration dict

        Returns:
            Error rate percentage or None
        """
        calculation = sla_config.get('calculation', '')

        if calculation:
            result = self.prometheus.query(calculation)
            return self.prometheus.extract_scalar_value(result)

        return None

    def calculate_efficiency_sla(self, sla_config: Dict) -> Optional[float]:
        """
        Calculate efficiency SLA (cache hit rate)

        Cache Hit Rate = (hits / (hits + misses)) * 100

        Args:
            sla_config: SLA configuration dict

        Returns:
            Cache hit rate percentage or None
        """
        calculation = sla_config.get('calculation', '')

        if calculation:
            result = self.prometheus.query(calculation)
            value = self.prometheus.extract_scalar_value(result)
            # Convert from 0-1 to 0-100 if needed
            if value and value < 1:
                value = value * 100
            return value

        return None

    def calculate_sla(self, sla_name: str, sla_config: Dict) -> Optional[float]:
        """
        Calculate SLA value based on category

        Args:
            sla_name: SLA name
            sla_config: SLA configuration

        Returns:
            Calculated value or None
        """
        try:
            # Dispatch to appropriate calculator based on category
            if 'availability' in sla_name.lower() or 'uptime' in sla_name.lower():
                return self.calculate_availability_sla(sla_config)
            elif 'latency' in sla_name.lower() or 'response time' in sla_name.lower():
                return self.calculate_performance_sla(sla_config)
            elif 'error' in sla_name.lower() or 'timeout' in sla_name.lower():
                return self.calculate_reliability_sla(sla_config)
            elif 'cache' in sla_name.lower():
                return self.calculate_efficiency_sla(sla_config)
            else:
                # Try custom calculation
                calculation = sla_config.get('calculation', '')
                if calculation:
                    result = self.prometheus.query(calculation)
                    return self.prometheus.extract_scalar_value(result)

            return None

        except Exception as e:
            logger.error(f"Error calculating SLA '{sla_name}': {e}")
            return None

    def process_all_slas(self):
        """Process all SLAs and record measurements"""
        logger.info("Processing all SLAs...")

        processed = 0
        errors = 0

        # Process each SLA category
        for category, slas in self.config.items():
            if category in ('global', 'reporting', 'sla_credits', 'alert_thresholds', 'composite'):
                continue  # Skip configuration sections

            if not isinstance(slas, list):
                continue

            logger.info(f"Processing {category} SLAs ({len(slas)} SLAs)...")

            for sla_config in slas:
                sla_name = sla_config.get('name')
                target_value = sla_config.get('target')
                unit = sla_config.get('unit')
                severity = sla_config.get('severity', 'high')

                if not sla_name or target_value is None:
                    logger.warning(f"Skipping incomplete SLA config: {sla_config}")
                    continue

                # Calculate actual value
                actual_value = self.calculate_sla(sla_name, sla_config)

                if actual_value is None:
                    logger.warning(f"Could not calculate SLA: {sla_name}")
                    errors += 1
                    continue

                # Get or create SLA definition in database
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT sla_id FROM sla_definitions WHERE sla_name = ?", (sla_name,))
                row = cursor.fetchone()

                if row:
                    sla_id = row['sla_id']
                else:
                    # Create new SLA definition
                    sla_id = self.db.add_sla_definition(
                        name=sla_name,
                        category=category,
                        metric_name=sla_config.get('metric', ''),
                        target_value=target_value,
                        unit=unit,
                        severity=severity,
                        description=sla_config.get('description', ''),
                        percentile=sla_config.get('percentile')
                    )

                # Record measurement
                self.db.record_measurement(sla_id, actual_value, target_value)

                processed += 1
                logger.info(f"✅ {sla_name}: {actual_value:.2f} {unit} (target: {target_value} {unit})")

        logger.info(f"SLA processing complete: {processed} processed, {errors} errors")

    def run_continuous(self, interval: int = 300):
        """
        Run SLA calculations continuously

        Args:
            interval: Seconds between calculations (default: 300 = 5 minutes)
        """
        logger.info(f"Starting continuous SLA calculation (interval: {interval}s)")

        while True:
            try:
                start_time = time.time()

                # Process all SLAs
                self.process_all_slas()

                # Generate daily summary if it's a new day
                now = datetime.utcnow()
                if now.hour == 0 and now.minute < 10:  # Run between 00:00-00:10
                    logger.info("Generating daily summary...")
                    self.db.generate_daily_summary()

                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)

                logger.info(f"Next calculation in {sleep_time:.1f} seconds")
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Stopping SLA calculator...")
                break
            except Exception as e:
                logger.error(f"Error in SLA calculation loop: {e}")
                time.sleep(interval)

        self.db.close()

    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate SLA compliance report

        Args:
            hours: Look back period in hours

        Returns:
            Report dictionary
        """
        logger.info(f"Generating SLA report for last {hours} hours...")

        # Get current status
        status = self.db.get_current_sla_status(hours=hours)

        # Get active breaches
        breaches = self.db.get_active_breaches()

        # Calculate overall compliance
        if status:
            avg_compliance = sum(s['compliance_pct'] for s in status) / len(status)
        else:
            avg_compliance = 0.0

        report = {
            'period_hours': hours,
            'generated_at': datetime.utcnow().isoformat(),
            'overall_compliance': avg_compliance,
            'total_slas': len(status),
            'active_breaches': len(breaches),
            'slas': status,
            'breaches': [
                {
                    'sla_name': b.sla_name,
                    'breach_start': b.breach_start.isoformat(),
                    'duration_seconds': b.duration_seconds,
                    'target_value': b.target_value,
                    'actual_value': b.actual_value,
                    'severity': b.severity.value
                }
                for b in breaches
            ]
        }

        return report


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="INSA CRM SLA Calculator")
    parser.add_argument('--config', default='sla_thresholds.yml',
                       help='Path to SLA thresholds YAML')
    parser.add_argument('--prometheus', default='http://localhost:9090',
                       help='Prometheus URL')
    parser.add_argument('--db', default='/var/lib/insa-crm/sla_tracking.db',
                       help='SLA database path')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously')
    parser.add_argument('--interval', type=int, default=300,
                       help='Calculation interval in seconds (default: 300)')
    parser.add_argument('--report', action='store_true',
                       help='Generate report and exit')
    parser.add_argument('--hours', type=int, default=24,
                       help='Report period in hours (default: 24)')

    args = parser.parse_args()

    # Initialize calculator
    calculator = SLACalculator(
        config_path=args.config,
        prometheus_url=args.prometheus,
        db_path=args.db
    )

    if args.report:
        # Generate report
        report = calculator.generate_report(hours=args.hours)

        print("\n" + "=" * 60)
        print("SLA COMPLIANCE REPORT")
        print("=" * 60)
        print(f"Period: Last {report['period_hours']} hours")
        print(f"Generated: {report['generated_at']}")
        print(f"Overall Compliance: {report['overall_compliance']:.2f}%")
        print(f"Total SLAs: {report['total_slas']}")
        print(f"Active Breaches: {report['active_breaches']}")
        print("=" * 60)

        if report['slas']:
            print("\nSLA Status:")
            print(f"{'SLA Name':<40} {'Target':<12} {'Actual':<12} {'Compliance':<12}")
            print("-" * 80)
            for sla in report['slas']:
                print(f"{sla['sla_name']:<40} "
                      f"{sla['target']:.2f} {sla['unit']:<6} "
                      f"{sla['avg_actual']:.2f} {sla['unit']:<6} "
                      f"{sla['compliance_pct']:.1f}%")

        if report['breaches']:
            print("\nActive Breaches:")
            for breach in report['breaches']:
                print(f"  • {breach['sla_name']}")
                print(f"    Started: {breach['breach_start']}")
                print(f"    Severity: {breach['severity']}")
                print(f"    Target: {breach['target_value']}, Actual: {breach['actual_value']}")

        print("=" * 60)

    elif args.continuous:
        # Run continuously
        calculator.run_continuous(interval=args.interval)
    else:
        # Run once
        calculator.process_all_slas()


if __name__ == '__main__':
    main()
