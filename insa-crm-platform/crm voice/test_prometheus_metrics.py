#!/usr/bin/env python3
"""
Tests for Prometheus Metrics Integration
Tests all metrics, helper methods, and HTTP endpoint
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
import requests

from prometheus_metrics import (
    PrometheusMetrics,
    metrics,
    initialize_metrics,
    start_metrics_server
)


class TestPrometheusMetrics:
    """Test PrometheusMetrics class"""

    def setup_method(self):
        """Setup test environment"""
        # Create fresh metrics instance for testing
        self.metrics = PrometheusMetrics()

    def test_initialization(self):
        """Test metrics are properly initialized"""
        # Check that all expected metrics exist
        assert self.metrics.request_total is not None
        assert self.metrics.request_duration is not None
        assert self.metrics.request_size is not None
        assert self.metrics.response_size is not None
        assert self.metrics.cache_hits is not None
        assert self.metrics.cache_misses is not None
        assert self.metrics.message_bus_messages is not None
        assert self.metrics.worker_health is not None
        assert self.metrics.retry_attempts is not None
        assert self.metrics.circuit_breaker_state is not None
        assert self.metrics.dead_letter_queue_size is not None

    def test_record_request_counter(self):
        """Test request counter increments"""
        agent_type = "test_agent"
        status = "success"

        # Get initial value
        initial_value = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": status}
        )

        # Record request
        self.metrics.record_request(agent_type, status, duration=1.0, request_size=100, response_size=200)

        # Check counter incremented
        new_value = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": status}
        )

        assert new_value == initial_value + 1

    def test_record_request_duration_histogram(self):
        """Test request duration histogram records observations"""
        agent_type = "test_agent"
        duration = 2.5

        # Record request
        self.metrics.record_request(agent_type, "success", duration=duration, request_size=100, response_size=200)

        # Check histogram has observations
        histogram_samples = self._get_histogram_samples(self.metrics.request_duration)
        assert len(histogram_samples) > 0

    def test_cache_hit_miss_counters(self):
        """Test cache hit and miss counters"""
        cache_type = "test_cache"

        # Get initial values
        initial_hits = self._get_metric_value(
            self.metrics.cache_hits,
            {"cache_type": cache_type}
        )
        initial_misses = self._get_metric_value(
            self.metrics.cache_misses,
            {"cache_type": cache_type}
        )

        # Record hits and misses
        self.metrics.record_cache_hit(cache_type)
        self.metrics.record_cache_hit(cache_type)
        self.metrics.record_cache_miss(cache_type)

        # Check values
        new_hits = self._get_metric_value(
            self.metrics.cache_hits,
            {"cache_type": cache_type}
        )
        new_misses = self._get_metric_value(
            self.metrics.cache_misses,
            {"cache_type": cache_type}
        )

        assert new_hits == initial_hits + 2
        assert new_misses == initial_misses + 1

    def test_cache_size_gauge(self):
        """Test cache size gauge updates"""
        cache_type = "test_cache"
        size = 150

        # Update cache size
        self.metrics.update_cache_size(cache_type, size)

        # Check gauge value
        value = self._get_metric_value(
            self.metrics.cache_size,
            {"cache_type": cache_type}
        )

        assert value == size

    def test_worker_health_gauge(self):
        """Test worker health gauge updates"""
        worker_name = "test_worker"
        worker_type = "sizing"

        # Set health status
        self.metrics.update_worker_health(worker_name, worker_type, healthy=True)

        # Check value
        value = self._get_metric_value(
            self.metrics.worker_health,
            {"worker_name": worker_name, "worker_type": worker_type}
        )

        assert value == 1

        # Set unhealthy
        self.metrics.update_worker_health(worker_name, worker_type, healthy=False)

        value = self._get_metric_value(
            self.metrics.worker_health,
            {"worker_name": worker_name, "worker_type": worker_type}
        )

        assert value == 0

    def test_retry_metrics(self):
        """Test retry attempt and success counters"""
        agent_type = "test_agent"
        attempt_number = 2

        # Get initial values
        initial_attempts = self._get_metric_value(
            self.metrics.retry_attempts,
            {"agent_type": agent_type, "attempt_number": str(attempt_number)}
        )
        initial_successes = self._get_metric_value(
            self.metrics.retry_success,
            {"agent_type": agent_type, "attempt_number": str(attempt_number)}
        )

        # Record retry attempt and success
        self.metrics.record_retry_attempt(agent_type, attempt_number)
        self.metrics.record_retry_success(agent_type, attempt_number)

        # Check values
        new_attempts = self._get_metric_value(
            self.metrics.retry_attempts,
            {"agent_type": agent_type, "attempt_number": str(attempt_number)}
        )
        new_successes = self._get_metric_value(
            self.metrics.retry_success,
            {"agent_type": agent_type, "attempt_number": str(attempt_number)}
        )

        assert new_attempts == initial_attempts + 1
        assert new_successes == initial_successes + 1

    def test_circuit_breaker_state_gauge(self):
        """Test circuit breaker state gauge"""
        breaker_name = "test_breaker"

        # Test all states
        states = {"closed": 0, "open": 1, "half_open": 2}

        for state_name, state_value in states.items():
            self.metrics.update_circuit_breaker_state(breaker_name, state_name)

            value = self._get_metric_value(
                self.metrics.circuit_breaker_state,
                {"breaker_name": breaker_name}
            )

            assert value == state_value

    def test_circuit_breaker_transitions(self):
        """Test circuit breaker transition counter"""
        breaker_name = "test_breaker"
        from_state = "closed"
        to_state = "open"

        # Get initial value
        initial_value = self._get_metric_value(
            self.metrics.circuit_breaker_transitions,
            {"breaker_name": breaker_name, "from_state": from_state, "to_state": to_state}
        )

        # Record transition
        self.metrics.record_circuit_breaker_transition(breaker_name, from_state, to_state)

        # Check value
        new_value = self._get_metric_value(
            self.metrics.circuit_breaker_transitions,
            {"breaker_name": breaker_name, "from_state": from_state, "to_state": to_state}
        )

        assert new_value == initial_value + 1

    def test_dead_letter_queue_size(self):
        """Test DLQ size gauge"""
        agent_type = "test_agent"
        size = 42

        # Update DLQ size
        self.metrics.update_dead_letter_queue_size(agent_type, size)

        # Check value
        value = self._get_metric_value(
            self.metrics.dead_letter_queue_size,
            {"agent_type": agent_type}
        )

        assert value == size

    def test_dead_letter_replay(self):
        """Test DLQ replay counters"""
        agent_type = "test_agent"

        # Get initial values
        initial_success = self._get_metric_value(
            self.metrics.dead_letter_replay,
            {"agent_type": agent_type, "success": "true"}
        )
        initial_failure = self._get_metric_value(
            self.metrics.dead_letter_replay,
            {"agent_type": agent_type, "success": "false"}
        )

        # Record replay success and failure
        self.metrics.record_dead_letter_replay(agent_type, success=True)
        self.metrics.record_dead_letter_replay(agent_type, success=False)

        # Check values
        new_success = self._get_metric_value(
            self.metrics.dead_letter_replay,
            {"agent_type": agent_type, "success": "true"}
        )
        new_failure = self._get_metric_value(
            self.metrics.dead_letter_replay,
            {"agent_type": agent_type, "success": "false"}
        )

        assert new_success == initial_success + 1
        assert new_failure == initial_failure + 1

    def test_message_bus_metrics(self):
        """Test message bus counters"""
        topic = "test_topic"
        priority = "high"

        # Get initial value
        initial_value = self._get_metric_value(
            self.metrics.message_bus_messages,
            {"topic": topic, "priority": priority}
        )

        # Record message
        self.metrics.record_message_bus_message(topic, priority)

        # Check value
        new_value = self._get_metric_value(
            self.metrics.message_bus_messages,
            {"topic": topic, "priority": priority}
        )

        assert new_value == initial_value + 1

    def test_track_request_metrics_decorator(self):
        """Test @track_request_metrics decorator"""
        agent_type = "test_agent"

        # Get initial request count
        initial_count = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": "success"}
        )

        # Decorate a test function
        from prometheus_metrics import track_request_metrics

        @track_request_metrics(agent_type)
        def test_function():
            time.sleep(0.1)
            return {"result": "success", "data": "test"}

        # Call function
        result = test_function()

        # Check request was recorded
        new_count = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": "success"}
        )

        assert new_count == initial_count + 1
        assert result == {"result": "success", "data": "test"}

    def test_track_request_metrics_decorator_with_error(self):
        """Test @track_request_metrics decorator handles errors"""
        agent_type = "test_agent"

        # Get initial error count
        initial_count = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": "error"}
        )

        # Decorate a test function that raises
        from prometheus_metrics import track_request_metrics

        @track_request_metrics(agent_type)
        def test_function():
            raise ValueError("Test error")

        # Call function and expect error
        with pytest.raises(ValueError):
            test_function()

        # Check error was recorded
        new_count = self._get_metric_value(
            self.metrics.request_total,
            {"agent_type": agent_type, "status": "error"}
        )

        assert new_count == initial_count + 1

    def test_message_processing_context_manager(self):
        """Test message processing context manager"""
        topic = "test_topic"
        priority = "high"

        # Get initial values
        initial_messages = self._get_metric_value(
            self.metrics.message_bus_messages,
            {"topic": topic, "priority": priority}
        )
        initial_queue_depth = self._get_metric_value(
            self.metrics.message_bus_queue_depth,
            {"topic": topic}
        )

        # Use context manager
        from prometheus_metrics import track_message_processing

        with track_message_processing(topic, priority):
            # Queue depth should increase
            current_depth = self._get_metric_value(
                self.metrics.message_bus_queue_depth,
                {"topic": topic}
            )
            assert current_depth == initial_queue_depth + 1

        # After context, message count should increase and queue depth decrease
        new_messages = self._get_metric_value(
            self.metrics.message_bus_messages,
            {"topic": topic, "priority": priority}
        )
        new_queue_depth = self._get_metric_value(
            self.metrics.message_bus_queue_depth,
            {"topic": topic}
        )

        assert new_messages == initial_messages + 1
        assert new_queue_depth == initial_queue_depth

    # Helper methods
    def _get_metric_value(self, metric, labels):
        """Get value from metric with specific labels"""
        try:
            # For Counter/Gauge with labels
            if hasattr(metric, 'labels'):
                labeled_metric = metric.labels(**labels)
                # Get current value
                for sample in labeled_metric.collect()[0].samples:
                    if sample.labels == labels:
                        return sample.value
            return 0
        except Exception:
            return 0

    def _get_histogram_samples(self, histogram):
        """Get all samples from histogram"""
        samples = []
        for family in histogram.collect():
            samples.extend(family.samples)
        return samples


class TestMetricsServer:
    """Test Prometheus metrics HTTP server"""

    @pytest.fixture(scope="class")
    def metrics_server(self):
        """Start metrics server for testing"""
        port = 19091  # Use different port for testing

        # Start server in background thread
        server_thread = threading.Thread(
            target=start_metrics_server,
            args=(port,),
            daemon=True
        )
        server_thread.start()

        # Wait for server to start
        time.sleep(1)

        yield f"http://localhost:{port}"

        # Server will be cleaned up automatically (daemon thread)

    def test_metrics_endpoint_accessible(self, metrics_server):
        """Test /metrics endpoint is accessible"""
        response = requests.get(f"{metrics_server}/metrics", timeout=5)

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("Content-Type", "")

    def test_metrics_endpoint_contains_expected_metrics(self, metrics_server):
        """Test /metrics endpoint returns expected metrics"""
        response = requests.get(f"{metrics_server}/metrics", timeout=5)

        # Check for key metrics in response
        assert "insa_agent_requests_total" in response.text
        assert "insa_agent_request_duration_seconds" in response.text
        assert "insa_cache_hits_total" in response.text
        assert "insa_cache_misses_total" in response.text
        assert "insa_worker_health_status" in response.text
        assert "insa_retry_attempts_total" in response.text
        assert "insa_circuit_breaker_state" in response.text
        assert "insa_dead_letter_queue_size" in response.text

    def test_metrics_endpoint_prometheus_format(self, metrics_server):
        """Test /metrics endpoint returns Prometheus text format"""
        response = requests.get(f"{metrics_server}/metrics", timeout=5)

        # Check for HELP and TYPE comments
        assert "# HELP insa_agent_requests_total" in response.text
        assert "# TYPE insa_agent_requests_total counter" in response.text
        assert "# TYPE insa_agent_request_duration_seconds histogram" in response.text


class TestInitialization:
    """Test module initialization functions"""

    def test_initialize_metrics(self):
        """Test initialize_metrics function"""
        # Should not raise any errors
        initialize_metrics(version="1.0.0", environment="test")

        # Global metrics instance should be available
        assert metrics is not None

    def test_global_metrics_instance(self):
        """Test global metrics instance is accessible"""
        from prometheus_metrics import metrics

        assert metrics is not None
        assert isinstance(metrics, PrometheusMetrics)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
