#!/usr/bin/env python3
"""
AI Reporting API Blueprint
RESTful API for AI narrative report generation

Version: 1.0
Date: October 30, 2025
Author: INSA Automation Corp
"""

from flask import Blueprint, jsonify, request, send_file, g
from functools import wraps
import logging
from datetime import datetime
import os
from ai_report_generator import AIReportGenerator
from typing import Optional

logger = logging.getLogger(__name__)

# Create Blueprint
reporting_bp = Blueprint('reporting', __name__, url_prefix='/api/v1/reports')

# Global generator instance (will be initialized in init_reporting_api)
_report_generator: Optional[AIReportGenerator] = None


def get_report_generator() -> Optional[AIReportGenerator]:
    """Get the global report generator instance"""
    return _report_generator


def init_reporting_api(db_config: dict):
    """
    Initialize the reporting API with database configuration

    Args:
        db_config: Database connection configuration
    """
    global _report_generator
    _report_generator = AIReportGenerator(db_config)
    logger.info("Reporting API initialized")


# Authentication decorator (uses existing JWT from app_advanced.py)
def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via JWT (set by app_advanced.py)
        if not hasattr(g, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@reporting_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Generate AI narrative report on-demand

    Request Body:
    {
        "location": "Vidrio Andino",  // Device location (required)
        "hours": 24,                   // Time window in hours (default: 24)
        "use_ai": true,                // Use AI narrative vs template (default: true)
        "format": "html"               // Output format: html, json, txt (default: html)
    }

    Returns:
        Report data with narrative and download links
    """
    generator = get_report_generator()
    if not generator:
        return jsonify({'error': 'Report generator not initialized'}), 500

    try:
        data = request.get_json() or {}

        # Validate required parameters
        location = data.get('location')
        if not location:
            return jsonify({'error': 'location parameter is required'}), 400

        hours = int(data.get('hours', 24))
        use_ai = data.get('use_ai', True)
        format_type = data.get('format', 'html')

        if hours < 1 or hours > 720:  # Max 30 days
            return jsonify({'error': 'hours must be between 1 and 720'}), 400

        if format_type not in ['html', 'json', 'txt']:
            return jsonify({'error': 'format must be html, json, or txt'}), 400

        # Generate report
        logger.info(f"Generating {format_type} report for {location} ({hours}h)")
        report_data = generator.generate_report(
            device_location=location,
            hours=hours,
            use_ai=use_ai
        )

        if 'error' in report_data:
            return jsonify(report_data), 500

        # Save report file
        filepath = generator.save_report(report_data, format=format_type)
        if not filepath:
            return jsonify({'error': 'Failed to save report file'}), 500

        # Return report data with download link
        response = {
            'success': True,
            'report': {
                'location': report_data['location'],
                'time_window_hours': report_data['time_window_hours'],
                'generated_at': report_data['generated_at'],
                'device_count': report_data['device_count'],
                'sensor_count': len(report_data.get('sensor_stats', {})),
                'anomaly_count': len(report_data.get('anomalies', [])),
                'correlation_count': len(report_data.get('correlations', [])),
                'narrative': report_data.get('narrative', ''),
                'format': format_type,
                'download_path': filepath,
                'filename': os.path.basename(filepath)
            }
        }

        # Include detailed data if JSON format
        if format_type == 'json':
            response['report']['details'] = {
                'sensor_stats': report_data.get('sensor_stats', {}),
                'anomalies': report_data.get('anomalies', []),
                'correlations': report_data.get('correlations', [])
            }

        logger.info(f"Report generated successfully: {filepath}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500


@reporting_bp.route('/download/<filename>', methods=['GET'])
def download_report(filename: str):
    """
    Download a generated report file

    Args:
        filename: Report filename (from /generate endpoint)

    Returns:
        Report file for download
    """
    try:
        filepath = os.path.join('/tmp', filename)

        # Security check: ensure file exists and is a report file
        if not os.path.exists(filepath):
            return jsonify({'error': 'Report file not found'}), 404

        if not filename.startswith('report_'):
            return jsonify({'error': 'Invalid report filename'}), 400

        # Determine mimetype based on extension
        if filename.endswith('.html'):
            mimetype = 'text/html'
        elif filename.endswith('.json'):
            mimetype = 'application/json'
        elif filename.endswith('.txt'):
            mimetype = 'text/plain'
        else:
            mimetype = 'application/octet-stream'

        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({'error': str(e)}), 500


@reporting_bp.route('/templates', methods=['GET'])
def list_report_templates():
    """
    List available report templates

    Returns:
        List of report template configurations
    """
    templates = [
        {
            'id': 'daily_summary',
            'name': 'Daily Operations Summary',
            'description': 'Comprehensive 24-hour operational report with all key metrics',
            'default_hours': 24,
            'default_format': 'html',
            'recommended_schedule': 'daily at 08:00'
        },
        {
            'id': 'shift_report',
            'name': 'Shift Performance Report',
            'description': '8-hour shift report for production handoff',
            'default_hours': 8,
            'default_format': 'html',
            'recommended_schedule': 'every 8 hours'
        },
        {
            'id': 'weekly_executive',
            'name': 'Weekly Executive Summary',
            'description': 'High-level KPIs and trends for management review',
            'default_hours': 168,  # 7 days
            'default_format': 'html',
            'recommended_schedule': 'weekly on Monday at 08:00'
        },
        {
            'id': 'anomaly_alert',
            'name': 'Anomaly Detection Alert',
            'description': 'Real-time alert report when anomalies are detected',
            'default_hours': 1,
            'default_format': 'txt',
            'recommended_schedule': 'on-demand (triggered by anomaly)'
        },
        {
            'id': 'maintenance_forecast',
            'name': 'Predictive Maintenance Forecast',
            'description': 'Equipment health assessment with maintenance predictions',
            'default_hours': 72,  # 3 days
            'default_format': 'html',
            'recommended_schedule': 'daily at 06:00'
        }
    ]

    return jsonify({
        'success': True,
        'templates': templates
    }), 200


@reporting_bp.route('/quick/<template_id>', methods=['POST'])
def generate_from_template(template_id: str):
    """
    Generate report using a predefined template

    Args:
        template_id: Template identifier (daily_summary, shift_report, etc.)

    Request Body:
    {
        "location": "Vidrio Andino"  // Required
    }

    Returns:
        Generated report
    """
    generator = get_report_generator()
    if not generator:
        return jsonify({'error': 'Report generator not initialized'}), 500

    try:
        data = request.get_json() or {}
        location = data.get('location')

        if not location:
            return jsonify({'error': 'location parameter is required'}), 400

        # Template configurations
        templates = {
            'daily_summary': {'hours': 24, 'format': 'html', 'use_ai': True},
            'shift_report': {'hours': 8, 'format': 'html', 'use_ai': True},
            'weekly_executive': {'hours': 168, 'format': 'html', 'use_ai': True},
            'anomaly_alert': {'hours': 1, 'format': 'txt', 'use_ai': False},
            'maintenance_forecast': {'hours': 72, 'format': 'html', 'use_ai': True}
        }

        if template_id not in templates:
            return jsonify({'error': f'Unknown template: {template_id}'}), 400

        template_config = templates[template_id]

        # Generate report with template settings
        logger.info(f"Generating report from template: {template_id}")
        report_data = generator.generate_report(
            device_location=location,
            hours=template_config['hours'],
            use_ai=template_config['use_ai']
        )

        if 'error' in report_data:
            return jsonify(report_data), 500

        # Save report
        filepath = generator.save_report(
            report_data,
            format=template_config['format']
        )

        if not filepath:
            return jsonify({'error': 'Failed to save report file'}), 500

        return jsonify({
            'success': True,
            'template_id': template_id,
            'report': {
                'location': report_data['location'],
                'time_window_hours': report_data['time_window_hours'],
                'generated_at': report_data['generated_at'],
                'narrative': report_data.get('narrative', ''),
                'format': template_config['format'],
                'download_path': filepath,
                'filename': os.path.basename(filepath)
            }
        }), 200

    except Exception as e:
        logger.error(f"Error generating template report: {e}")
        return jsonify({'error': str(e)}), 500


@reporting_bp.route('/status', methods=['GET'])
def get_reporting_status():
    """
    Get reporting system status

    Returns:
        System status and capabilities
    """
    generator = get_report_generator()

    status = {
        'success': True,
        'reporting_engine': {
            'status': 'operational' if generator else 'not_initialized',
            'version': '1.0',
            'capabilities': {
                'ai_narrative': True,
                'template_narrative': True,
                'formats': ['html', 'json', 'txt'],
                'max_time_window_hours': 720,
                'templates': 5
            }
        },
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(status), 200


@reporting_bp.route('/test', methods=['GET'])
def test_report():
    """
    Generate a simple test report (no auth required for testing)

    Query Parameters:
        location: Device location (default: "Vidrio Andino")
        hours: Time window (default: 24)
        all_data: Use all available data (default: false)

    Returns:
        Test report in JSON format
    """
    generator = get_report_generator()
    if not generator:
        return jsonify({'error': 'Report generator not initialized'}), 500

    try:
        location = request.args.get('location', 'Vidrio Andino')
        hours = int(request.args.get('hours', 24))
        use_all_data = request.args.get('all_data', 'false').lower() == 'true'

        if use_all_data:
            logger.info(f"Generating test report for {location} (all available data)")
        else:
            logger.info(f"Generating test report for {location} ({hours}h)")

        report_data = generator.generate_report(
            device_location=location,
            hours=hours,
            use_ai=False,  # Use template for faster testing
            use_all_data=use_all_data
        )

        if 'error' in report_data:
            return jsonify(report_data), 500

        return jsonify({
            'success': True,
            'test_mode': True,
            'report': {
                'location': report_data['location'],
                'time_window_hours': report_data['time_window_hours'],
                'generated_at': report_data['generated_at'],
                'device_count': report_data['device_count'],
                'sensor_count': len(report_data.get('sensor_stats', {})),
                'anomaly_count': len(report_data.get('anomalies', [])),
                'correlation_count': len(report_data.get('correlations', [])),
                'narrative_preview': report_data.get('narrative', '')[:500] + '...'
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in test report: {e}")
        return jsonify({'error': str(e)}), 500


# Error handlers
@reporting_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@reporting_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
