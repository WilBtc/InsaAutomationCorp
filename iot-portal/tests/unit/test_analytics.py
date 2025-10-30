#!/usr/bin/env python3
"""
Unit Tests for Analytics Module (Phase 3 Feature 1)
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests all 5 analytics endpoints:
1. GET /api/v1/analytics/timeseries/<device_id>/<metric> - Time-series analysis
2. GET /api/v1/analytics/trend/<device_id>/<metric> - Trend detection
3. GET /api/v1/analytics/stats/<device_id>/<metric> - Statistical summary
4. GET /api/v1/analytics/correlation/<device_id> - Correlation analysis
5. GET /api/v1/analytics/forecast/<device_id>/<metric> - Simple forecasting
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import numpy as np


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_telemetry_data():
    """Generate sample telemetry data for testing"""
    base_time = datetime.now()
    data = []

    for i in range(100):
        data.append({
            'timestamp': (base_time - timedelta(minutes=100-i)).isoformat(),
            'value': 20.0 + i * 0.1 + np.random.normal(0, 0.5),  # Increasing trend
            'unit': '°C'
        })

    return data


@pytest.fixture
def correlation_data():
    """Generate multi-metric data for correlation testing"""
    base_time = datetime.now()
    data = {
        'temperature': [],
        'pressure': [],
        'humidity': []
    }

    for i in range(100):
        timestamp = (base_time - timedelta(minutes=100-i)).isoformat()
        # Positive correlation: temperature and pressure
        temp = 20.0 + i * 0.1
        pressure = 100.0 + i * 0.5 + np.random.normal(0, 1)
        # Negative correlation: temperature and humidity
        humidity = 80.0 - i * 0.2 + np.random.normal(0, 2)

        data['temperature'].append({'timestamp': timestamp, 'value': temp})
        data['pressure'].append({'timestamp': timestamp, 'value': pressure})
        data['humidity'].append({'timestamp': timestamp, 'value': humidity})

    return data


# ============================================================================
# Test 1: Time-series Analytics
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestTimeseriesAnalytics:
    """Test suite for time-series analytics endpoint"""

    def test_timeseries_success(self, client, admin_token, sample_telemetry_data):
        """Test successful time-series analysis"""
        with patch('app_advanced.get_db_connection') as mock_db:
            # Mock database query
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                {
                    'timestamp': row['timestamp'],
                    'value': row['value'],
                    'unit': row['unit'],
                    'moving_avg': row['value'],  # Simplified
                    'rate_per_minute': 0.1
                }
                for row in sample_telemetry_data[:50]
            ]

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            # Test request
            response = client.get(
                '/api/v1/analytics/timeseries/TEST-001/temperature?window=5',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert 'timestamps' in data
            assert 'values' in data
            assert 'moving_avg' in data
            assert 'rate_per_minute' in data
            assert 'unit' in data
            assert len(data['values']) == 50

    def test_timeseries_with_time_range(self, client, admin_token):
        """Test time-series with from/to parameters"""
        from_time = (datetime.now() - timedelta(hours=1)).isoformat()
        to_time = datetime.now().isoformat()

        response = client.get(
            f'/api/v1/analytics/timeseries/TEST-001/temperature?from={from_time}&to={to_time}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        # Should not fail even with empty data
        assert response.status_code in [200, 404]

    def test_timeseries_invalid_window(self, client, admin_token):
        """Test time-series with invalid window parameter"""
        response = client.get(
            '/api/v1/analytics/timeseries/TEST-001/temperature?window=-5',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        # Should handle invalid window gracefully
        assert response.status_code in [200, 400]

    def test_timeseries_no_auth(self, client):
        """Test time-series without authentication"""
        response = client.get(
            '/api/v1/analytics/timeseries/TEST-001/temperature'
        )

        assert response.status_code == 401

    def test_timeseries_limit_parameter(self, client, admin_token):
        """Test time-series with limit parameter"""
        response = client.get(
            '/api/v1/analytics/timeseries/TEST-001/temperature?limit=10',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 200:
            data = response.get_json()
            assert len(data.get('values', [])) <= 10


# ============================================================================
# Test 2: Trend Analysis
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestTrendAnalysis:
    """Test suite for trend detection endpoint"""

    def test_trend_increasing(self, client, admin_token):
        """Test detection of increasing trend"""
        with patch('app_advanced.get_db_connection') as mock_db:
            # Mock increasing trend data
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'slope': 0.05,  # Positive slope
                'r_squared': 0.95,  # High confidence
                'points': 100
            }

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/trend/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert data['trend'] == 'increasing'
            assert data['slope'] > 0
            assert data['confidence'] >= 0.9
            assert data['points'] == 100

    def test_trend_decreasing(self, client, admin_token):
        """Test detection of decreasing trend"""
        with patch('app_advanced.get_db_connection') as mock_db:
            # Mock decreasing trend data
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'slope': -0.05,  # Negative slope
                'r_squared': 0.92,
                'points': 100
            }

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/trend/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert data['trend'] == 'decreasing'
            assert data['slope'] < 0

    def test_trend_stable(self, client, admin_token):
        """Test detection of stable trend"""
        with patch('app_advanced.get_db_connection') as mock_db:
            # Mock stable trend data
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'slope': 0.005,  # Near-zero slope
                'r_squared': 0.85,
                'points': 100
            }

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/trend/TEST-001/temperature?threshold=0.01',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert data['trend'] == 'stable'

    def test_trend_insufficient_data(self, client, admin_token):
        """Test trend analysis with insufficient data"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/trend/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code in [200, 404]


