#!/usr/bin/env python3
"""
Alert Testing Script for INSA CRM Monitoring
Tests alert firing by simulating various failure scenarios
"""
import time
import logging
import requests
from prometheus_metrics import metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_worker_unhealthy_alert():
    """
    Test WorkerUnhealthy alert by marking a worker as unhealthy
    Alert should fire after 1 minute
    """
    logger.info("=" * 60)
    logger.info("TEST 1: WorkerUnhealthy Alert")
    logger.info("=" * 60)

    worker_name = "test_worker"
    worker_type = "test"

    logger.info(f"Setting {worker_name} to UNHEALTHY...")
    metrics.update_worker_health(worker_name, worker_type, healthy=False)

    logger.info("Worker marked as unhealthy. Alert should fire in 1 minute.")
    logger.info("Check Alertmanager: http://localhost:9093/#/alerts")

    time.sleep(5)

    logger.info(f"Recovering {worker_name} to HEALTHY...")
    metrics.update_worker_health(worker_name, worker_type, healthy=True)

    logger.info("Worker recovered. Alert should resolve shortly.")
    logger.info("")


def test_high_error_rate_alert():
    """
    Test HighErrorRate alert by generating many error requests
    Alert should fire after 5 minutes if error rate > 5%
    """
    logger.info("=" * 60)
    logger.info("TEST 2: HighErrorRate Alert")
    logger.info("=" * 60)

    agent_type = "test_agent"

    logger.info("Generating high error rate (20 errors, 1 success)...")

    # Generate errors
    for i in range(20):
        metrics.record_request(agent_type, "error", duration=0.1, request_size=100, response_size=0)

    # Generate some successes (but still >5% error rate)
    for i in range(1):
        metrics.record_request(agent_type, "success", duration=0.1, request_size=100, response_size=200)

    logger.info("Error rate: 95% (threshold: 5%). Alert should fire in 5 minutes.")
    logger.info("Generating normal traffic to resolve alert...")

    # Generate normal traffic (95% success)
    for i in range(95):
        metrics.record_request(agent_type, "success", duration=0.1, request_size=100, response_size=200)

    for i in range(5):
        metrics.record_request(agent_type, "error", duration=0.1, request_size=100, response_size=0)

    logger.info("Error rate normalized to 5%. Alert should resolve.")
    logger.info("")


def test_circuit_breaker_open_alert():
    """
    Test CircuitBreakerOpen alert by setting circuit breaker to OPEN state
    Alert should fire after 2 minutes
    """
    logger.info("=" * 60)
    logger.info("TEST 3: CircuitBreakerOpen Alert")
    logger.info("=" * 60)

    breaker_name = "test_breaker"

    logger.info(f"Setting circuit breaker {breaker_name} to OPEN...")
    metrics.update_circuit_breaker_state(breaker_name, "open")

    logger.info("Circuit breaker OPEN. Alert should fire in 2 minutes.")

    time.sleep(5)

    logger.info(f"Transitioning {breaker_name} to HALF_OPEN...")
    metrics.record_circuit_breaker_transition(breaker_name, "open", "half_open")
    metrics.update_circuit_breaker_state(breaker_name, "half_open")

    time.sleep(2)

    logger.info(f"Recovering {breaker_name} to CLOSED...")
    metrics.record_circuit_breaker_transition(breaker_name, "half_open", "closed")
    metrics.update_circuit_breaker_state(breaker_name, "closed")

    logger.info("Circuit breaker recovered. Alert should resolve.")
    logger.info("")


def test_dlq_growing_alert():
    """
    Test DeadLetterQueueGrowing alert by increasing DLQ size
    Alert should fire after 10 minutes if size > 50
    """
    logger.info("=" * 60)
    logger.info("TEST 4: DeadLetterQueueGrowing Alert")
    logger.info("=" * 60)

    agent_type = "test_agent"

    logger.info(f"Increasing DLQ size to 75 messages (threshold: 50)...")
    metrics.update_dead_letter_queue_size(agent_type, 75)

    logger.info("DLQ size: 75. Alert should fire in 10 minutes.")

    time.sleep(5)

    logger.info("Replaying messages and reducing DLQ size...")

    # Simulate successful replays
    for i in range(50):
        metrics.record_dead_letter_replay(agent_type, success=True)

    metrics.update_dead_letter_queue_size(agent_type, 25)

    logger.info("DLQ size reduced to 25. Alert should resolve.")
    logger.info("")


def test_low_cache_hit_rate_alert():
    """
    Test LowCacheHitRate alert by generating many cache misses
    Alert should fire after 15 minutes if hit rate < 70%
    """
    logger.info("=" * 60)
    logger.info("TEST 5: LowCacheHitRate Alert")
    logger.info("=" * 60)

    cache_type = "test_cache"

    logger.info("Generating low cache hit rate (30% hits, 70% misses)...")

    # Generate many misses
    for i in range(70):
        metrics.record_cache_miss(cache_type)

    # Generate some hits (but still <70%)
    for i in range(30):
        metrics.record_cache_hit(cache_type)

    logger.info("Cache hit rate: 30% (threshold: 70%). Alert should fire in 15 minutes.")

    logger.info("Improving cache hit rate...")

    # Generate normal cache behavior (80% hits)
    for i in range(80):
        metrics.record_cache_hit(cache_type)

    for i in range(20):
        metrics.record_cache_miss(cache_type)

    logger.info("Cache hit rate improved to 80%. Alert should resolve.")
    logger.info("")


