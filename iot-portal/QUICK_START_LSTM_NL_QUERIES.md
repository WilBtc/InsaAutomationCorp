# Quick Start: LSTM Natural Language Queries

**5-Minute Guide to Using Natural Language for Failure Predictions**

---

## Prerequisites

1. ✅ Flask app running on port 5002
2. ✅ TensorFlow installed (`pip install tensorflow`)
3. ✅ LSTM model trained for target sensor

---

## Step 1: Verify System Status (30 seconds)

```bash
# Check if NL Query API is operational
curl http://localhost:5002/api/v1/query/status

# Check if LSTM API is operational
curl http://localhost:5002/api/v1/lstm/status

# List trained models
curl http://localhost:5002/api/v1/lstm/models
```

**Expected Output**: Both APIs should show `"status": "operational"`

---

## Step 2: Train a Model (Optional - 2 minutes)

If no models exist, train one first:

```bash
curl -X POST http://localhost:5002/api/v1/lstm/train \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "34e566f0-6d61-11f0-8d7b-3bc2e9586a38",
    "sensor_key": "146"
  }'
```

**Note**: Training takes 20-60 seconds depending on CPU. You only need to do this once per sensor.

---

## Step 3: Ask Your First Question (5 seconds)

### Question 1: "When will sensor 146 fail?"

```bash
curl -X POST http://localhost:5002/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"When will sensor 146 fail?","use_ai":false}'
```

**Expected Answer**:
```json
{
  "success": true,
  "answer": "🔴 Sensor 146 on IoT_VidrioAndino: Predicted failure in 8 hours. Recommendation: URGENT: Schedule immediate maintenance - failure expected within 24 hours Next hour prediction: 78.5",
  "risk_assessment": {
    "risk_level": "high",
    "risk_score": 85,
    "time_to_failure_hours": 8,
    "recommended_action": "URGENT: Schedule immediate maintenance..."
  },
  "forecasts": [
    {
      "timestamp": "2025-10-30T13:00:00",
      "predicted_value": 78.5,
      "confidence_lower": 75.2,
      "confidence_upper": 81.8,
      "hours_ahead": 1
    }
  ]
}
```

---

### Question 2: "Show maintenance schedule"

```bash
curl -X POST http://localhost:5002/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Show maintenance schedule","use_ai":false}'
```

**Expected Answer**:
```json
{
  "success": true,
  "answer": "🔧 Maintenance Schedule: 5 items requiring attention.\n\n🔴 URGENT (2): IoT_VidrioAndino sensor 146, Pozo3 sensor 147\n\n🟡 MONITOR (3): TempSensor1 sensor 80, PressureSensor sensor 166, FlowMeter sensor 200",
  "results": [
    {
      "device_name": "IoT_VidrioAndino",
      "sensor_key": "146",
      "risk_level": "high",
      "risk_score": 85,
      "time_to_failure_hours": 8,
      "recommended_action": "URGENT: Schedule immediate maintenance..."
    }
  ],
  "summary": {
    "high_risk": 2,
    "medium_risk": 3
  }
}
```

---

### Question 3: "What's the failure risk for sensor 146?"

```bash
curl -X POST http://localhost:5002/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the failure risk for sensor 146?","use_ai":false}'
```

**Expected Answer**:
```json
{
  "success": true,
  "answer": "🔴 Sensor 146 on IoT_VidrioAndino: HIGH risk (85/100). Factors: Prediction exceeds normal range in 40.0% of forecasts; Predicted change rate 3.2x faster than recent trend",
  "risk_assessment": {
    "risk_level": "high",
    "risk_score": 85,
    "risk_factors": [
      "Prediction exceeds normal range in 40.0% of forecasts",
      "Predicted change rate 3.2x faster than recent trend"
    ],
    "recommended_action": "Schedule maintenance within 48 hours..."
  }
}
```

---

## Step 4: Try More Questions

### More Example Queries

```bash
# Predict another sensor
curl -X POST http://localhost:5002/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Predict sensor 147 failure","use_ai":false}'

# Check device health
curl -X POST http://localhost:5002/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Check health of sensor 80","use_ai":false}'

# Get suggestions for more queries
curl http://localhost:5002/api/v1/query/suggestions
```

---

## Python Example

```python
import requests
import json

# API endpoint
url = "http://localhost:5002/api/v1/query/ask"

# Ask a question
question = "When will sensor 146 fail?"

response = requests.post(url, json={
    "question": question,
    "use_ai": False  # Use template for faster response
})

result = response.json()

if result['success']:
    # Print answer
    print(f"Question: {question}")
    print(f"Answer: {result['answer']}\n")

    # Print risk assessment
    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print(f"Risk Level: {risk['risk_level'].upper()}")
        print(f"Risk Score: {risk['risk_score']}/100")

        if risk.get('time_to_failure_hours'):
            print(f"Time to Failure: {risk['time_to_failure_hours']} hours")

        print(f"Action: {risk['recommended_action']}\n")

    # Print forecast preview
    if 'forecasts' in result:
        print("Forecast Preview (next 3 hours):")
        for forecast in result['forecasts'][:3]:
            print(f"  +{forecast['hours_ahead']}h: {forecast['predicted_value']:.2f} "
                  f"({forecast['confidence_lower']:.2f} - {forecast['confidence_upper']:.2f})")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
    if 'suggestions' in result:
        print(f"Try: {result['suggestions'][0]}")
```

---

## Common Query Patterns

### Failure Prediction

- "When will sensor X fail?"
- "Predict sensor X failure"
- "Forecast sensor X"
- "Will sensor X fail?"

### Maintenance

- "Show maintenance schedule"
- "Which devices need maintenance?"
- "What equipment should we maintain?"
- "Maintenance priorities"

### Risk Assessment

- "What's the failure risk for sensor X?"
- "Check health of sensor X"
- "Is sensor X at risk?"
- "Sensor X health status"

---

## Troubleshooting

### Error: "LSTM forecasting not available"

**Cause**: TensorFlow not installed

**Solution**:
```bash
cd /home/wil/iot-portal
source venv/bin/activate
pip install tensorflow
# Restart Flask app
```

---

### Error: "No trained model found"

**Cause**: Model not trained for sensor

**Solution**: Train model first (see Step 2)

---

### Error: "Need device ID and sensor key"

**Cause**: Query doesn't specify which sensor

**Solution**: Add sensor number to query, e.g., "sensor 146"

---

## Next Steps

1. ✅ Train models for your critical sensors
2. ✅ Set up automated queries (cron jobs)
3. ✅ Integrate with alerting system
4. ✅ Create dashboard widgets
5. ✅ Share with operations team

---

## Full Documentation

- **Integration Guide**: `LSTM_NL_QUERY_INTEGRATION_COMPLETE.md`
- **Integration Report**: `INTEGRATION_REPORT_PHASE_A_C.md`
- **LSTM API Docs**: `PHASE_A_LSTM_FORECASTING_COMPLETE.md`
- **NL Query Docs**: `PHASE_C_NL_QUERY_COMPLETE.md`
- **Test Suite**: `test_lstm_nl_integration.py`

---

**Ready in 5 minutes!** 🚀

Start asking questions about your equipment in plain English and get AI-powered predictions instantly.
