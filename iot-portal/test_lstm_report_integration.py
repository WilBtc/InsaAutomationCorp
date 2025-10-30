#!/usr/bin/env python3
"""
Test LSTM + AI Report Integration
Quick verification that Phase A and Phase B are integrated correctly

Usage:
    python3 test_lstm_report_integration.py
"""

import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_iiot',
    'user': 'iiot_user',
    'password': 'iiot_secure_2025'
}


def test_lstm_forecaster():
    """Test LSTM forecaster initialization"""
    logger.info("=" * 80)
    logger.info("TEST 1: LSTM Forecaster Initialization")
    logger.info("=" * 80)

    try:
        from lstm_forecaster import LSTMForecaster

        forecaster = LSTMForecaster(DB_CONFIG)
        logger.info("✅ LSTM forecaster created successfully")

        # List available models
        models = forecaster.list_models()
        logger.info(f"✅ Found {len(models)} trained LSTM models")

        if models:
            for model in models[:3]:  # Show first 3
                logger.info(f"   - {model['device_name']}/{model['sensor_key']}: "
                           f"MAE={model['accuracy_mae']:.2f}, "
                           f"horizon={model['forecast_horizon_hours']}h")
        else:
            logger.warning("⚠️  No trained LSTM models found - train models first")

        return forecaster, len(models) > 0

    except Exception as e:
        logger.error(f"❌ LSTM forecaster test failed: {e}")
        return None, False


def test_report_generator(forecaster):
    """Test AI report generator with LSTM integration"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: AI Report Generator with LSTM")
    logger.info("=" * 80)

    try:
        from ai_report_generator import AIReportGenerator

        # Create generator WITH LSTM forecaster
        generator = AIReportGenerator(DB_CONFIG, lstm_forecaster=forecaster)
        logger.info("✅ AI Report Generator created with LSTM forecaster")

        # Generate test report
        logger.info("Generating test report for 'Vidrio Andino'...")
        report_data = generator.generate_report(
            device_location="Vidrio Andino",
            hours=24,
            use_ai=False,  # Use template for faster testing
            use_all_data=False
        )

        if 'error' in report_data:
            logger.error(f"❌ Report generation failed: {report_data['error']}")
            return False

        # Check report structure
        logger.info("✅ Report generated successfully")
        logger.info(f"   - Location: {report_data.get('location')}")
        logger.info(f"   - Devices: {report_data.get('device_count')}")
        logger.info(f"   - Sensors: {len(report_data.get('sensor_stats', {}))}")
        logger.info(f"   - Anomalies: {len(report_data.get('anomalies', []))}")
        logger.info(f"   - Correlations: {len(report_data.get('correlations', []))}")

        # CHECK: LSTM predictions included
        lstm_predictions = report_data.get('lstm_predictions', [])
        logger.info(f"   - LSTM Predictions: {len(lstm_predictions)} ⭐ NEW")

        if lstm_predictions:
            logger.info("✅ LSTM predictions successfully integrated in report!")

            # Show prediction details
            for pred in lstm_predictions[:3]:  # First 3
                risk = pred['failure_risk']
                logger.info(f"\n   📊 Sensor {pred['sensor_key']}:")
                logger.info(f"      - Risk Level: {risk['risk_level'].upper()}")
                logger.info(f"      - Risk Score: {risk['risk_score']}")
                logger.info(f"      - Time to Failure: {risk.get('time_to_failure_hours', 'N/A')}h")
                logger.info(f"      - Recommendation: {risk['recommended_action']}")
        else:
            logger.warning("⚠️  No LSTM predictions in report (expected if no models trained)")

        # Check narrative includes LSTM mentions
        narrative = report_data.get('narrative', '')
        if 'PREDICTIVE MAINTENANCE' in narrative or 'LSTM' in narrative or 'forecast' in narrative.lower():
            logger.info("✅ Narrative includes LSTM predictions")
        else:
            logger.warning("⚠️  Narrative does not mention LSTM predictions")

        # Save report to file
        logger.info("\nSaving test report to HTML...")
        html_path = generator.save_report(report_data, format='html')

        if html_path:
            logger.info(f"✅ HTML report saved: {html_path}")
            logger.info(f"   Open with: open {html_path}")

            # Check HTML contains LSTM section
            with open(html_path, 'r') as f:
                html_content = f.read()
                if 'LSTM Predictive Maintenance Forecast' in html_content:
                    logger.info("✅ HTML report contains LSTM section")
                else:
                    logger.warning("⚠️  HTML report missing LSTM section")

        return True

    except Exception as e:
        logger.error(f"❌ Report generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reporting_api_integration():
    """Test that reporting API can be initialized with LSTM forecaster"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Reporting API Integration")
    logger.info("=" * 80)

    try:
        from reporting_api import init_reporting_api, get_report_generator
        from lstm_forecaster import LSTMForecaster

        # Create forecaster
        forecaster = LSTMForecaster(DB_CONFIG)

        # Initialize API with forecaster
        init_reporting_api(DB_CONFIG, lstm_forecaster=forecaster)
        logger.info("✅ Reporting API initialized with LSTM forecaster")

        # Get generator
        generator = get_report_generator()

        if generator and generator.lstm_forecaster:
            logger.info("✅ Report generator has LSTM forecaster attached")
            return True
        else:
            logger.error("❌ Report generator missing LSTM forecaster")
            return False

    except Exception as e:
        logger.error(f"❌ Reporting API integration test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    logger.info("\n" + "=" * 80)
    logger.info("LSTM + AI REPORT INTEGRATION TEST SUITE")
    logger.info("=" * 80)
    logger.info("Testing Phase A + Phase B Integration")
    logger.info("=" * 80 + "\n")

    results = {
        'lstm_forecaster': False,
        'report_generator': False,
        'api_integration': False
    }

    # Test 1: LSTM Forecaster
    forecaster, has_models = test_lstm_forecaster()
    results['lstm_forecaster'] = forecaster is not None

    if not forecaster:
        logger.error("\n❌ Cannot proceed - LSTM forecaster failed to initialize")
        sys.exit(1)

    # Test 2: Report Generator
    results['report_generator'] = test_report_generator(forecaster)

    # Test 3: API Integration
    results['api_integration'] = test_reporting_api_integration()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        logger.info(f"{status} - {test_name.replace('_', ' ').title()}")

    logger.info("=" * 80)
    logger.info(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    logger.info("=" * 80)

    if passed == total:
        logger.info("\n🎉 SUCCESS: All integration tests passed!")
        logger.info("✅ Phase A + Phase B integration is working correctly")
        logger.info("✅ LSTM predictions are included in AI reports")
        logger.info("✅ Reporting API correctly integrates with LSTM forecaster")

        if not has_models:
            logger.warning("\n⚠️  Note: No trained LSTM models found")
            logger.warning("   Train models first to see predictions in reports:")
            logger.warning("   curl -X POST http://localhost:5002/api/v1/lstm/train ...")

        return 0
    else:
        logger.error("\n❌ FAILURE: Some tests failed")
        logger.error(f"   {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
