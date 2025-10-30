#!/usr/bin/env python3
"""
Test LSTM + NL Query Integration
Phase A + Phase C Integration Test

Verifies natural language queries can trigger LSTM predictions
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5002"
NL_QUERY_URL = f"{BASE_URL}/api/v1/query/ask"
LSTM_URL = f"{BASE_URL}/api/v1/lstm"

# Test queries
TEST_QUERIES = [
    # LSTM prediction queries
    {
        "question": "When will sensor 146 fail?",
        "expected_intent": "lstm_prediction"
    },
    {
        "question": "Predict sensor 146 failure",
        "expected_intent": "lstm_prediction"
    },
    {
        "question": "What's the failure risk for sensor 146?",
        "expected_intent": "failure_risk"
    },
    {
        "question": "Show maintenance schedule",
        "expected_intent": "maintenance_schedule"
    },
    {
        "question": "Which devices need maintenance?",
        "expected_intent": "maintenance_schedule"
    },
    # Non-LSTM queries (should still work)
    {
        "question": "What is the current value of sensor 146?",
        "expected_intent": "sensor_value"
    }
]


def test_nl_query(question: str, expected_intent: str) -> bool:
    """Test a single NL query"""
    print(f"\n{'='*80}")
    print(f"Testing: '{question}'")
    print(f"Expected intent: {expected_intent}")
    print(f"{'='*80}")

    try:
        # Send query
        response = requests.post(
            NL_QUERY_URL,
            json={"question": question, "use_ai": False},  # Use template for faster testing
            timeout=30
        )

        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()

        # Check if successful
        if not result.get('success'):
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            if 'suggestions' in result:
                print(f"Suggestions: {result['suggestions']}")
            return False

        # Verify intent
        intent = result.get('intent', {})
        intent_type = intent.get('type', 'unknown')

        print(f"✅ Query successful")
        print(f"Detected intent: {intent_type} (confidence: {intent.get('confidence', 0):.2f})")

        if intent_type != expected_intent:
            print(f"⚠️  Intent mismatch! Expected: {expected_intent}, Got: {intent_type}")
            return False

        # Display answer
        answer = result.get('answer', 'No answer generated')
        print(f"\n💬 Answer:")
        print(f"   {answer}\n")

        # Display additional data for LSTM queries
        if intent_type in ['lstm_prediction', 'failure_risk', 'maintenance_schedule']:
            if 'risk_assessment' in result:
                risk = result['risk_assessment']
                print(f"📊 Risk Assessment:")
                print(f"   Level: {risk.get('risk_level', 'unknown').upper()}")
                print(f"   Score: {risk.get('risk_score', 0)}/100")
                if risk.get('time_to_failure_hours'):
                    print(f"   Time to failure: {risk['time_to_failure_hours']} hours")
                print(f"   Action: {risk.get('recommended_action', 'N/A')}")

            if 'summary' in result:
                summary = result['summary']
                print(f"📋 Schedule Summary:")
                print(f"   High risk: {summary.get('high_risk', 0)} items")
                print(f"   Medium risk: {summary.get('medium_risk', 0)} items")

            if 'forecasts' in result:
                forecasts = result['forecasts'][:3]  # First 3 hours
                print(f"🔮 Forecast Preview (first 3 hours):")
                for forecast in forecasts:
                    print(f"   +{forecast['hours_ahead']}h: {forecast['predicted_value']:.2f}")

        return True

    except requests.exceptions.Timeout:
        print(f"❌ Request timeout after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - is the server running at {BASE_URL}?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_lstm_status():
    """Check if LSTM is available"""
    print(f"\n{'='*80}")
    print("Checking LSTM Status")
    print(f"{'='*80}")

    try:
        response = requests.get(f"{LSTM_URL}/status", timeout=10)

        if response.status_code == 200:
            status = response.json()
            engine = status.get('forecasting_engine', {})

            print(f"Status: {engine.get('status', 'unknown')}")
            print(f"TensorFlow: {'✅ Available' if engine.get('tensorflow_available') else '❌ Not available'}")

            if engine.get('tensorflow_version'):
                print(f"Version: {engine['tensorflow_version']}")

            trained_models = status.get('trained_models', {})
            print(f"Trained models: {trained_models.get('count', 0)}")

            return engine.get('tensorflow_available', False)
        else:
            print(f"❌ Status check failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False


def check_nl_query_status():
    """Check if NL Query is available"""
    print(f"\n{'='*80}")
    print("Checking NL Query Status")
    print(f"{'='*80}")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/query/status", timeout=10)

        if response.status_code == 200:
            status = response.json()
            engine = status.get('query_engine', {})

            print(f"Status: {engine.get('status', 'unknown')}")
            print(f"Capabilities: {', '.join(engine.get('capabilities', {}).keys())}")
            print(f"Supported queries: {len(engine.get('supported_queries', []))}")

            return engine.get('status') == 'operational'
        else:
            print(f"❌ Status check failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False


def main():
    """Run integration tests"""
    print("🔗 LSTM + NL Query Integration Test")
    print("=" * 80)

    # Check service status
    lstm_available = check_lstm_status()
    nl_query_available = check_nl_query_status()

    if not nl_query_available:
        print("\n❌ NL Query API not available - stopping tests")
        sys.exit(1)

    if not lstm_available:
        print("\n⚠️  LSTM not available - LSTM queries will fail gracefully")

    # Run tests
    results = []
    for test_query in TEST_QUERIES:
        question = test_query['question']
        expected_intent = test_query['expected_intent']

        # Skip LSTM tests if LSTM not available
        if not lstm_available and expected_intent in ['lstm_prediction', 'failure_risk', 'maintenance_schedule']:
            print(f"\n⏭️  Skipping LSTM query: '{question}' (LSTM not available)")
            continue

        success = test_nl_query(question, expected_intent)
        results.append({
            'question': question,
            'success': success
        })

    # Summary
    print(f"\n{'='*80}")
    print("Test Summary")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r['success'])
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Passed: {passed}/{total} ({pass_rate:.1f}%)")
    print()

    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['question']}")

    print()

    if pass_rate == 100:
        print("🎉 All tests passed!")
        sys.exit(0)
    elif pass_rate >= 50:
        print("⚠️  Some tests failed")
        sys.exit(1)
    else:
        print("❌ Most tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
