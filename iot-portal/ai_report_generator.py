#!/usr/bin/env python3
"""
AI Narrative Report Generator
Generates human-readable insights and reports from IoT telemetry data

Version: 1.0
Date: October 30, 2025
Author: INSA Automation Corp
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
import statistics
import os

logger = logging.getLogger(__name__)


class AIReportGenerator:
    """
    Generates AI-powered narrative reports from IoT sensor data

    Features:
    - Statistical analysis of sensor trends
    - Anomaly detection summaries
    - Cross-sensor correlation insights
    - Natural language narrative generation
    - Multiple report formats (HTML, PDF, Email)
    """

    def __init__(self, db_config: Dict[str, str], lstm_forecaster=None):
        """
        Initialize report generator

        Args:
            db_config: Database connection configuration
            lstm_forecaster: Optional LSTMForecaster instance for predictive maintenance
        """
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        self.lstm_forecaster = lstm_forecaster

    def _get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            return None

    def get_sensor_statistics(self, device_id: str, sensor_key: str,
                              hours: int = 24, use_all_data: bool = False) -> Optional[Dict]:
        """
        Calculate comprehensive statistics for a sensor

        Args:
            device_id: Device identifier
            sensor_key: Sensor key/metric name
            hours: Time window in hours (ignored if use_all_data=True)
            use_all_data: If True, use all available data regardless of timestamp

        Returns:
            Dictionary with statistics or None if error
        """
        conn = self._get_db_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get sensor data for time window or all data
            if use_all_data:
                query = """
                    SELECT value, timestamp, unit
                    FROM telemetry
                    WHERE device_id = %s
                      AND key = %s
                    ORDER BY timestamp ASC
                """
                cur.execute(query, (device_id, sensor_key))
            else:
                query = """
                    SELECT value, timestamp, unit
                    FROM telemetry
                    WHERE device_id = %s
                      AND key = %s
                      AND timestamp >= NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp ASC
                """
                cur.execute(query, (device_id, sensor_key, hours))
            data = cur.fetchall()

            if not data:
                return None

            values = [float(row['value']) for row in data]
            timestamps = [row['timestamp'] for row in data]

            # Calculate statistics
            stats = {
                'sensor_key': sensor_key,
                'device_id': device_id,
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'latest': values[-1],
                'unit': data[0]['unit'] if data[0]['unit'] else '',
                'start_time': timestamps[0],
                'end_time': timestamps[-1],
                'time_window_hours': hours
            }

            # Calculate trend (simple linear regression slope)
            if len(values) > 1:
                x = list(range(len(values)))
                x_mean = statistics.mean(x)
                y_mean = statistics.mean(values)

                numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(len(values)))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(len(values)))

                slope = numerator / denominator if denominator != 0 else 0
                stats['trend_slope'] = slope
                stats['trend_direction'] = 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
            else:
                stats['trend_slope'] = 0
                stats['trend_direction'] = 'stable'

            # Calculate rate of change (percentage)
            if len(values) > 1 and values[0] != 0:
                stats['change_percent'] = ((values[-1] - values[0]) / abs(values[0])) * 100
            else:
                stats['change_percent'] = 0

            return stats

        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            return None
        finally:
            conn.close()

    def detect_correlations(self, sensor_keys: List[Tuple[str, str]],
                           hours: int = 24, use_all_data: bool = False) -> List[Dict]:
        """
        Find correlations between multiple sensors

        Args:
            sensor_keys: List of (device_id, sensor_key) tuples
            hours: Time window in hours (ignored if use_all_data=True)
            use_all_data: If True, use all available data

        Returns:
            List of correlation insights
        """
        correlations = []

        # Get statistics for all sensors
        sensor_stats = {}
        for device_id, sensor_key in sensor_keys:
            stats = self.get_sensor_statistics(device_id, sensor_key, hours, use_all_data)
            if stats:
                sensor_stats[f"{device_id}_{sensor_key}"] = stats

        # Simple correlation detection (if one changes, did another change?)
        keys = list(sensor_stats.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                key1, key2 = keys[i], keys[j]
                stats1, stats2 = sensor_stats[key1], sensor_stats[key2]

                # Check if both showed significant changes in same direction
                change1 = abs(stats1.get('change_percent', 0))
                change2 = abs(stats2.get('change_percent', 0))

                if change1 > 5 and change2 > 5:  # Both changed more than 5%
                    direction1 = 'up' if stats1.get('change_percent', 0) > 0 else 'down'
                    direction2 = 'up' if stats2.get('change_percent', 0) > 0 else 'down'

                    correlation_type = 'positive' if direction1 == direction2 else 'negative'

                    correlations.append({
                        'sensor1': {
                            'device_id': stats1['device_id'],
                            'sensor_key': stats1['sensor_key'],
                            'change_percent': stats1['change_percent']
                        },
                        'sensor2': {
                            'device_id': stats2['device_id'],
                            'sensor_key': stats2['sensor_key'],
                            'change_percent': stats2['change_percent']
                        },
                        'correlation_type': correlation_type,
                        'strength': min(change1, change2)  # Use smaller change as strength indicator
                    })

        return correlations

    def get_recent_anomalies(self, hours: int = 24, limit: int = 10, use_all_data: bool = False) -> List[Dict]:
        """
        Get recent anomaly detections from ML system

        Args:
            hours: Time window in hours (ignored if use_all_data=True)
            limit: Maximum number of anomalies to return
            use_all_data: If True, get all anomalies regardless of timestamp

        Returns:
            List of anomaly records
        """
        conn = self._get_db_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Fix type mismatch: cast varchar to uuid for join
            if use_all_data:
                query = """
                    SELECT ad.*, d.name as device_name, mm.metric_name
                    FROM anomaly_detections ad
                    LEFT JOIN ml_models mm ON ad.model_id = mm.id
                    LEFT JOIN devices d ON mm.device_id::uuid = d.id
                    WHERE ad.is_anomaly = true
                    ORDER BY ad.anomaly_score DESC
                    LIMIT %s
                """
                cur.execute(query, (limit,))
            else:
                query = """
                    SELECT ad.*, d.name as device_name, mm.metric_name
                    FROM anomaly_detections ad
                    LEFT JOIN ml_models mm ON ad.model_id = mm.id
                    LEFT JOIN devices d ON mm.device_id::uuid = d.id
                    WHERE ad.detected_at >= NOW() - INTERVAL '%s hours'
                      AND ad.is_anomaly = true
                    ORDER BY ad.anomaly_score DESC
                    LIMIT %s
                """
                cur.execute(query, (hours, limit))
            return cur.fetchall()

        except Exception as e:
            self.logger.error(f"Error fetching anomalies: {e}")
            return []
        finally:
            conn.close()

    def get_lstm_predictions(self, sensor_keys: List[Tuple[str, str]]) -> List[Dict]:
        """
        Get LSTM failure predictions for multiple sensors

        Args:
            sensor_keys: List of (device_id, sensor_key) tuples

        Returns:
            List of prediction records with failure risk assessments
        """
        if not self.lstm_forecaster:
            self.logger.warning("LSTM forecaster not available - skipping predictions")
            return []

        predictions = []

        for device_id, sensor_key in sensor_keys:
            try:
                # Get prediction from LSTM model
                result = self.lstm_forecaster.predict_future(device_id, sensor_key)

                if result.get('success'):
                    prediction_record = {
                        'device_id': device_id,
                        'sensor_key': sensor_key,
                        'forecast_horizon_hours': result['forecast_horizon_hours'],
                        'failure_risk': result['failure_risk'],
                        'forecasts': result['forecasts'][:6],  # First 6 hours
                        'last_value': result['metadata']['last_actual_value'],
                        'model_accuracy': result['metadata']['model_accuracy']
                    }
                    predictions.append(prediction_record)
                    self.logger.info(
                        f"LSTM prediction for {device_id}/{sensor_key}: "
                        f"{result['failure_risk']['risk_level']} risk"
                    )

            except Exception as e:
                self.logger.error(f"Error getting LSTM prediction for {device_id}/{sensor_key}: {e}")
                continue

        return predictions

    def generate_narrative_with_ai(self, report_data: Dict) -> str:
        """
        Generate human-readable narrative using Claude Code subprocess
        (Zero API cost - uses local Claude Code instance)

        Args:
            report_data: Dictionary with sensor statistics, anomalies, correlations, LSTM predictions

        Returns:
            Natural language narrative text
        """
        try:
            # Create a prompt for Claude to analyze the data
            lstm_section = ""
            if report_data.get('lstm_predictions'):
                lstm_section = f"""

