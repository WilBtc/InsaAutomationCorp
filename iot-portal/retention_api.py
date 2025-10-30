#!/usr/bin/env python3
"""
Data Retention API
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 7

Provides REST API endpoints for data retention policy management.

Endpoints:
- GET /api/v1/retention/policies - List all retention policies
- GET /api/v1/retention/policies/{id} - Get specific policy
- POST /api/v1/retention/policies/{id}/execute - Execute retention policy
- GET /api/v1/retention/executions - Get execution history
- GET /api/v1/retention/archives - Get archived data index
- GET /api/v1/retention/stats/{id} - Get policy statistics

Author: INSA Automation Corp
Date: October 28, 2025
"""

from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from typing import Dict, Any

from retention_manager import RetentionManager, RetentionManagerException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint for retention routes
retention_bp = Blueprint('retention', __name__, url_prefix='/api/v1/retention')

# Database configuration (will be imported from app config)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_iiot',
    'user': 'iiot_user',
    'password': 'iiot_secure_2025'
}


def handle_errors(f):
    """Decorator to handle common errors in retention endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except RetentionManagerException as e:
            logger.error(f"Retention error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    return decorated_function


# =============================================================================
# Policy Management Endpoints
# =============================================================================

@retention_bp.route('/policies', methods=['GET'])
@handle_errors
def list_policies():
    """
    List all retention policies.

    Query Parameters:
    - enabled_only: bool (default: true) - Only return enabled policies

    Returns:
        {
            "success": true,
            "policies": [
                {
                    "id": "uuid",
                    "name": "Telemetry Data - 90 Days",
                    "data_type": "telemetry",
                    "retention_days": 90,
                    "enabled": true,
                    ...
                }
            ],
            "count": 4
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: enabled_only
        in: query
        type: boolean
        default: true
        description: Only return enabled policies
    responses:
      200:
        description: List of retention policies
    """
    enabled_only = request.args.get('enabled_only', 'true').lower() == 'true'

    with RetentionManager(DB_CONFIG) as manager:
        policies = manager.list_policies(enabled_only=enabled_only)

    return jsonify({
        'success': True,
        'policies': policies,
        'count': len(policies)
    })


@retention_bp.route('/policies/<policy_id>', methods=['GET'])
@handle_errors
def get_policy(policy_id):
    """
    Get a specific retention policy.

    Path Parameters:
    - policy_id: UUID of the policy

    Returns:
        {
            "success": true,
            "policy": {
                "id": "uuid",
                "name": "Telemetry Data - 90 Days",
                "data_type": "telemetry",
                "retention_days": 90,
                ...
            }
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: policy_id
        in: path
        type: string
        required: true
        description: UUID of the retention policy
    responses:
      200:
        description: Retention policy details
      404:
        description: Policy not found
    """
    with RetentionManager(DB_CONFIG) as manager:
        policy = manager.get_policy(policy_id)

    if not policy:
        return jsonify({
            'success': False,
            'error': f'Policy not found: {policy_id}'
        }), 404

    return jsonify({
        'success': True,
        'policy': policy
    })


# =============================================================================
# Policy Execution Endpoints
# =============================================================================

@retention_bp.route('/policies/<policy_id>/execute', methods=['POST'])
@handle_errors
def execute_policy(policy_id):
    """
    Execute a retention policy.

    Path Parameters:
    - policy_id: UUID of the policy

    Request Body:
        {
            "dry_run": false  // Optional, default: false
        }

    Returns:
        {
            "success": true,
            "execution": {
                "execution_id": "uuid",
                "policy_id": "uuid",
                "policy_name": "Telemetry Data - 90 Days",
                "status": "success",
                "dry_run": false,
                "records_deleted": 1234,
                "records_archived": 1234,
                "bytes_freed": 246800
            }
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: policy_id
        in: path
        type: string
        required: true
        description: UUID of the retention policy
      - name: body
        in: body
        schema:
          type: object
          properties:
            dry_run:
              type: boolean
              default: false
              description: If true, simulate execution without deleting data
    responses:
      200:
        description: Execution completed successfully
      400:
        description: Invalid request or policy disabled
      404:
        description: Policy not found
    """
    data = request.get_json() or {}
    dry_run = data.get('dry_run', False)

    with RetentionManager(DB_CONFIG) as manager:
        result = manager.execute_policy(policy_id, dry_run=dry_run)

    return jsonify({
        'success': True,
        'execution': result
    })


@retention_bp.route('/executions', methods=['GET'])
@handle_errors
def get_executions():
    """
    Get retention policy execution history.

    Query Parameters:
    - policy_id: UUID (optional) - Filter by policy
    - limit: int (default: 50) - Maximum number of results

    Returns:
        {
            "success": true,
            "executions": [
                {
                    "id": "uuid",
                    "policy_id": "uuid",
                    "policy_name": "Telemetry Data - 90 Days",
                    "started_at": "2025-10-28T12:00:00",
                    "completed_at": "2025-10-28T12:01:30",
                    "duration_seconds": 90,
                    "status": "success",
                    "records_deleted": 1234,
                    "records_archived": 1234,
                    "bytes_freed": 246800,
                    ...
                }
            ],
            "count": 10
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: policy_id
        in: query
        type: string
        description: Filter by policy UUID
      - name: limit
        in: query
        type: integer
        default: 50
        description: Maximum number of results
    responses:
      200:
        description: List of execution records
    """
    policy_id = request.args.get('policy_id')
    limit = int(request.args.get('limit', 50))

    with RetentionManager(DB_CONFIG) as manager:
        executions = manager.get_execution_history(policy_id=policy_id, limit=limit)

    return jsonify({
        'success': True,
        'executions': executions,
        'count': len(executions)
    })


# =============================================================================
# Archive Management Endpoints
# =============================================================================

@retention_bp.route('/archives', methods=['GET'])
@handle_errors
def get_archives():
    """
    Get archived data index.

    Query Parameters:
    - data_type: string (optional) - Filter by data type (telemetry, alerts, etc.)
    - limit: int (default: 100) - Maximum number of results

    Returns:
        {
            "success": true,
            "archives": [
                {
                    "id": "uuid",
                    "policy_id": "uuid",
                    "execution_id": "uuid",
                    "data_type": "telemetry",
                    "archive_path": "/tmp/insa-iiot/archives/telemetry/...",
                    "archive_format": "jsonl",
                    "compression": "gzip",
                    "data_start_date": "2025-01-01T00:00:00",
                    "data_end_date": "2025-07-01T00:00:00",
                    "record_count": 1234,
                    "file_size_bytes": 45678,
                    "checksum": "sha256...",
                    "archived_at": "2025-10-28T12:00:00"
                }
            ],
            "count": 25,
            "total_size_bytes": 1234567,
            "total_records": 50000
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: data_type
        in: query
        type: string
        description: Filter by data type (telemetry, alerts, audit_logs, ml_anomalies)
      - name: limit
        in: query
        type: integer
        default: 100
        description: Maximum number of results
    responses:
      200:
        description: List of archived data files
    """
    data_type = request.args.get('data_type')
    limit = int(request.args.get('limit', 100))

    with RetentionManager(DB_CONFIG) as manager:
        archives = manager.get_archived_data_index(data_type=data_type, limit=limit)

    # Calculate totals
    total_size = sum(a['file_size_bytes'] for a in archives if a.get('file_size_bytes'))
    total_records = sum(a['record_count'] for a in archives if a.get('record_count'))

    return jsonify({
        'success': True,
        'archives': archives,
        'count': len(archives),
        'total_size_bytes': total_size,
        'total_records': total_records
    })


# =============================================================================
# Statistics Endpoints
# =============================================================================

@retention_bp.route('/stats/<policy_id>', methods=['GET'])
@handle_errors
def get_policy_stats(policy_id):
    """
    Get retention policy statistics.

    Path Parameters:
    - policy_id: UUID of the policy

    Returns:
        {
            "success": true,
            "stats": {
                "policy_id": "uuid",
                "policy_name": "Telemetry Data - 90 Days",
                "total_executions": 45,
                "successful_executions": 44,
                "failed_executions": 1,
                "total_records_deleted": 1234567,
                "total_records_archived": 1234567,
                "total_bytes_freed": 246913400,
                "avg_execution_time_seconds": 87.5,
                "last_execution_at": "2025-10-28T12:00:00",
                "last_execution_status": "success"
            }
        }
    ---
    tags:
      - Data Retention
    parameters:
      - name: policy_id
        in: path
        type: string
        required: true
        description: UUID of the retention policy
    responses:
      200:
        description: Policy statistics
      404:
        description: Policy not found
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    # Get policy details
    with RetentionManager(DB_CONFIG) as manager:
        policy = manager.get_policy(policy_id)

    if not policy:
        return jsonify({
            'success': False,
            'error': f'Policy not found: {policy_id}'
        }), 404

    # Get statistics from database function
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM get_retention_policy_stats(%s)", (policy_id,))
            stats = cursor.fetchone()

        if stats:
            stats = dict(stats)
            stats['policy_id'] = policy_id
            stats['policy_name'] = policy['name']
        else:
            stats = {
                'policy_id': policy_id,
                'policy_name': policy['name'],
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_records_deleted': 0,
                'total_records_archived': 0,
                'total_bytes_freed': 0,
                'avg_execution_time_seconds': 0
            }
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'stats': stats
    })


# =============================================================================
# Health Check Endpoint
# =============================================================================

@retention_bp.route('/health', methods=['GET'])
def health_check():
    """
    Retention service health check.

    Returns:
        {
            "success": true,
            "service": "retention",
            "status": "healthy",
            "database": "connected",
            "archive_path": "/tmp/insa-iiot/archives"
        }
    ---
    tags:
      - Data Retention
    responses:
      200:
        description: Service is healthy
    """
    try:
        # Test database connection
        with RetentionManager(DB_CONFIG) as manager:
            policies = manager.list_policies()
            db_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "error"

    return jsonify({
        'success': True,
        'service': 'retention',
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'database': db_status,
        'archive_path': '/tmp/insa-iiot/archives',
        'policies_count': len(policies) if db_status == 'connected' else 0
    })


# =============================================================================
# Blueprint Registration Helper
# =============================================================================

def register_retention_routes(app):
    """
    Register retention API routes with the Flask app.

    Usage:
        from retention_api import register_retention_routes
        register_retention_routes(app)
    """
    app.register_blueprint(retention_bp)
    logger.info("Retention API routes registered")


# =============================================================================
# Standalone Testing
# =============================================================================

if __name__ == '__main__':
    from flask import Flask

    app = Flask(__name__)
    register_retention_routes(app)

    print("=== Data Retention API ===")
    print("\nAvailable endpoints:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('retention'):
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"  {methods:6} {rule.rule}")

    print("\n✓ Retention API ready")
    print("\nTo test:")
    print("  python3 -c 'from retention_api import retention_bp; print(retention_bp)'")