# ============================================================================
# Test 3: Statistical Summary
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestStatisticalSummary:
    """Test suite for statistical summary endpoint"""

    def test_stats_complete(self, client, admin_token):
        """Test complete statistical summary"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'count': 100,
                'mean': 25.5,
                'median': 25.0,
                'min': 20.0,
                'max': 30.0,
                'p25': 22.5,
                'p75': 27.5,
                'stddev': 2.5,
                'variance': 6.25
            }

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/stats/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert data['count'] == 100
            assert data['mean'] == 25.5
            assert data['median'] == 25.0
            assert data['min'] == 20.0
            assert data['max'] == 30.0
            assert 'coefficient_of_variation' in data
            assert 'iqr' in data

    def test_stats_with_time_range(self, client, admin_token):
        """Test stats with time range filter"""
        from_time = (datetime.now() - timedelta(hours=1)).isoformat()
        to_time = datetime.now().isoformat()

        response = client.get(
            f'/api/v1/analytics/stats/TEST-001/temperature?from={from_time}&to={to_time}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code in [200, 404]

    def test_stats_empty_dataset(self, client, admin_token):
        """Test stats with no data"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/stats/NONEXISTENT/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code in [200, 404]


# ============================================================================
# Test 4: Correlation Analysis
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestCorrelationAnalysis:
    """Test suite for correlation analysis endpoint"""

    def test_correlation_success(self, client, admin_token):
        """Test successful correlation analysis"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                {'metric1': 'temperature', 'metric2': 'pressure', 'correlation': 0.85, 'strength': 'strong positive'},
                {'metric1': 'temperature', 'metric2': 'humidity', 'correlation': -0.75, 'strength': 'strong negative'},
                {'metric1': 'pressure', 'metric2': 'humidity', 'correlation': -0.65, 'strength': 'moderate negative'}
            ]

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/correlation/TEST-001',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 200
            data = response.get_json()

            assert 'correlations' in data
            assert len(data['correlations']) == 3
            assert data['correlations'][0]['correlation'] == 0.85
            assert 'strong positive' in data['correlations'][0]['strength']

    def test_correlation_single_metric(self, client, admin_token):
        """Test correlation with only one metric (should return empty)"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/correlation/TEST-001',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            if response.status_code == 200:
                data = response.get_json()
                assert 'correlations' in data
                assert len(data.get('correlations', [])) == 0

    def test_correlation_with_time_range(self, client, admin_token):
        """Test correlation with time filter"""
        from_time = (datetime.now() - timedelta(hours=1)).isoformat()

        response = client.get(
            f'/api/v1/analytics/correlation/TEST-001?from={from_time}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code in [200, 404]


# ============================================================================
# Test 5: Forecasting
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestForecasting:
    """Test suite for forecasting endpoint"""

    def test_forecast_success(self, client, admin_token):
        """Test successful forecast generation"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()

            # Mock historical data for regression
            historical_data = [
                {'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(), 'value': 20.0 + i * 0.1}
                for i in range(100, 0, -1)
            ]

            mock_cursor.fetchall.return_value = historical_data

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/forecast/TEST-001/temperature?periods=10',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            if response.status_code == 200:
                data = response.get_json()

                assert 'forecast' in data
                assert 'confidence_interval' in data
                assert 'slope' in data
                assert 'r_squared' in data
                assert len(data['forecast']) == 10

    def test_forecast_custom_periods(self, client, admin_token):
        """Test forecast with custom number of periods"""
        response = client.get(
            '/api/v1/analytics/forecast/TEST-001/temperature?periods=20',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 200:
            data = response.get_json()
            assert len(data.get('forecast', [])) <= 20

    def test_forecast_insufficient_data(self, client, admin_token):
        """Test forecast with insufficient historical data"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []  # No data

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/forecast/NONEXISTENT/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code in [200, 400, 404]

    def test_forecast_confidence_intervals(self, client, admin_token):
        """Test that forecast includes confidence intervals"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()

            historical_data = [
                {'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(), 'value': 20.0 + i * 0.1}
                for i in range(50, 0, -1)
            ]

            mock_cursor.fetchall.return_value = historical_data

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get(
                '/api/v1/analytics/forecast/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            if response.status_code == 200:
                data = response.get_json()
                assert 'confidence_interval' in data

                if data['confidence_interval']:
                    assert 'lower' in data['confidence_interval']
                    assert 'upper' in data['confidence_interval']


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.unit
@pytest.mark.analytics
class TestAnalyticsEdgeCases:
    """Test edge cases and error handling"""

    def test_database_connection_failure(self, client, admin_token):
        """Test handling of database connection failure"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_db.return_value = None

            response = client.get(
                '/api/v1/analytics/timeseries/TEST-001/temperature',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            assert response.status_code == 500

    def test_invalid_device_id(self, client, admin_token):
        """Test with invalid device ID format"""
        response = client.get(
            '/api/v1/analytics/timeseries//temperature',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 404

    def test_special_characters_in_metric(self, client, admin_token):
        """Test handling of special characters in metric name"""
        response = client.get(
            '/api/v1/analytics/timeseries/TEST-001/temp%20sensor',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 404]

    @pytest.mark.slow
    def test_large_dataset_performance(self, client, admin_token):
        """Test performance with large dataset request"""
        response = client.get(
            '/api/v1/analytics/timeseries/TEST-001/temperature?limit=10000',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        # Should not timeout or fail
        assert response.status_code in [200, 400, 404]
