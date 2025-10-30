#!/usr/bin/env python3
"""
Natural Language Query Engine
Translates natural language questions into SQL queries and provides AI-powered answers

Version: 1.0
Date: October 30, 2025
Author: INSA Automation Corp
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class NLQueryEngine:
    """
    Natural Language Query Engine for IoT data

    Features:
    - Natural language to SQL translation
    - Safe query execution (read-only)
    - AI-powered answer generation
    - Context-aware responses
    - Query history and learning
    """

    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize query engine

        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)

        # Query templates for common patterns
        self.query_templates = {
            'sensor_value': """
                SELECT t.timestamp, t.value, t.unit, d.name as device_name, d.location
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE t.key = %s
                ORDER BY t.timestamp DESC
                LIMIT %s
            """,
            'sensor_range': """
                SELECT t.timestamp, t.value, t.unit, d.name as device_name, d.location
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE t.key = %s
                  AND t.timestamp >= %s
                  AND t.timestamp <= %s
                ORDER BY t.timestamp ASC
            """,
            'sensor_stats': """
                SELECT
                    COUNT(*) as count,
                    AVG(CAST(t.value AS FLOAT)) as avg,
                    MIN(CAST(t.value AS FLOAT)) as min,
                    MAX(CAST(t.value AS FLOAT)) as max,
                    STDDEV(CAST(t.value AS FLOAT)) as stddev,
                    d.name as device_name,
                    t.unit
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE t.key = %s
                  AND t.timestamp >= %s
                GROUP BY d.name, t.unit
            """,
            'device_sensors': """
                SELECT DISTINCT t.key, t.unit, COUNT(*) as samples
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.name = %s OR d.id::text = %s
                GROUP BY t.key, t.unit
                ORDER BY samples DESC
            """,
            'location_devices': """
                SELECT id, name, type, status, last_seen
                FROM devices
                WHERE location = %s
                ORDER BY name
            """,
            'anomalies': """
                SELECT ad.*, d.name as device_name, mm.metric_name
                FROM anomaly_detections ad
                LEFT JOIN ml_models mm ON ad.model_id = mm.id
                LEFT JOIN devices d ON mm.device_id::uuid = d.id
                WHERE ad.detected_at >= %s
                  AND ad.is_anomaly = true
                ORDER BY ad.anomaly_score DESC
                LIMIT %s
            """
        }

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

    def extract_intent(self, question: str) -> Dict[str, Any]:
        """
        Extract intent and parameters from natural language question

        Args:
            question: Natural language question

        Returns:
            Dictionary with intent, entities, and parameters
        """
        question_lower = question.lower()

        intent = {
            'type': 'unknown',
            'entities': {},
            'confidence': 0.0,
            'original_question': question
        }

        # Time patterns
        time_patterns = {
            'last hour': timedelta(hours=1),
            'past hour': timedelta(hours=1),
            'last 24 hours': timedelta(hours=24),
            'past 24 hours': timedelta(hours=24),
            'yesterday': timedelta(days=1),
            'last day': timedelta(days=1),
            'last week': timedelta(weeks=1),
            'past week': timedelta(weeks=1),
            'last month': timedelta(days=30),
            'past month': timedelta(days=30),
        }

        # Extract time range
        for pattern, delta in time_patterns.items():
            if pattern in question_lower:
                intent['entities']['time_start'] = datetime.now() - delta
                intent['entities']['time_end'] = datetime.now()
                break

        # Extract sensor numbers (e.g., "sensor 146", "key 147")
        sensor_match = re.search(r'(?:sensor|key)\s+(\d+)', question_lower)
        if sensor_match:
            intent['entities']['sensor_key'] = sensor_match.group(1)

        # Extract device names
        device_match = re.search(r'(?:device|pozo)\s+(\w+)', question_lower)
        if device_match:
            intent['entities']['device_name'] = device_match.group(1)

        # Extract locations
        if 'vidrio andino' in question_lower:
            intent['entities']['location'] = 'Vidrio Andino'

        # Detect query types
        if any(word in question_lower for word in ['average', 'avg', 'mean']):
            intent['type'] = 'statistics'
            intent['confidence'] = 0.8
        elif any(word in question_lower for word in ['maximum', 'max', 'highest', 'peak']):
            intent['type'] = 'statistics'
            intent['entities']['stat_type'] = 'max'
            intent['confidence'] = 0.8
        elif any(word in question_lower for word in ['minimum', 'min', 'lowest']):
            intent['type'] = 'statistics'
            intent['entities']['stat_type'] = 'min'
            intent['confidence'] = 0.8
        elif any(word in question_lower for word in ['show', 'get', 'what is', 'what was']):
            if 'sensor' in question_lower or 'key' in question_lower:
                intent['type'] = 'sensor_value'
                intent['confidence'] = 0.7
            elif 'device' in question_lower:
                intent['type'] = 'device_info'
                intent['confidence'] = 0.7
        elif any(word in question_lower for word in ['anomaly', 'anomalies', 'unusual', 'abnormal']):
            intent['type'] = 'anomalies'
            intent['confidence'] = 0.9
        elif any(word in question_lower for word in ['trend', 'trending', 'pattern']):
            intent['type'] = 'trend_analysis'
            intent['confidence'] = 0.7
        elif any(word in question_lower for word in ['compare', 'comparison', 'difference']):
            intent['type'] = 'comparison'
            intent['confidence'] = 0.7
        elif any(word in question_lower for word in ['list', 'all', 'devices', 'sensors']):
            if 'device' in question_lower:
                intent['type'] = 'list_devices'
                intent['confidence'] = 0.8
            elif 'sensor' in question_lower:
                intent['type'] = 'list_sensors'
                intent['confidence'] = 0.8

        return intent

    def generate_sql(self, intent: Dict[str, Any]) -> tuple[Optional[str], Optional[tuple]]:
        """
        Generate SQL query from intent

        Args:
            intent: Extracted intent dictionary

        Returns:
            Tuple of (SQL query string, parameters tuple)
        """
        query_type = intent['type']
        entities = intent['entities']

        try:
            if query_type == 'sensor_value':
                sensor_key = entities.get('sensor_key')
                if not sensor_key:
                    return None, None

                if 'time_start' in entities:
                    query = self.query_templates['sensor_range']
                    params = (sensor_key, entities['time_start'], entities['time_end'])
                else:
                    query = self.query_templates['sensor_value']
                    params = (sensor_key, 100)  # Default limit

                return query, params

            elif query_type == 'statistics':
                sensor_key = entities.get('sensor_key')
                if not sensor_key:
                    return None, None

                time_start = entities.get('time_start', datetime.now() - timedelta(days=7))
                query = self.query_templates['sensor_stats']
                params = (sensor_key, time_start)

                return query, params

            elif query_type == 'device_info':
                device_name = entities.get('device_name')
                if not device_name:
                    return None, None

                query = self.query_templates['device_sensors']
                params = (device_name, device_name)

                return query, params

            elif query_type == 'list_devices':
                location = entities.get('location')
                if location:
                    query = self.query_templates['location_devices']
                    params = (location,)
                else:
                    query = "SELECT id, name, type, status, location FROM devices ORDER BY name"
                    params = ()

                return query, params

            elif query_type == 'list_sensors':
                device_name = entities.get('device_name')
                if device_name:
                    query = self.query_templates['device_sensors']
                    params = (device_name, device_name)
                else:
                    query = """
                        SELECT DISTINCT t.key, t.unit, d.name as device_name, COUNT(*) as samples
                        FROM telemetry t
                        JOIN devices d ON t.device_id = d.id
                        GROUP BY t.key, t.unit, d.name
                        ORDER BY samples DESC
                        LIMIT 50
                    """
                    params = ()

                return query, params

            elif query_type == 'anomalies':
                time_start = entities.get('time_start', datetime.now() - timedelta(days=7))
                query = self.query_templates['anomalies']
                params = (time_start, 20)

                return query, params

            else:
                self.logger.warning(f"Unknown query type: {query_type}")
                return None, None

        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return None, None

    def execute_query(self, query: str, params: tuple) -> Optional[List[Dict]]:
        """
        Execute SQL query safely (read-only)

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result dictionaries or None if error
        """
        # Safety check: ensure query is read-only
        query_upper = query.upper().strip()
        if not query_upper.startswith('SELECT'):
            self.logger.error("Only SELECT queries are allowed")
            return None

        # Forbidden keywords
        forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        if any(keyword in query_upper for keyword in forbidden):
            self.logger.error("Query contains forbidden keywords")
            return None

        conn = self._get_db_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            results = cur.fetchall()

            # Convert to list of dicts
            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return None
        finally:
            conn.close()

    def generate_answer_with_ai(self, question: str, intent: Dict[str, Any],
                               results: List[Dict]) -> str:
        """
        Generate natural language answer using Claude Code subprocess

        Args:
            question: Original question
            intent: Extracted intent
            results: Query results

        Returns:
            Natural language answer
        """
        try:
            # Prepare context for Claude
            context = {
                'question': question,
                'intent_type': intent['type'],
                'entities': intent['entities'],
                'result_count': len(results),
                'results_preview': results[:5] if results else []  # First 5 results
            }

            prompt = f"""You are an IoT data analyst for a glass manufacturing plant (Vidrio Andino).

