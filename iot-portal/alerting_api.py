#!/usr/bin/env python3
"""
Advanced Alerting API Endpoints
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8

Provides REST API access to:
- Alert state management (acknowledge, investigate, resolve)
- SLA tracking and compliance
- Escalation policies
- On-call rotation schedules
- Alert grouping statistics

Author: INSA Automation Corp
Date: October 28, 2025
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
import logging
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional, Any

# Import our alerting modules
from alert_state_machine import AlertStateMachine, InvalidStateTransition
from sla_tracking import SLATracker, SLAIntegratedStateMachine
from escalation_engine import EscalationEngine, EscalationException
from on_call_manager import OnCallManager, OnCallException
from alert_grouping import AlertGroupManager, AlertGroupException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
alerting_api = Blueprint('alerting_api', __name__, url_prefix='/api/v1')

# Database configuration (will be passed from main app)
DB_CONFIG = None

def init_alerting_api(db_config: Dict[str, Any]):
    """
    Initialize alerting API with database configuration.

    Args:
        db_config: Database configuration dictionary
    """
    global DB_CONFIG
    DB_CONFIG = db_config
    logger.info("Alerting API initialized with database configuration")


# =============================================================================
# Endpoint 1: Create Alert
# =============================================================================

@alerting_api.route('/alerts', methods=['POST'])
@jwt_required()
def create_alert():
    """
    Create new alert
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - device_id
            - rule_id
            - severity
            - message
          properties:
            device_id:
              type: string
              description: Device UUID
            rule_id:
              type: string
              description: Rule UUID
            severity:
              type: string
              enum: [critical, high, medium, low, info]
            message:
              type: string
            value:
              type: number
              description: Metric value that triggered alert
            threshold:
              type: number
              description: Threshold that was exceeded
    responses:
      201:
        description: Alert created successfully
        schema:
          type: object
          properties:
            alert_id:
              type: string
            state:
              type: string
            sla_status:
              type: object
            group_id:
              type: string
      400:
        description: Invalid request data
      500:
        description: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['device_id', 'rule_id', 'severity', 'message']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing
            }), 400

        # Validate severity
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if data['severity'] not in valid_severities:
            return jsonify({
                'error': 'Invalid severity',
                'valid_values': valid_severities
            }), 400

        # Create alert in database
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                alert_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO alerts (
                        id, device_id, rule_id, severity, message,
                        value, threshold, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
                    RETURNING id, created_at
                """, (
                    alert_id,
                    data['device_id'],
                    data['rule_id'],
                    data['severity'],
                    data['message'],
                    data.get('value'),
                    data.get('threshold')
                ))

                result = cursor.fetchone()
            conn.commit()

            # Get initial state (auto-created by trigger)
            with AlertStateMachine(DB_CONFIG) as state_machine:
                state = state_machine.get_current_state(alert_id)

            # Get SLA status (auto-created by trigger)
            with SLATracker(DB_CONFIG) as sla_tracker:
                sla_status = sla_tracker.get_sla_status(alert_id)

            # Add to alert group
            with AlertGroupManager(DB_CONFIG) as group_manager:
                group_id = group_manager.find_or_create_group(
                    device_id=data['device_id'],
                    rule_id=data['rule_id'],
                    severity=data['severity'],
                    alert_id=alert_id
                )

            return jsonify({
                'alert_id': alert_id,
                'created_at': result['created_at'].isoformat(),
                'state': state['state'],
                'sla_status': {
                    'tta_target_minutes': sla_status['tta_target_minutes'],
                    'ttr_target_minutes': sla_status['ttr_target_minutes'],
                    'tta_breached': sla_status['tta_breached'],
                    'ttr_breached': sla_status['ttr_breached']
                },
                'group_id': group_id
            }), 201

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 2: Get Alert Details
# =============================================================================

@alerting_api.route('/alerts/<alert_id>', methods=['GET'])
@jwt_required()
def get_alert(alert_id):
    """
    Get alert details including state, SLA, and escalation status
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: string
        description: Alert UUID
    responses:
      200:
        description: Alert details
      404:
        description: Alert not found
      500:
        description: Server error
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        a.*,
                        d.name as device_name,
                        r.name as rule_name
                    FROM alerts a
                    LEFT JOIN devices d ON a.device_id = d.id
                    LEFT JOIN rules r ON a.rule_id = r.id
                    WHERE a.id = %s
                """, (alert_id,))

                alert = cursor.fetchone()
                if not alert:
                    return jsonify({'error': 'Alert not found'}), 404

            # Get state history
            with AlertStateMachine(DB_CONFIG) as state_machine:
                state_history = state_machine.get_state_history(alert_id)

            # Get SLA status
            with SLATracker(DB_CONFIG) as sla_tracker:
                sla_status = sla_tracker.get_sla_status(alert_id)

            # Get escalation status
            with EscalationEngine(DB_CONFIG) as escalation_engine:
                escalation_status = escalation_engine.get_escalation_status(alert_id)

            return jsonify({
                'alert': dict(alert),
                'state_history': state_history,
                'sla_status': sla_status,
                'escalation_status': escalation_status
            }), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 3: List Alerts
# =============================================================================

@alerting_api.route('/alerts', methods=['GET'])
@jwt_required()
def list_alerts():
    """
    List alerts with optional filters
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: query
        name: severity
        type: string
        enum: [critical, high, medium, low, info]
      - in: query
        name: status
        type: string
        enum: [active, acknowledged, resolved]
      - in: query
        name: device_id
        type: string
      - in: query
        name: limit
        type: integer
        default: 50
      - in: query
        name: offset
        type: integer
        default: 0
    responses:
      200:
        description: List of alerts
      500:
        description: Server error
    """
    try:
        # Get query parameters
        severity = request.args.get('severity')
        status = request.args.get('status')
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query
                query = """
                    SELECT
                        a.*,
                        d.name as device_name,
                        r.name as rule_name
                    FROM alerts a
                    LEFT JOIN devices d ON a.device_id = d.id
                    LEFT JOIN rules r ON a.rule_id = r.id
                    WHERE 1=1
                """
                params = []

                if severity:
                    query += " AND a.severity = %s"
                    params.append(severity)

                if status:
                    query += " AND a.status = %s"
                    params.append(status)

                if device_id:
                    query += " AND a.device_id = %s"
                    params.append(device_id)

                query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cursor.execute(query, params)
                alerts = cursor.fetchall()

                # Get total count
                count_query = """
                    SELECT COUNT(*) as total FROM alerts a WHERE 1=1
                """
                count_params = []

                if severity:
                    count_query += " AND a.severity = %s"
                    count_params.append(severity)

                if status:
                    count_query += " AND a.status = %s"
                    count_params.append(status)

                if device_id:
                    count_query += " AND a.device_id = %s"
                    count_params.append(device_id)

                cursor.execute(count_query, count_params)
                total = cursor.fetchone()['total']

            return jsonify({
                'alerts': [dict(a) for a in alerts],
                'total': total,
                'limit': limit,
                'offset': offset
            }), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 4: Acknowledge Alert
# =============================================================================

@alerting_api.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alert(alert_id):
    """
    Acknowledge alert (updates state and calculates TTA)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            notes:
              type: string
    responses:
      200:
        description: Alert acknowledged
      500:
        description: Server error
    """
    try:
        data = request.get_json() or {}
        user_id = get_jwt_identity()

        # Use integrated state machine (auto-updates SLA)
        with SLAIntegratedStateMachine(DB_CONFIG) as machine:
            result = machine.acknowledge(
                alert_id=alert_id,
                user_id=user_id,
                notes=data.get('notes', 'Alert acknowledged via API')
            )

        return jsonify({
            'state': result['state'],
            'tta_minutes': result.get('tta_minutes'),
            'tta_breached': result.get('tta_breached'),
            'acknowledged_at': result['changed_at'].isoformat()
        }), 200

    except InvalidStateTransition as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 5: Start Investigation
# =============================================================================

@alerting_api.route('/alerts/<alert_id>/investigate', methods=['POST'])
@jwt_required()
def investigate_alert(alert_id):
    """
    Start alert investigation
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            notes:
              type: string
    responses:
      200:
        description: Investigation started
      500:
        description: Server error
    """
    try:
        data = request.get_json() or {}
        user_id = get_jwt_identity()

        with SLAIntegratedStateMachine(DB_CONFIG) as machine:
            result = machine.start_investigation(
                alert_id=alert_id,
                user_id=user_id,
                notes=data.get('notes', 'Investigation started via API')
            )

        return jsonify({
            'state': result['state'],
            'started_at': result['changed_at'].isoformat()
        }), 200

    except InvalidStateTransition as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting investigation: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 6: Resolve Alert
# =============================================================================

@alerting_api.route('/alerts/<alert_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    """
    Resolve alert (updates state and calculates TTR)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            notes:
              type: string
    responses:
      200:
        description: Alert resolved
      500:
        description: Server error
    """
    try:
        data = request.get_json() or {}
        user_id = get_jwt_identity()

        with SLAIntegratedStateMachine(DB_CONFIG) as machine:
            result = machine.resolve(
                alert_id=alert_id,
                user_id=user_id,
                notes=data.get('notes', 'Alert resolved via API')
            )

        return jsonify({
            'state': result['state'],
            'ttr_minutes': result.get('ttr_minutes'),
            'ttr_breached': result.get('ttr_breached'),
            'resolved_at': result['changed_at'].isoformat()
        }), 200

    except InvalidStateTransition as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 7: List Escalation Policies
# =============================================================================

@alerting_api.route('/escalation-policies', methods=['GET'])
@jwt_required()
def list_escalation_policies():
    """
    List escalation policies
    ---
    tags:
      - Escalation
    security:
      - Bearer: []
    parameters:
      - in: query
        name: severity
        type: string
      - in: query
        name: enabled
        type: boolean
    responses:
      200:
        description: List of policies
      500:
        description: Server error
    """
    try:
        severity = request.args.get('severity')
        enabled = request.args.get('enabled', 'true').lower() == 'true'

        with EscalationEngine(DB_CONFIG) as engine:
            policies = engine.list_policies(enabled_only=enabled)

            # Filter by severity if specified
            if severity:
                policies = [p for p in policies if severity in p.get('severities', [])]

            return jsonify({
                'policies': policies,
                'total': len(policies)
            }), 200

    except Exception as e:
        logger.error(f"Error listing policies: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 8: Create Escalation Policy
# =============================================================================

@alerting_api.route('/escalation-policies', methods=['POST'])
@jwt_required()
def create_escalation_policy():
    """
    Create new escalation policy
    ---
    tags:
      - Escalation
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - severities
            - rules
          properties:
            name:
              type: string
            description:
              type: string
            severities:
              type: array
              items:
                type: string
            rules:
              type: object
              description: Escalation tiers configuration
    responses:
      201:
        description: Policy created
      400:
        description: Invalid request
      500:
        description: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['name', 'severities', 'rules']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing
            }), 400

        with EscalationEngine(DB_CONFIG) as engine:
            policy_id = engine.create_policy(
                name=data['name'],
                severities=data['severities'],
                rules=data['rules'],
                description=data.get('description')
            )

            policy = engine.get_policy(policy_id)

        return jsonify({
            'policy_id': policy_id,
            'policy': policy
        }), 201

    except Exception as e:
        logger.error(f"Error creating policy: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 9: Get Current On-Call User
# =============================================================================

@alerting_api.route('/on-call/current', methods=['GET'])
@jwt_required()
def get_current_on_call():
    """
    Get current on-call user for a schedule
    ---
    tags:
      - On-Call
    security:
      - Bearer: []
    parameters:
      - in: query
        name: schedule_id
        required: true
        type: string
    responses:
      200:
        description: Current on-call user
      404:
        description: Schedule not found
      500:
        description: Server error
    """
    try:
        schedule_id = request.args.get('schedule_id')
        if not schedule_id:
            return jsonify({'error': 'schedule_id is required'}), 400

        with OnCallManager(DB_CONFIG) as manager:
            on_call = manager.get_current_on_call(schedule_id)

        return jsonify(on_call), 200

    except OnCallException as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting current on-call: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 10: List On-Call Schedules
# =============================================================================

@alerting_api.route('/on-call/schedules', methods=['GET'])
@jwt_required()
def list_on_call_schedules():
    """
    List on-call schedules
    ---
    tags:
      - On-Call
    security:
      - Bearer: []
    parameters:
      - in: query
        name: enabled
        type: boolean
        default: true
    responses:
      200:
        description: List of schedules
      500:
        description: Server error
    """
    try:
        enabled = request.args.get('enabled', 'true').lower() == 'true'

        with OnCallManager(DB_CONFIG) as manager:
            schedules = manager.list_schedules(enabled_only=enabled)

        return jsonify({
            'schedules': schedules,
            'total': len(schedules)
        }), 200

    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 11: List Alert Groups
# =============================================================================

@alerting_api.route('/groups', methods=['GET'])
@jwt_required()
def list_alert_groups():
    """
    List alert groups
    ---
    tags:
      - Groups
    security:
      - Bearer: []
    parameters:
      - in: query
        name: device_id
        type: string
      - in: query
        name: severity
        type: string
      - in: query
        name: limit
        type: integer
        default: 100
    responses:
      200:
        description: List of alert groups
      500:
        description: Server error
    """
    try:
        device_id = request.args.get('device_id')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))

        with AlertGroupManager(DB_CONFIG) as manager:
            groups = manager.get_active_groups(
                device_id=device_id,
                severity=severity,
                limit=limit
            )

        return jsonify({
            'groups': groups,
            'total': len(groups)
        }), 200

    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Endpoint 12: Get Alert Group Statistics