LSTM FAILURE PREDICTIONS (12-hour forecast):
{json.dumps(report_data.get('lstm_predictions', []), indent=2, default=str)}"""

            prompt = f"""You are an industrial IoT analyst for a glass manufacturing plant.

Analyze the following sensor data and generate a concise, actionable executive summary (3-5 paragraphs):

SENSOR STATISTICS (Last 24 Hours):
{json.dumps(report_data.get('sensor_stats', {}), indent=2, default=str)}

DETECTED ANOMALIES:
{json.dumps(report_data.get('anomalies', []), indent=2, default=str)}

CROSS-SENSOR CORRELATIONS:
{json.dumps(report_data.get('correlations', []), indent=2, default=str)}{lstm_section}

Generate a professional report that:
1. Summarizes key findings in plain language
2. Highlights any concerning trends or anomalies
3. Explains correlations in context of glass manufacturing
4. PRIORITIZE LSTM predictions - identify high-risk equipment failures
5. Provides actionable maintenance recommendations with timeframes
6. Prioritizes critical issues by urgency

Format as plain text paragraphs (not markdown). Be concise but specific with numbers."""

            # Use Claude Code subprocess (same approach as autonomous healing system)
            process = subprocess.Popen(
                ['claude', '--no-color'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=prompt, timeout=60)

            if process.returncode == 0 and stdout.strip():
                return stdout.strip()
            else:
                # Fallback to template-based narrative if Claude not available
                return self._generate_template_narrative(report_data)

        except Exception as e:
            self.logger.error(f"Error generating AI narrative: {e}")
            return self._generate_template_narrative(report_data)

    def _generate_template_narrative(self, report_data: Dict) -> str:
        """
        Fallback: Generate narrative using templates when AI is not available

        Args:
            report_data: Report data dictionary

        Returns:
            Template-based narrative text
        """
        narrative_parts = []

        # Opening
        narrative_parts.append(
            f"INSA IoT Platform - Automated Report\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # Sensor statistics summary
        sensor_stats = report_data.get('sensor_stats', {})
        if sensor_stats:
            narrative_parts.append("\nKEY SENSOR METRICS:")
            for sensor_id, stats in sensor_stats.items():
                trend_emoji = "📈" if stats['trend_direction'] == 'increasing' else "📉" if stats['trend_direction'] == 'decreasing' else "➡️"
                narrative_parts.append(
                    f"\n• Sensor {stats['sensor_key']} ({stats['device_id']}): "
                    f"{stats['latest']:.2f} {stats['unit']} {trend_emoji} "
                    f"({stats['trend_direction']}, {stats['change_percent']:+.1f}% change)"
                )

        # Anomalies
        anomalies = report_data.get('anomalies', [])
        if anomalies:
            narrative_parts.append(f"\n\n⚠️ ANOMALIES DETECTED ({len(anomalies)}):")
            for anomaly in anomalies[:5]:  # Top 5
                narrative_parts.append(
                    f"\n• {anomaly.get('device_name', 'Unknown')} - "
                    f"{anomaly.get('metric_name', 'Unknown')}: "
                    f"Anomaly score {anomaly.get('anomaly_score', 0):.2f}"
                )

        # Correlations
        correlations = report_data.get('correlations', [])
        if correlations:
            narrative_parts.append(f"\n\n🔗 CROSS-SENSOR CORRELATIONS ({len(correlations)}):")
            for corr in correlations[:3]:  # Top 3
                s1 = corr['sensor1']
                s2 = corr['sensor2']
                narrative_parts.append(
                    f"\n• Sensor {s1['sensor_key']} and {s2['sensor_key']} "
                    f"showed {corr['correlation_type']} correlation "
                    f"({s1['change_percent']:+.1f}% and {s2['change_percent']:+.1f}%)"
                )

        # LSTM Predictions
        lstm_predictions = report_data.get('lstm_predictions', [])
        if lstm_predictions:
            narrative_parts.append(f"\n\n🔮 PREDICTIVE MAINTENANCE FORECAST ({len(lstm_predictions)} sensors):")
            high_risk_count = sum(1 for p in lstm_predictions if p['failure_risk']['risk_level'] == 'high')
            medium_risk_count = sum(1 for p in lstm_predictions if p['failure_risk']['risk_level'] == 'medium')

            if high_risk_count > 0:
                narrative_parts.append(f"\n⚠️ HIGH RISK ({high_risk_count} sensors):")
                for pred in lstm_predictions:
                    if pred['failure_risk']['risk_level'] == 'high':
                        ttf = pred['failure_risk'].get('time_to_failure_hours')
                        ttf_text = f"{ttf}h" if ttf else "N/A"
                        narrative_parts.append(
                            f"\n  • Sensor {pred['sensor_key']} ({pred['device_id']}): "
                            f"Time to failure: {ttf_text} - "
                            f"{pred['failure_risk']['recommended_action']}"
                        )

            if medium_risk_count > 0:
                narrative_parts.append(f"\n⚠️ MEDIUM RISK ({medium_risk_count} sensors):")
                for pred in lstm_predictions:
                    if pred['failure_risk']['risk_level'] == 'medium':
                        narrative_parts.append(
                            f"\n  • Sensor {pred['sensor_key']}: {pred['failure_risk']['recommended_action']}"
                        )

        # Recommendations
        narrative_parts.append("\n\n📋 RECOMMENDATIONS:")
        if lstm_predictions:
            high_risk = [p for p in lstm_predictions if p['failure_risk']['risk_level'] == 'high']
            if high_risk:
                narrative_parts.append("\n🔴 URGENT: Address high-risk equipment failures within 24-48 hours")
        if anomalies:
            narrative_parts.append("\n• Investigate detected anomalies within 24 hours")
        if any(abs(stats.get('change_percent', 0)) > 10 for stats in sensor_stats.values()):
            narrative_parts.append("\n• Review sensors with >10% change for equipment issues")
        if not anomalies and not correlations and not lstm_predictions:
            narrative_parts.append("\n✅ All systems operating normally - continue monitoring")

        return '\n'.join(narrative_parts)

    def generate_report(self, device_location: str = "Vidrio Andino",
                       hours: int = 24, use_ai: bool = True, use_all_data: bool = False) -> Dict:
        """
        Generate comprehensive AI report for a location

        Args:
            device_location: Location filter (e.g., "Vidrio Andino")
            hours: Time window in hours (ignored if use_all_data=True)
            use_ai: Whether to use AI narrative generation (vs template)
            use_all_data: If True, use all available data regardless of timestamp

        Returns:
            Dictionary with report data and narrative
        """
        if use_all_data:
            self.logger.info(f"Generating report for {device_location}, using all available data")
        else:
            self.logger.info(f"Generating report for {device_location}, last {hours} hours")

        # Get devices at location
        conn = self._get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}

        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get devices
            cur.execute(
                "SELECT id, name FROM devices WHERE location = %s",
                (device_location,)
            )
            devices = cur.fetchall()

            if not devices:
                return {'error': f'No devices found at location: {device_location}'}

            # Get key sensors (for glass manufacturing: furnace temps, quality, pressure, zones)
            key_sensors = [
                ('146', 'Furnace Temperature 1'),
                ('147', 'Furnace Temperature 2'),
                ('166', 'Quality Yield'),
                ('79', 'Pressure'),
                ('80', 'Temperature Zone')
            ]

            # Collect sensor statistics
            sensor_stats = {}
            sensor_keys_for_correlation = []

            for device in devices:
                for sensor_key, sensor_name in key_sensors:
                    stats = self.get_sensor_statistics(device['id'], sensor_key, hours, use_all_data)
                    if stats:
                        sensor_id = f"{device['name']}_{sensor_key}"
                        sensor_stats[sensor_id] = {
                            **stats,
                            'device_name': device['name'],
                            'sensor_name': sensor_name
                        }
                        sensor_keys_for_correlation.append((device['id'], sensor_key))

            # Get anomalies
            anomalies = self.get_recent_anomalies(hours, limit=10, use_all_data=use_all_data)

            # Detect correlations
            correlations = self.detect_correlations(sensor_keys_for_correlation, hours, use_all_data)

            # Get LSTM predictions (if forecaster available)
            lstm_predictions = []
            if self.lstm_forecaster:
                self.logger.info("Fetching LSTM predictions for sensors...")
                lstm_predictions = self.get_lstm_predictions(sensor_keys_for_correlation)
                self.logger.info(f"Retrieved {len(lstm_predictions)} LSTM predictions")

            # Compile report data
            report_data = {
                'location': device_location,
                'time_window_hours': hours,
                'generated_at': datetime.now().isoformat(),
                'device_count': len(devices),
                'sensor_stats': sensor_stats,
                'anomalies': anomalies,
                'correlations': correlations,
                'lstm_predictions': lstm_predictions
            }

            # Generate narrative
            if use_ai:
                narrative = self.generate_narrative_with_ai(report_data)
            else:
                narrative = self._generate_template_narrative(report_data)

            report_data['narrative'] = narrative

            self.logger.info(f"Report generated successfully with {len(sensor_stats)} sensors")

            return report_data

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {'error': str(e)}
        finally:
            conn.close()

    def generate_html_report(self, report_data: Dict) -> str:
        """
        Convert report data to HTML format

        Args:
            report_data: Report data dictionary

        Returns:
            HTML string
        """
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>INSA IoT Report - {location}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e2e8f0;
        }}
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            color: white;
        }}
        .header .subtitle {{
            margin-top: 10px;
            opacity: 0.9;
            font-size: 16px;
        }}
        .section {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #a855f7;
            font-size: 24px;
            border-bottom: 2px solid rgba(168, 85, 247, 0.3);
            padding-bottom: 10px;
        }}
        .narrative {{
            line-height: 1.8;
            font-size: 16px;
            white-space: pre-wrap;
        }}
        .sensor-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .sensor-card {{
            background: rgba(99, 102, 241, 0.1);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #6366f1;
        }}
        .sensor-card .name {{
            font-weight: bold;
            color: #a855f7;
            margin-bottom: 8px;
        }}
        .sensor-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #10b981;
            margin: 10px 0;
        }}
        .sensor-card .trend {{
            font-size: 14px;
            opacity: 0.8;
        }}
        .anomaly {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
        }}
        .correlation {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid #10b981;
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
        }}
        .lstm-prediction {{
            background: rgba(139, 92, 246, 0.1);
            border-left: 4px solid #8b5cf6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
        }}
        .lstm-prediction.high-risk {{
            background: rgba(239, 68, 68, 0.15);
            border-left-color: #ef4444;
        }}
        .lstm-prediction.medium-risk {{
            background: rgba(251, 191, 36, 0.15);
            border-left-color: #fbbf24;
        }}
        .lstm-prediction .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .lstm-prediction .risk-badge.high {{
            background: #ef4444;
            color: white;
        }}
        .lstm-prediction .risk-badge.medium {{
            background: #fbbf24;
            color: #0a0e27;
        }}
        .lstm-prediction .risk-badge.low {{
            background: #10b981;
            color: white;
        }}
        .lstm-forecast {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 8px;
            margin-top: 10px;
            font-size: 12px;
        }}
        .lstm-forecast .hour {{
            background: rgba(255, 255, 255, 0.05);
            padding: 6px;
            border-radius: 4px;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            opacity: 0.7;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔥 INSA IoT Platform - AI Report</h1>
        <div class="subtitle">
            Location: {location} | Generated: {generated_at} | Window: {time_window_hours} hours
        </div>
    </div>

    <div class="section">
        <h2>📊 Executive Summary</h2>
        <div class="narrative">{narrative}</div>
    </div>

    <div class="section">
        <h2>🌡️ Sensor Metrics</h2>
        <div class="sensor-grid">
            {sensor_cards}
        </div>
    </div>

    {anomalies_section}

    {correlations_section}

    {lstm_section}

    <div class="footer">
        INSA Automation Corp | Advanced Industrial IoT Platform v2.0<br>
        Report generated automatically by AI Narrative Engine + LSTM Forecasting
    </div>
</body>
</html>
"""

        # Generate sensor cards
        sensor_cards = []
        for sensor_id, stats in report_data.get('sensor_stats', {}).items():
            trend_emoji = "📈" if stats['trend_direction'] == 'increasing' else "📉" if stats['trend_direction'] == 'decreasing' else "➡️"
            sensor_cards.append(f"""
            <div class="sensor-card">
                <div class="name">{stats.get('sensor_name', stats['sensor_key'])} ({stats['device_name']})</div>
                <div class="value">{stats['latest']:.2f} {stats['unit']}</div>
                <div class="trend">{trend_emoji} {stats['trend_direction']} ({stats['change_percent']:+.1f}%)</div>
                <div class="trend">Avg: {stats['mean']:.2f} | Range: {stats['min']:.2f} - {stats['max']:.2f}</div>
            </div>
            """)

        # Generate anomalies section
        anomalies = report_data.get('anomalies', [])
        if anomalies:
            anomaly_items = []
            for anomaly in anomalies:
                anomaly_items.append(f"""
                <div class="anomaly">
                    <strong>⚠️ {anomaly.get('device_name', 'Unknown Device')}</strong> -
                    {anomaly.get('metric_name', 'Unknown Metric')}<br>
                    Anomaly Score: {anomaly.get('anomaly_score', 0):.2f} |
                    Detected: {anomaly.get('detected_at', 'Unknown')}
                </div>
                """)
            anomalies_section = f"""
            <div class="section">
                <h2>⚠️ Detected Anomalies ({len(anomalies)})</h2>
                {''.join(anomaly_items)}
            </div>
            """
        else:
            anomalies_section = ""

        # Generate correlations section
        correlations = report_data.get('correlations', [])
        if correlations:
            correlation_items = []
            for corr in correlations:
                s1 = corr['sensor1']
                s2 = corr['sensor2']
                correlation_items.append(f"""
                <div class="correlation">
                    <strong>🔗 {corr['correlation_type'].title()} Correlation</strong><br>
                    Sensor {s1['sensor_key']} ({s1['change_percent']:+.1f}%) ↔
                    Sensor {s2['sensor_key']} ({s2['change_percent']:+.1f}%)
                </div>
                """)
            correlations_section = f"""
            <div class="section">
                <h2>🔗 Cross-Sensor Correlations ({len(correlations)})</h2>
                {''.join(correlation_items)}
            </div>
            """
        else:
            correlations_section = ""

        # Generate LSTM predictions section
        lstm_predictions = report_data.get('lstm_predictions', [])
        if lstm_predictions:
            lstm_items = []
            for pred in lstm_predictions:
                risk = pred['failure_risk']
                risk_level = risk['risk_level']
                risk_class = f"{risk_level}-risk" if risk_level in ['high', 'medium'] else ""

                # Format forecasts (first 6 hours)
                forecast_html = []
                for fc in pred['forecasts'][:6]:
                    forecast_html.append(f"""
                    <div class="hour">
                        +{fc['hours_ahead']}h<br>
                        <strong>{fc['predicted_value']:.1f}</strong>
                    </div>
                    """)

                ttf = risk.get('time_to_failure_hours')
                ttf_text = f"{ttf} hours" if ttf else "N/A"

                lstm_items.append(f"""
                <div class="lstm-prediction {risk_class}">
                    <strong>🔮 Sensor {pred['sensor_key']}</strong>
                    <span class="risk-badge {risk_level}">{risk_level.upper()} RISK</span>
                    <br>
                    <div style="margin-top: 8px;">
                        Current Value: {pred['last_value']:.2f} |
                        Time to Failure: {ttf_text} |
                        Model MAE: {pred['model_accuracy']['val_mae']:.2f}
                    </div>
                    <div style="margin-top: 8px; font-size: 13px; opacity: 0.9;">
                        {risk['recommended_action']}
                    </div>
                    <div class="lstm-forecast">
                        {''.join(forecast_html)}
                    </div>
                </div>
                """)

            lstm_section = f"""
            <div class="section">
                <h2>🔮 LSTM Predictive Maintenance Forecast ({len(lstm_predictions)} sensors)</h2>
                <p style="opacity: 0.9; margin-bottom: 15px;">
                    12-hour equipment failure predictions using deep learning time-series analysis
                </p>
                {''.join(lstm_items)}
            </div>
            """
        else:
            lstm_section = ""

        # Fill template
        html = html_template.format(
            location=report_data.get('location', 'Unknown'),
            generated_at=report_data.get('generated_at', datetime.now().isoformat()),
            time_window_hours=report_data.get('time_window_hours', 24),
            narrative=report_data.get('narrative', 'No narrative generated'),
            sensor_cards=''.join(sensor_cards) if sensor_cards else '<p>No sensor data available</p>',
            anomalies_section=anomalies_section,
            correlations_section=correlations_section,
            lstm_section=lstm_section
        )

        return html

    def save_report(self, report_data: Dict, format: str = 'html',
                   filename: Optional[str] = None) -> str:
        """
        Save report to file

        Args:
            report_data: Report data dictionary
            format: Output format ('html', 'json', 'txt')
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            location = report_data.get('location', 'unknown').replace(' ', '_')
            filename = f"report_{location}_{timestamp}.{format}"

        filepath = os.path.join('/tmp', filename)

        try:
            if format == 'html':
                html = self.generate_html_report(report_data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
            elif format == 'json':
                # Remove non-serializable objects
                serializable_data = json.loads(
                    json.dumps(report_data, default=str)
                )
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, indent=2)
            elif format == 'txt':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_data.get('narrative', 'No narrative available'))
            else:
                raise ValueError(f"Unsupported format: {format}")

            self.logger.info(f"Report saved to: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    # Create generator
    generator = AIReportGenerator(db_config)

    # Generate report for Vidrio Andino (all available data)
    print("Generating AI report for Vidrio Andino...")
    report = generator.generate_report(
        device_location="Vidrio Andino",
        hours=24,  # Ignored when use_all_data=True
        use_ai=False,  # Set to True to use Claude AI narrative
        use_all_data=True  # Use all historical data (Oct 3-4)
    )

    if 'error' in report:
        print(f"Error: {report['error']}")
    else:
        print(f"\n{'='*80}")
        print("NARRATIVE:")
        print(f"{'='*80}")
        print(report['narrative'])
        print(f"{'='*80}\n")

        # Save reports
        html_path = generator.save_report(report, format='html')
        json_path = generator.save_report(report, format='json')

        print(f"HTML Report: {html_path}")
        print(f"JSON Report: {json_path}")
        print(f"\nTo view HTML report: open {html_path}")