def test_high_latency_alert():
    """
    Test HighLatencyP95 alert by generating slow requests
    Alert should fire after 10 minutes if P95 > 10s
    """
    logger.info("=" * 60)
    logger.info("TEST 6: HighLatencyP95 Alert")
    logger.info("=" * 60)

    agent_type = "test_agent"

    logger.info("Generating high latency requests (P95 > 10s)...")

    # Generate many fast requests
    for i in range(90):
        metrics.record_request(agent_type, "success", duration=0.5, request_size=100, response_size=200)

    # Generate some very slow requests (5% are >10s)
    for i in range(10):
        metrics.record_request(agent_type, "success", duration=15.0, request_size=100, response_size=200)

    logger.info("P95 latency: ~15s (threshold: 10s). Alert should fire in 10 minutes.")

    logger.info("Reducing latency...")

    # Generate all fast requests
    for i in range(100):
        metrics.record_request(agent_type, "success", duration=0.5, request_size=100, response_size=200)

    logger.info("P95 latency normalized. Alert should resolve.")
    logger.info("")


def check_prometheus_connection():
    """Check if Prometheus is accessible"""
    try:
        response = requests.get('http://localhost:9090/-/healthy', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Prometheus is running and healthy")
            return True
        else:
            logger.error(f"❌ Prometheus health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to Prometheus: {e}")
        return False


def check_alertmanager_connection():
    """Check if Alertmanager is accessible"""
    try:
        response = requests.get('http://localhost:9093/-/healthy', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Alertmanager is running and healthy")
            return True
        else:
            logger.error(f"❌ Alertmanager health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to Alertmanager: {e}")
        logger.error("   Make sure Alertmanager is running: alertmanager --config.file=alertmanager.yml")
        return False


def check_metrics_endpoint():
    """Check if metrics endpoint is accessible"""
    try:
        response = requests.get('http://localhost:9091/metrics', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Metrics endpoint is accessible")
            return True
        else:
            logger.error(f"❌ Metrics endpoint check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to metrics endpoint: {e}")
        logger.error("   Make sure crm-backend.py is running")
        return False


def main():
    """Run all alert tests"""
    logger.info("=" * 60)
    logger.info("INSA CRM Alert Testing")
    logger.info("=" * 60)
    logger.info("")

    # Check prerequisites
    logger.info("Checking prerequisites...")
    prometheus_ok = check_prometheus_connection()
    alertmanager_ok = check_alertmanager_connection()
    metrics_ok = check_metrics_endpoint()

    if not all([prometheus_ok, alertmanager_ok, metrics_ok]):
        logger.error("")
        logger.error("❌ Prerequisites not met. Please ensure:")
        logger.error("   1. Prometheus is running: prometheus --config.file=prometheus_config.yml")
        logger.error("   2. Alertmanager is running: alertmanager --config.file=alertmanager.yml")
        logger.error("   3. CRM backend is running: ./venv/bin/python crm-backend.py")
        logger.error("")
        return

    logger.info("")
    logger.info("All prerequisites met. Starting alert tests...")
    logger.info("")
    logger.info("Note: Alerts have different 'for' durations:")
    logger.info("  - WorkerUnhealthy: 1 minute")
    logger.info("  - CircuitBreakerOpen: 2 minutes")
    logger.info("  - HighErrorRate: 5 minutes")
    logger.info("  - DeadLetterQueueGrowing: 10 minutes")
    logger.info("  - LowCacheHitRate: 15 minutes")
    logger.info("  - HighLatencyP95: 10 minutes")
    logger.info("")
    logger.info("Monitor alerts at:")
    logger.info("  - Prometheus: http://localhost:9090/alerts")
    logger.info("  - Alertmanager: http://localhost:9093/#/alerts")
    logger.info("")

    input("Press Enter to start tests...")

    # Run tests
    test_worker_unhealthy_alert()
    test_circuit_breaker_open_alert()
    test_high_error_rate_alert()
    test_dlq_growing_alert()
    test_low_cache_hit_rate_alert()
    test_high_latency_alert()

    logger.info("=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Check Prometheus alerts: http://localhost:9090/alerts")
    logger.info("2. Check Alertmanager: http://localhost:9093/#/alerts")
    logger.info("3. Wait for alert 'for' durations to expire")
    logger.info("4. Verify email notifications are sent")
    logger.info("5. Confirm alerts resolve after recovery")
    logger.info("")


if __name__ == '__main__':
    main()