# =============================================================================

@alerting_api.route('/groups/stats', methods=['GET'])
@jwt_required()
def get_group_statistics():
    """
    Get platform-wide alert grouping statistics
    ---
    tags:
      - Groups
    security:
      - Bearer: []
    responses:
      200:
        description: Grouping statistics
        schema:
          type: object
          properties:
            total_groups:
              type: integer
            active_groups:
              type: integer
            closed_groups:
              type: integer
            total_alerts_grouped:
              type: integer
            avg_alerts_per_group:
              type: number
            max_alerts_in_group:
              type: integer
            overall_noise_reduction_pct:
              type: number
      500:
        description: Server error
    """
    try:
        with AlertGroupManager(DB_CONFIG) as manager:
            stats = manager.get_overall_statistics()

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting group statistics: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Health Check Endpoint
# =============================================================================

@alerting_api.route('/alerting/health', methods=['GET'])
def alerting_health():
    """
    Health check for alerting system
    ---
    tags:
      - Health
    responses:
      200:
        description: Alerting system health status
    """
    try:
        # Test database connectivity
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()

        return jsonify({
            'status': 'healthy',
            'modules': {
                'state_machine': 'ok',
                'sla_tracking': 'ok',
                'escalation_engine': 'ok',
                'on_call_manager': 'ok',
                'alert_grouping': 'ok'
            },
            'database': 'connected'
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# =============================================================================
# Export Blueprint
# =============================================================================

__all__ = ['alerting_api', 'init_alerting_api']