A user asked: "{question}"

Query results ({len(results)} rows):
{json.dumps(results[:10], indent=2, default=str)}

Generate a concise, natural language answer that:
1. Directly answers the user's question
2. Highlights key findings or numbers
3. Provides context for glass manufacturing
4. Mentions any anomalies or interesting patterns
5. Uses simple language (2-3 sentences max)

Answer:"""

            # Use Claude Code subprocess (zero API cost)
            process = subprocess.Popen(
                ['claude', '--no-color'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=prompt, timeout=30)

            if process.returncode == 0 and stdout.strip():
                return stdout.strip()
            else:
                # Fallback to template answer
                return self._generate_template_answer(question, intent, results)

        except Exception as e:
            self.logger.error(f"Error generating AI answer: {e}")
            return self._generate_template_answer(question, intent, results)

    def _generate_template_answer(self, question: str, intent: Dict[str, Any],
                                  results: List[Dict]) -> str:
        """
        Generate template-based answer when AI is not available

        Args:
            question: Original question
            intent: Extracted intent
            results: Query results

        Returns:
            Template-based answer
        """
        if not results:
            return f"I couldn't find any data matching your question: '{question}'"

        query_type = intent['type']
        entities = intent['entities']

        if query_type == 'sensor_value':
            sensor_key = entities.get('sensor_key', 'unknown')
            latest = results[0]
            value = latest.get('value', 'N/A')
            unit = latest.get('unit', '')
            device = latest.get('device_name', 'Unknown device')
            timestamp = latest.get('timestamp', 'Unknown time')

            return f"Sensor {sensor_key} on {device} is currently {value} {unit} (as of {timestamp}). I found {len(results)} data points."

        elif query_type == 'statistics':
            stats = results[0]
            sensor_key = entities.get('sensor_key', 'unknown')
            avg = stats.get('avg', 0)
            min_val = stats.get('min', 0)
            max_val = stats.get('max', 0)
            count = stats.get('count', 0)
            unit = stats.get('unit', '')

            return f"Sensor {sensor_key} statistics: Average {avg:.2f} {unit}, Range {min_val:.2f} - {max_val:.2f} {unit}, {count} samples analyzed."

        elif query_type == 'list_devices':
            device_names = [r.get('name', 'Unknown') for r in results[:5]]
            total = len(results)
            location = entities.get('location', 'the system')

            if total <= 5:
                return f"I found {total} devices in {location}: {', '.join(device_names)}."
            else:
                return f"I found {total} devices in {location}. Top 5: {', '.join(device_names)}."

        elif query_type == 'list_sensors':
            sensor_keys = [r.get('key', 'Unknown') for r in results[:5]]
            total = len(results)

            if total <= 5:
                return f"I found {total} sensors: {', '.join(sensor_keys)}."
            else:
                return f"I found {total} sensors. Top 5: {', '.join(sensor_keys)}."

        elif query_type == 'anomalies':
            anomaly_count = len(results)
            if anomaly_count == 0:
                return "No anomalies detected in the specified time period. All systems operating normally."
            else:
                top_anomaly = results[0]
                device = top_anomaly.get('device_name', 'Unknown device')
                score = top_anomaly.get('anomaly_score', 0)
                return f"I found {anomaly_count} anomalies. Highest severity: {device} (score: {score:.2f})."

        else:
            return f"I found {len(results)} results for your question: '{question}'"

    def query(self, question: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        Process natural language question and return answer

        Args:
            question: Natural language question
            use_ai: Whether to use AI for answer generation

        Returns:
            Dictionary with question, intent, results, answer, and metadata
        """
        self.logger.info(f"Processing query: {question}")

        # Extract intent
        intent = self.extract_intent(question)

        if intent['type'] == 'unknown' or intent['confidence'] < 0.5:
            return {
                'question': question,
                'intent': intent,
                'error': 'Could not understand the question. Try rephrasing.',
                'suggestions': [
                    'Show me sensor 146 values',
                    'What is the average temperature for sensor 80?',
                    'List all devices in Vidrio Andino',
                    'Show me anomalies from the last week'
                ]
            }

        # Generate SQL
        sql, params = self.generate_sql(intent)
        if not sql:
            return {
                'question': question,
                'intent': intent,
                'error': 'Could not generate query. Missing required information.',
                'suggestions': [
                    'Specify a sensor number (e.g., sensor 146)',
                    'Specify a device name (e.g., Pozo3)',
                    'Specify a time range (e.g., last 24 hours)'
                ]
            }

        # Execute query
        results = self.execute_query(sql, params)
        if results is None:
            return {
                'question': question,
                'intent': intent,
                'error': 'Query execution failed. Please try again.',
                'sql': sql
            }

        # Generate answer
        if use_ai:
            answer = self.generate_answer_with_ai(question, intent, results)
        else:
            answer = self._generate_template_answer(question, intent, results)

        return {
            'question': question,
            'intent': intent,
            'sql': sql,
            'result_count': len(results),
            'results': results[:20],  # Return first 20 results
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }


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

    # Create engine
    engine = NLQueryEngine(db_config)

    # Test queries
    test_questions = [
        "What is the current value of sensor 146?",
        "Show me the average temperature for sensor 80 in the last week",
        "List all devices in Vidrio Andino",
        "What anomalies were detected in the past 24 hours?",
        "Show me sensor 147 values",
    ]

    print("=" * 80)
    print("Natural Language Query Engine - Test Suite")
    print("=" * 80)

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 80)

        result = engine.query(question, use_ai=False)  # Use template for faster testing

        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            if 'suggestions' in result:
                print(f"Suggestions: {', '.join(result['suggestions'])}")
        else:
            print(f"✅ Intent: {result['intent']['type']}")
            print(f"📊 Results: {result['result_count']} rows")
            print(f"💬 Answer: {result['answer']}")

        print("=" * 80)
