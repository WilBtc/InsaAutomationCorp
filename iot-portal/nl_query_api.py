#!/usr/bin/env python3
"""
Natural Language Query API Blueprint
REST API for natural language queries on IoT data

Version: 1.0
Date: October 30, 2025
Author: INSA Automation Corp
"""

from flask import Blueprint, jsonify, request, g
from functools import wraps
import logging
from datetime import datetime
from nl_query_engine import NLQueryEngine
from typing import Optional

logger = logging.getLogger(__name__)

# Create Blueprint
nl_query_bp = Blueprint('nl_query', __name__, url_prefix='/api/v1/query')

# Global engine instance (will be initialized in init_nl_query_api)
_query_engine: Optional[NLQueryEngine] = None
_query_history = []  # In-memory history (could be moved to database)


def get_query_engine() -> Optional[NLQueryEngine]:
    """Get the global query engine instance"""
    return _query_engine


def init_nl_query_api(db_config: dict, lstm_forecaster=None):
    """
    Initialize the NL query API with database configuration

    Args:
        db_config: Database connection configuration
        lstm_forecaster: Optional LSTMForecaster instance for predictions
    """
    global _query_engine
    _query_engine = NLQueryEngine(db_config, lstm_forecaster)
    logger.info("Natural Language Query API initialized")
    if lstm_forecaster:
        logger.info("✅ LSTM forecasting enabled for NL queries")


@nl_query_bp.route('/ask', methods=['POST'])
def ask_question():
    """
    Ask a natural language question about IoT data

    Request Body:
    {
        "question": "What is the temperature of sensor 146?",
        "use_ai": true  // Optional, default: true
    }

    Returns:
        Natural language answer with query results
    """
    engine = get_query_engine()
    if not engine:
        return jsonify({'error': 'Query engine not initialized'}), 500

    try:
        data = request.get_json() or {}

        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'question parameter is required'}), 400

        use_ai = data.get('use_ai', True)

        logger.info(f"Processing question: {question}")

        # Process query
        result = engine.query(question, use_ai=use_ai)

        # Store in history
        history_entry = {
            'id': len(_query_history) + 1,
            'question': question,
            'answer': result.get('answer', 'No answer generated'),
            'intent': result.get('intent', {}),
            'result_count': result.get('result_count', 0),
            'timestamp': datetime.now().isoformat(),
            'has_error': 'error' in result
        }
        _query_history.append(history_entry)

        # Return result
        response = {
            'success': 'error' not in result,
            'question': question,
            'answer': result.get('answer'),
            'intent': result.get('intent', {}),
            'result_count': result.get('result_count', 0),
            'results': result.get('results', []),
            'timestamp': result.get('timestamp'),
            'query_id': history_entry['id']
        }

        if 'error' in result:
            response['error'] = result['error']
            response['suggestions'] = result.get('suggestions', [])

        if 'sql' in result:
            response['sql'] = result['sql']  # For debugging/transparency

        logger.info(f"Query processed successfully: {result.get('result_count', 0)} results")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return jsonify({'error': str(e)}), 500


@nl_query_bp.route('/history', methods=['GET'])
def get_history():
    """
    Get query history

    Query Parameters:
        limit: Maximum number of entries to return (default: 20)

    Returns:
        List of recent queries
    """
    try:
        limit = int(request.args.get('limit', 20))

        # Return most recent first
        recent_history = list(reversed(_query_history[-limit:]))

        return jsonify({
            'success': True,
            'history': recent_history,
            'total_count': len(_query_history)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({'error': str(e)}), 500


@nl_query_bp.route('/history/<int:query_id>', methods=['GET'])
def get_query_by_id(query_id: int):
    """
    Get specific query from history

    Args:
        query_id: Query ID from history

    Returns:
        Query details
    """
    try:
        # Find query in history
        query = next((q for q in _query_history if q['id'] == query_id), None)

        if not query:
            return jsonify({'error': 'Query not found'}), 404

        return jsonify({
            'success': True,
            'query': query
        }), 200

    except Exception as e:
        logger.error(f"Error fetching query: {e}")
        return jsonify({'error': str(e)}), 500


@nl_query_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get example questions/suggestions

    Returns:
        List of example questions
    """
    suggestions = {
        'sensor_queries': [
            "What is the current value of sensor 146?",
            "Show me sensor 147 from the last 24 hours",
            "What is the average temperature for sensor 80?",
            "Show me the maximum value of sensor 166 this week"
        ],
        'device_queries': [
            "List all devices in Vidrio Andino",
            "Show me sensors for device Pozo3",
            "What devices are in the system?",
            "Show me IoT_VidrioAndino sensors"
        ],
        'analysis_queries': [
            "What anomalies were detected this week?",
            "Show me temperature trends for the past month",
            "Compare sensor 146 and 147 values",
            "What is the quality yield trend?"
        ],
        'lstm_queries': [
            "When will sensor 146 fail?",
            "Predict sensor 147 failure",
            "What's the failure risk for sensor 146?",
            "Show maintenance schedule",
            "Which devices need maintenance?"
        ],
        'quick_queries': [
            "Show me furnace temperatures",
            "What's the pressure reading?",
            "Check quality metrics",
            "List production lines"
        ]
    }

    return jsonify({
        'success': True,
        'suggestions': suggestions
    }), 200


@nl_query_bp.route('/clear-history', methods=['POST'])
def clear_history():
    """
    Clear query history

    Returns:
        Success status
    """
    global _query_history

    count = len(_query_history)
    _query_history = []

    return jsonify({
        'success': True,
        'message': f'Cleared {count} queries from history'
    }), 200


@nl_query_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get query engine status

    Returns:
        System status and capabilities
    """
    engine = get_query_engine()

    status = {
        'success': True,
        'query_engine': {
            'status': 'operational' if engine else 'not_initialized',
            'version': '1.0',
            'capabilities': {
                'natural_language': True,
                'ai_answers': True,
                'template_answers': True,
                'sql_generation': True,
                'query_history': True,
                'max_results': 100
            },
            'supported_queries': [
                'sensor_value', 'statistics', 'device_info',
                'list_devices', 'list_sensors', 'anomalies',
                'trend_analysis', 'comparison'
            ]
        },
        'history': {
            'total_queries': len(_query_history),
            'recent_count': min(20, len(_query_history))
        },
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(status), 200


@nl_query_bp.route('/test', methods=['GET'])
def test_query():
    """
    Test query endpoint (no auth required)

    Query Parameters:
        q: Question to ask (default: "List all devices in Vidrio Andino")

    Returns:
        Test query result
    """
    engine = get_query_engine()
    if not engine:
        return jsonify({'error': 'Query engine not initialized'}), 500

    try:
        question = request.args.get('q', 'List all devices in Vidrio Andino')

        logger.info(f"Test query: {question}")

        result = engine.query(question, use_ai=False)  # Template for faster testing

        return jsonify({
            'success': 'error' not in result,
            'test_mode': True,
            'question': question,
            'answer': result.get('answer'),
            'intent': result.get('intent', {}),
            'result_count': result.get('result_count', 0),
            'results_preview': result.get('results', [])[:5],  # First 5 results
            'timestamp': result.get('timestamp')
        }), 200

    except Exception as e:
        logger.error(f"Error in test query: {e}")
        return jsonify({'error': str(e)}), 500


# Error handlers
@nl_query_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@nl_query_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
