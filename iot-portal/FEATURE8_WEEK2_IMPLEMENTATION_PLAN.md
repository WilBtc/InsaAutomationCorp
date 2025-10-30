# Phase 3 Feature 8: Advanced Alerting - Week 2 Implementation Plan

**Date**: October 28, 2025 20:00 UTC
**Platform**: INSA Advanced IIoT Platform v2.0
**Status**: 📋 **PLANNING COMPLETE** - Ready to start Week 2
**Duration**: 4-5 days (November 1-5, 2025)

---

## 🎯 WEEK 2 OBJECTIVES

**Goal**: Expose core alert management features via REST API + ML integration

### Deliverables (5 tasks)
1. ✅ **Week 1 Foundation** (COMPLETE)
   - Alert state machine (600 lines, 20 tests)
   - SLA tracking (700 lines, 15 tests)
   - Escalation policies (800 lines, 15 tests)
   - On-call rotation (700 lines, 15 tests)
   - Alert grouping (800 lines, 20 tests)

2. ⏳ **12 REST API Endpoints** (Week 2)
   - 6 Alert management endpoints
   - 2 Escalation policy endpoints
   - 2 On-call management endpoints
   - 2 Alert grouping endpoints

3. ⏳ **ML Integration** (Week 2)
   - Auto-create alerts from ML anomalies
   - High-confidence auto-escalation
   - ML metadata tracking

4. ⏳ **Twilio SMS Integration** (Week 2 - OPTIONAL)
   - SMS notifications for critical alerts
   - Delivery tracking
   - Rate limiting

5. ⏳ **Integration Tests** (Week 2)
   - End-to-end workflow tests
   - API authentication/authorization tests
   - ML integration tests

---

## 📋 DETAILED TASK BREAKDOWN

### Task 1: API Blueprint Setup (Day 1 Morning - 2 hours)

**Goal**: Create Flask blueprint for alert management API

#### Subtasks
1. **Create Blueprint Structure** (30 minutes)
   ```python
   # File: alert_api.py (line 1-50)
   from flask import Blueprint, request, jsonify
   from functools import wraps

   alert_bp = Blueprint('alert_api', __name__, url_prefix='/api/v1')

   # JWT authentication decorator
   def require_jwt(f):
       @wraps(f)
       def decorated(*args, **kwargs):
           token = request.headers.get('Authorization')
           if not token:
               return jsonify({'error': 'No token provided'}), 401
           # Validate JWT token
           return f(*args, **kwargs)
       return decorated

   # RBAC permission decorator
   def require_permission(permission):
       def decorator(f):
           @wraps(f)
           def decorated(*args, **kwargs):
               # Check user has permission
               return f(*args, **kwargs)
           return decorated
       return decorator
   ```

2. **Register Blueprint in app_advanced.py** (15 minutes)
   ```python
   # File: app_advanced.py (line ~2900)
   from alert_api import alert_bp

   # Register alert API blueprint
   app.register_blueprint(alert_bp)
   logger.info("✅ Alert API Blueprint registered at /api/v1")
   ```

3. **Add Swagger Documentation** (15 minutes)
   ```python
   # File: alert_api.py (line 51-100)
   from flasgger import swag_from

   @alert_bp.route('/alerts', methods=['POST'])
   @swag_from({
       'tags': ['Alerts'],
       'summary': 'Create new alert',
       'parameters': [
           {
               'name': 'body',
               'in': 'body',
               'required': True,
               'schema': {
                   'type': 'object',
                   'properties': {
                       'device_id': {'type': 'string', 'format': 'uuid'},
                       'severity': {'type': 'string', 'enum': ['critical', 'high', 'medium', 'low', 'info']},
                       'message': {'type': 'string'},
                       'metadata': {'type': 'object'}
                   },
                   'required': ['device_id', 'severity', 'message']
               }
           }
       ],
       'responses': {
           201: {'description': 'Alert created successfully'},
           400: {'description': 'Invalid request'},
           401: {'description': 'Unauthorized'}
       }
   })
   @require_jwt
   @require_permission('alerts:create')
   def create_alert():
       pass  # Implementation in next step
   ```

4. **Create Test File** (30 minutes)
   ```python
   # File: test_alert_api.py (line 1-100)
   import pytest
   import json
   from app_advanced import app

   @pytest.fixture
   def client():
       app.config['TESTING'] = True
       with app.test_client() as client:
           yield client

   @pytest.fixture
   def auth_token():
       # Get JWT token for testing
       return "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

   def test_create_alert_success(client, auth_token):
       """Test successful alert creation"""
       response = client.post('/api/v1/alerts',
           headers={'Authorization': auth_token},
           json={
               'device_id': '3a9ccfce-9773-4c72-b905-6a850e961587',
               'severity': 'critical',
               'message': 'Temperature threshold exceeded',
               'metadata': {'temperature': 85.5}
           })
       assert response.status_code == 201
       data = json.loads(response.data)
       assert 'alert_id' in data
       assert data['severity'] == 'critical'

   def test_create_alert_missing_fields(client, auth_token):
       """Test alert creation with missing required fields"""
       response = client.post('/api/v1/alerts',
           headers={'Authorization': auth_token},
           json={'device_id': '3a9ccfce-9773-4c72-b905-6a850e961587'})
       assert response.status_code == 400

   def test_create_alert_unauthorized(client):
       """Test alert creation without JWT token"""
       response = client.post('/api/v1/alerts',
           json={'device_id': '...', 'severity': 'critical'})
       assert response.status_code == 401
   ```

5. **Verify Setup** (30 minutes)
   - Run app_advanced.py, check blueprint registration
   - Access /api/v1/docs in browser
   - Verify alert endpoints visible in Swagger
   - Run initial test: `pytest test_alert_api.py::test_create_alert_unauthorized -v`

**Deliverable**: API blueprint structure ready for implementation

---

### Task 2: Alert Management Endpoints (Day 1 Afternoon - 4 hours)

**Goal**: Implement 6 alert management endpoints

#### Endpoint 1: POST /api/v1/alerts (1 hour)
**Purpose**: Create new alert

**Implementation**:
```python
# File: alert_api.py (line 150-220)
@alert_bp.route('/alerts', methods=['POST'])
@require_jwt
@require_permission('alerts:create')
def create_alert():
    """Create new alert with automatic state/SLA initialization"""
    data = request.get_json()

    # Validate required fields
    required = ['device_id', 'severity', 'message']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate severity
    valid_severities = ['critical', 'high', 'medium', 'low', 'info']
    if data['severity'] not in valid_severities:
        return jsonify({'error': 'Invalid severity'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Insert alert (triggers auto-create state and SLA)
        cur.execute("""
            INSERT INTO alerts (device_id, severity, message, metadata, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id, device_id, severity, message, created_at
        """, (data['device_id'], data['severity'], data['message'],
              json.dumps(data.get('metadata', {}))))

        alert = cur.fetchone()
        conn.commit()

        # Get initial state (auto-created by trigger)
        cur.execute("SELECT * FROM get_current_alert_state(%s)", (alert[0],))
        state = cur.fetchone()

        # Get SLA targets (auto-created by trigger)
        cur.execute("SELECT target_tta, target_ttr FROM alert_slas WHERE alert_id = %s", (alert[0],))
        sla = cur.fetchone()

        return jsonify({
            'alert_id': str(alert[0]),
            'device_id': str(alert[1]),
            'severity': alert[2],
            'message': alert[3],
            'state': state[2] if state else 'new',
            'sla_targets': {
                'tta': sla[0] if sla else None,
                'ttr': sla[1] if sla else None
            },
            'created_at': alert[4].isoformat()
        }), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create alert: {e}")
        return jsonify({'error': 'Failed to create alert'}), 500
    finally:
        cur.close()
        conn.close()
```

**Tests** (3 tests):
```python
# File: test_alert_api.py (line 101-200)
def test_create_alert_success(client, auth_token)  # ✅ Success case
def test_create_alert_missing_fields(client, auth_token)  # ✅ Missing fields
def test_create_alert_invalid_severity(client, auth_token)  # ✅ Invalid severity
```

#### Endpoint 2: GET /api/v1/alerts/{id} (45 minutes)
**Purpose**: Get alert details with current state

**Implementation**: Similar structure, JOIN with alert_states, alert_slas, alert_groups

**Tests** (2 tests):
```python
def test_get_alert_success(client, auth_token)  # ✅ Found
def test_get_alert_not_found(client, auth_token)  # ✅ Not found (404)
```

#### Endpoint 3: GET /api/v1/alerts (1 hour)
**Purpose**: List alerts with filtering

**Implementation**:
- Query parameters: severity, state, device_id, start_date, end_date, page, limit
- Default pagination: 50 per page
- Sort by created_at DESC
- JOIN with v_current_alert_states view

**Tests** (4 tests):
```python
def test_list_alerts_success(client, auth_token)  # ✅ Basic list
def test_list_alerts_filter_severity(client, auth_token)  # ✅ Filter by severity
def test_list_alerts_filter_device(client, auth_token)  # ✅ Filter by device
def test_list_alerts_pagination(client, auth_token)  # ✅ Pagination
```

#### Endpoint 4: POST /api/v1/alerts/{id}/acknowledge (30 minutes)
**Purpose**: Acknowledge alert (new → acknowledged)

**Implementation**:
- Call alert_state_machine.transition_state()
- Update alert_slas.acknowledged_at
- Calculate TTA, check for breach

**Tests** (3 tests):
```python
def test_acknowledge_alert_success(client, auth_token)  # ✅ Success
def test_acknowledge_alert_invalid_state(client, auth_token)  # ✅ Invalid transition
def test_acknowledge_alert_not_found(client, auth_token)  # ✅ Not found (404)
```

#### Endpoint 5: POST /api/v1/alerts/{id}/investigate (30 minutes)
**Purpose**: Start investigation (acknowledged → investigating)

**Implementation**: Similar to acknowledge, with assign_to_user_id optional

**Tests** (3 tests):
```python
def test_investigate_alert_success(client, auth_token)  # ✅ Success
def test_investigate_alert_with_assignment(client, auth_token)  # ✅ With user assignment
def test_investigate_alert_invalid_state(client, auth_token)  # ✅ Invalid transition
```

#### Endpoint 6: POST /api/v1/alerts/{id}/resolve (30 minutes)
**Purpose**: Resolve alert (investigating → resolved)

**Implementation**:
- Call alert_state_machine.transition_state()
- Update alert_slas.resolved_at
- Calculate TTR, check for breach
- Close alert_group if last alert

**Tests** (3 tests):
```python
def test_resolve_alert_success(client, auth_token)  # ✅ Success
def test_resolve_alert_closes_group(client, auth_token)  # ✅ Group closed
def test_resolve_alert_invalid_state(client, auth_token)  # ✅ Invalid transition
```

**Deliverable**: 6 alert management endpoints with 18 tests

---

### Task 3: Escalation & On-Call Endpoints (Day 2 Morning - 3 hours)

**Goal**: Implement 4 additional endpoints

#### Endpoint 7: GET /api/v1/escalation-policies (45 minutes)
**Purpose**: List escalation policies

**Implementation**:
- Query parameters: enabled, severity_match
- Return JSONB rules as structured JSON

**Tests** (2 tests)

#### Endpoint 8: POST /api/v1/escalation-policies (1 hour)
**Purpose**: Create escalation policy

**Implementation**:
- Validate JSONB rules structure (tiers, channels, delays)
- RBAC: admin only

**Tests** (3 tests)

#### Endpoint 9: GET /api/v1/on-call/current (30 minutes)
**Purpose**: Get current on-call user

**Implementation**:
- Call on_call_manager.get_current_on_call()
- Optional schedule_id parameter

**Tests** (2 tests)

#### Endpoint 10: GET /api/v1/on-call/schedules (45 minutes)
**Purpose**: List on-call schedules

**Implementation**:
- Query parameters: enabled, rotation_type
- Return JSONB users as structured JSON

**Tests** (2 tests)

**Deliverable**: 4 endpoints with 9 tests

---

### Task 4: Alert Grouping Endpoints (Day 2 Afternoon - 2 hours)

**Goal**: Implement 2 grouping endpoints

#### Endpoint 11: GET /api/v1/groups (1 hour)
**Purpose**: List alert groups

**Implementation**:
- Query parameters: status (active/closed), device_id, start_date, end_date
- Use v_active_alert_groups view
- Return occurrence counts

**Tests** (3 tests)

#### Endpoint 12: GET /api/v1/groups/stats (1 hour)
**Purpose**: Get platform-wide grouping statistics

**Implementation**:
- Use v_alert_group_stats view
- Calculate noise reduction percentage
- Return total groups, total alerts, reduction %

**Tests** (2 tests)

**Deliverable**: 2 endpoints with 5 tests

---

### Task 5: ML Integration (Day 3 Morning - 3 hours)

**Goal**: Auto-create alerts from ML anomaly detection

#### Implementation Steps

1. **Create ML Alert Integration Module** (1 hour)
   ```python
   # File: ml_alert_integration.py (line 1-200)
   from ml_model_manager import MLModelManager
   from alert_state_machine import AlertStateMachine
   from escalation_engine import EscalationEngine
   import logging

   logger = logging.getLogger(__name__)

   class MLAlertIntegration:
       """
       Integrates ML anomaly detection with alert management

       Features:
       - Auto-create alerts from ML anomalies
       - High-confidence auto-escalation (confidence >80%)
       - ML metadata tracking (model_id, confidence, prediction)
       - False positive tracking
       """

       def __init__(self):
           self.ml_manager = MLModelManager()
           self.state_machine = AlertStateMachine()
           self.escalation_engine = EscalationEngine()

       def handle_anomaly(self, device_id: str, metric: str, value: float,
                         model_id: int, confidence: float) -> Optional[int]:
           """
           Handle ML anomaly detection and create alert if needed

           Args:
               device_id: Device UUID
               metric: Metric name (temperature, pressure, etc.)
               value: Anomalous value
               model_id: ML model ID that detected anomaly
               confidence: Prediction confidence (0.0-1.0)

           Returns:
               alert_id if alert created, None otherwise
           """
           # Confidence threshold for alert creation
           if confidence < 0.70:
               logger.info(f"Low confidence ({confidence:.2f}), no alert created")
               return None

           # Determine severity based on confidence
           if confidence >= 0.95:
               severity = 'critical'
           elif confidence >= 0.85:
               severity = 'high'
           elif confidence >= 0.75:
               severity = 'medium'
           else:
               severity = 'low'

           # Create alert with ML metadata
           conn = get_db_connection()
           cur = conn.cursor()

           try:
               message = f"ML anomaly detected: {metric}={value:.2f} (confidence: {confidence:.2%})"
               metadata = {
                   'source': 'ml_anomaly_detection',
                   'model_id': model_id,
                   'confidence': confidence,
                   'metric': metric,
                   'value': value,
                   'threshold_exceeded': True
               }

               cur.execute("""
                   INSERT INTO alerts (device_id, severity, message, metadata, created_at)
                   VALUES (%s, %s, %s, %s, NOW())
                   RETURNING id
               """, (device_id, severity, message, json.dumps(metadata)))

               alert_id = cur.fetchone()[0]
               conn.commit()

               logger.info(f"✅ ML alert created: alert_id={alert_id}, severity={severity}, confidence={confidence:.2%}")

               # Auto-escalate high-confidence anomalies (confidence >80%)
               if confidence >= 0.80:
                   self._auto_escalate(alert_id, severity, confidence)

               return alert_id

           except Exception as e:
               conn.rollback()
               logger.error(f"Failed to create ML alert: {e}")
               return None
           finally:
               cur.close()
               conn.close()

       def _auto_escalate(self, alert_id: int, severity: str, confidence: float):
           """Auto-escalate high-confidence anomalies"""
           try:
               # Find matching escalation policy
               policy = self.escalation_engine.find_policy(severity)
               if policy:
                   self.escalation_engine.trigger_escalation(alert_id, policy['id'])
                   logger.info(f"✅ Alert {alert_id} auto-escalated (confidence: {confidence:.2%})")
           except Exception as e:
               logger.error(f"Failed to auto-escalate alert {alert_id}: {e}")
   ```

2. **Integrate with ML API** (1 hour)
   ```python
   # File: ml_api.py (add to existing predict endpoint)
   from ml_alert_integration import MLAlertIntegration

   ml_alert = MLAlertIntegration()

   @ml_bp.route('/predict', methods=['POST'])
   def predict():
       # ... existing prediction code ...

       # If anomaly detected (is_anomaly == -1)
       if prediction['is_anomaly'] == -1:
           alert_id = ml_alert.handle_anomaly(
               device_id=data['device_id'],
               metric=data['metric'],
               value=data['value'],
               model_id=model_id,
               confidence=prediction['confidence']
           )
           prediction['alert_id'] = alert_id

       return jsonify(prediction), 200
   ```

3. **Create Tests** (1 hour)
   ```python
   # File: test_ml_alert_integration.py (line 1-400)

   def test_handle_anomaly_high_confidence():
       """Test alert creation with high confidence (>90%)"""
       # confidence=0.95 → severity=critical, auto-escalation triggered

   def test_handle_anomaly_medium_confidence():
       """Test alert creation with medium confidence (70-80%)"""
       # confidence=0.75 → severity=medium, no auto-escalation

   def test_handle_anomaly_low_confidence():
       """Test no alert creation with low confidence (<70%)"""
       # confidence=0.65 → no alert created

   def test_auto_escalation_triggered():
       """Test auto-escalation for confidence >80%"""
       # confidence=0.85 → escalation policy triggered

   def test_ml_metadata_tracking():
       """Test ML metadata stored in alert"""
       # Verify model_id, confidence, metric, value in metadata

   def test_false_positive_handling():
       """Test false positive tracking"""
       # Alert created, manually resolved, track as false positive

   # ... 4 more tests (10 total)
   ```

**Deliverable**: ML integration with 10 tests

---

### Task 6: Twilio SMS Integration (Day 3 Afternoon - 3 hours) - OPTIONAL

**Goal**: Real SMS notifications for critical alerts

#### Implementation Steps

1. **Create Twilio Notifier Module** (1.5 hours)
   ```python
   # File: twilio_notifier.py (line 1-300)
   from twilio.rest import Client
   import os

   class TwilioNotifier:
       """
       SMS notification handler using Twilio API

       Features:
       - SMS sending for critical alerts
       - Delivery tracking (sent, delivered, failed)
       - Rate limiting (max 10 SMS/hour per recipient)
       - Cost tracking (SMS sent count)
       - Error handling (invalid phone numbers)
       """

       def __init__(self):
           # Load Twilio credentials from environment
           self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
           self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
           self.from_number = os.getenv('TWILIO_FROM_NUMBER')

           if not all([self.account_sid, self.auth_token, self.from_number]):
               raise ValueError("Missing Twilio credentials in environment")

           self.client = Client(self.account_sid, self.auth_token)

       def send_sms(self, to_number: str, message: str, alert_id: int) -> dict:
           """
           Send SMS notification

           Args:
               to_number: Recipient phone number (+1234567890)
               message: SMS message (max 160 chars)
               alert_id: Alert ID for tracking

           Returns:
               {
                   'sid': 'SM...',
                   'status': 'queued',
                   'alert_id': alert_id,
                   'to': to_number
               }
           """
           # Rate limiting check
           if self._is_rate_limited(to_number):
               logger.warning(f"SMS rate limit exceeded for {to_number}")
               return {'error': 'Rate limit exceeded'}

           try:
               # Send SMS via Twilio
               sms = self.client.messages.create(
                   to=to_number,
                   from_=self.from_number,
                   body=message
               )

               # Track SMS delivery
               self._track_delivery(alert_id, sms.sid, to_number, 'sent')

               logger.info(f"✅ SMS sent: sid={sms.sid}, to={to_number}, alert_id={alert_id}")

               return {
                   'sid': sms.sid,
                   'status': sms.status,
                   'alert_id': alert_id,
                   'to': to_number
               }

           except Exception as e:
               logger.error(f"Failed to send SMS: {e}")
               return {'error': str(e)}
   ```

2. **Integrate with Escalation Engine** (1 hour)
   ```python
   # File: escalation_engine.py (add SMS channel support)
   from twilio_notifier import TwilioNotifier

   self.twilio = TwilioNotifier()

   def _execute_notification(self, channel: str, recipient: str, alert_id: int):
       if channel == 'sms':
           self.twilio.send_sms(recipient, f"Critical alert: {alert_id}", alert_id)
   ```

3. **Create Tests** (30 minutes)
   ```python
   # File: test_twilio_notifier.py (line 1-400)

   @patch('twilio.rest.Client')
   def test_send_sms_success(mock_client):
       """Test successful SMS sending"""

   def test_send_sms_rate_limit():
       """Test rate limiting (max 10 SMS/hour)"""

   def test_send_sms_invalid_number():
       """Test error handling for invalid phone numbers"""

   # ... 12 more tests (15 total)
   ```

**Deliverable**: Twilio SMS integration with 15 tests

---

### Task 7: Integration Tests (Day 4 - Full Day - 6 hours)

**Goal**: End-to-end workflow validation

#### Test Scenarios (20 tests)

1. **Complete Alert Lifecycle** (3 tests)
   ```python
   def test_alert_lifecycle_end_to_end():
       """Test complete lifecycle: create → ack → investigate → resolve"""
       # 1. Create alert via API
       # 2. Verify initial state = 'new'
       # 3. Acknowledge alert via API
       # 4. Verify state = 'acknowledged', TTA calculated
       # 5. Start investigation via API
       # 6. Verify state = 'investigating'
       # 7. Resolve alert via API
       # 8. Verify state = 'resolved', TTR calculated

   def test_alert_lifecycle_with_sla_breach():
       """Test lifecycle with SLA breach detection"""
       # Similar flow, but delay to trigger breach

   def test_alert_lifecycle_with_escalation():
       """Test lifecycle with escalation triggering"""
       # Create critical alert, verify escalation triggered
   ```

2. **SLA Enforcement** (3 tests)
   ```python
   def test_sla_breach_detection_tta():
       """Test TTA breach detection"""

   def test_sla_breach_detection_ttr():
       """Test TTR breach detection"""

   def test_sla_compliance_reporting():
       """Test compliance reporting API"""
   ```

3. **Escalation Policies** (3 tests)
   ```python
   def test_escalation_multi_tier():
       """Test multi-tier escalation (tier 1 → tier 2 → tier 3)"""

   def test_escalation_cancellation_on_ack():
       """Test escalation cancellation when alert acknowledged"""

   def test_escalation_with_sms():
       """Test SMS notification in tier 2-3"""
   ```

4. **On-Call Rotation** (3 tests)
   ```python
   def test_on_call_weekly_rotation():
       """Test weekly rotation calculation"""

   def test_on_call_override():
       """Test vacation override"""

   def test_on_call_timezone_handling():
       """Test timezone-aware calculations"""
   ```

5. **Alert Grouping** (3 tests)
   ```python
   def test_alert_grouping_time_window():
       """Test 5-minute time window grouping"""

   def test_alert_grouping_deduplication():
       """Test duplicate detection"""

   def test_alert_grouping_noise_reduction():
       """Test 70%+ noise reduction"""
   ```

6. **ML Integration** (3 tests)
   ```python
   def test_ml_anomaly_to_alert():
       """Test ML anomaly detection → alert creation"""

   def test_ml_auto_escalation():
       """Test auto-escalation for high-confidence anomalies"""

   def test_ml_false_positive_tracking():
       """Test false positive handling"""
   ```

7. **Concurrent Operations** (2 tests)
   ```python
   def test_concurrent_alert_creation():
       """Test 100+ concurrent alert creations"""

   def test_concurrent_state_transitions():
       """Test concurrent state changes on same alert"""
   ```

**Deliverable**: 20 integration tests

---

## 📊 WEEK 2 SUMMARY

### Tasks Overview
| Task | Duration | Deliverable | Tests | Lines |
|------|----------|------------|-------|-------|
| **1. API Blueprint Setup** | 2 hours | Blueprint + Swagger | 3 | 150 |
| **2. Alert Endpoints** | 4 hours | 6 endpoints | 18 | 600 |
| **3. Escalation/On-Call** | 3 hours | 4 endpoints | 9 | 400 |
| **4. Alert Grouping** | 2 hours | 2 endpoints | 5 | 200 |
| **5. ML Integration** | 3 hours | ML → Alert | 10 | 350 |
| **6. Twilio SMS** | 3 hours | SMS notifications | 15 | 500 |
| **7. Integration Tests** | 6 hours | End-to-end tests | 20 | 800 |
| **TOTAL** | **23 hours** | **12 endpoints + ML + SMS** | **80** | **3,000** |

**Timeline**: 4-5 days (November 1-5, 2025)

### Code Metrics
| Metric | Week 1 | Week 2 | Total | Change |
|--------|--------|--------|-------|--------|
| **Production Code** | 5,850 | 2,250 | 8,100 | +38% |
| **Test Code** | 2,700 | 3,000 | 5,700 | +111% |
| **Total Code** | 8,550 | 5,250 | 13,800 | +61% |
| **Tests** | 85 | 80 | 165 | +94% |
| **Pass Rate** | 100% | 100% | 100% | ✅ |

### Feature Completion
| Feature | Week 1 | Week 2 | Total | Status |
|---------|--------|--------|-------|--------|
| **Core Modules** | 100% | - | 100% | ✅ Complete |
| **API Endpoints** | 0% | 100% | 100% | ⏳ Week 2 |
| **ML Integration** | 0% | 100% | 100% | ⏳ Week 2 |
| **SMS Integration** | 0% | 100% | 100% | ⏳ Week 2 |
| **Integration Tests** | 0% | 100% | 100% | ⏳ Week 2 |
| **Feature 8 Progress** | 71% | 29% | 100% | ⏳ Week 2 |

---

## 🎯 SUCCESS CRITERIA

### Week 2 Completion Checklist
- ✅ 12 REST API endpoints implemented
- ✅ All endpoints documented in Swagger
- ✅ JWT authentication on all endpoints
- ✅ RBAC permissions enforced
- ✅ ML integration complete (anomaly → alert → escalation)
- ✅ Twilio SMS integration complete (OPTIONAL)
- ✅ 80 tests created (70 minimum, 80 target)
- ✅ 100% test pass rate maintained
- ✅ Integration tests cover all workflows
- ✅ Documentation updated (API reference)

### Quality Checklist
- ✅ Type hints on all functions
- ✅ Docstrings on all endpoints
- ✅ Error handling (4xx, 5xx responses)
- ✅ Input validation (required fields, data types)
- ✅ Logging (INFO, WARNING, ERROR levels)
- ✅ Swagger documentation complete
- ✅ Test coverage >80% (target: 90%)
- ✅ Performance <100ms per API call

### Production Readiness Checklist
- ✅ All endpoints operational
- ✅ ML integration working
- ✅ SMS notifications working (if enabled)
- ✅ Integration tests passing (100%)
- ✅ No critical bugs
- ✅ Documentation complete
- ✅ Ready for Grafana dashboard (Week 3)

---

## 📋 DAILY BREAKDOWN

### Day 1 (November 1, 2025)
**Goal**: API blueprint + 6 alert management endpoints

**Morning (4 hours)**:
- ✅ Task 1: API Blueprint Setup (2 hours)
- ✅ Task 2 (Part 1): Endpoints 1-3 (2 hours)

**Afternoon (4 hours)**:
- ✅ Task 2 (Part 2): Endpoints 4-6 (2 hours)
- ✅ Write tests for endpoints 1-6 (2 hours)

**Deliverable**: 6 endpoints + 18 tests

### Day 2 (November 2, 2025)
**Goal**: 4 escalation/on-call endpoints + 2 grouping endpoints

**Morning (4 hours)**:
- ✅ Task 3: Escalation/On-Call Endpoints (3 hours)
- ✅ Write tests (1 hour)

**Afternoon (4 hours)**:
- ✅ Task 4: Alert Grouping Endpoints (2 hours)
- ✅ Write tests (1 hour)
- ✅ Integration testing (1 hour)

**Deliverable**: 6 endpoints + 14 tests

### Day 3 (November 3, 2025)
**Goal**: ML integration + Twilio SMS

**Morning (4 hours)**:
- ✅ Task 5: ML Alert Integration (3 hours)
- ✅ Write tests (1 hour)

**Afternoon (4 hours)**:
- ✅ Task 6: Twilio SMS Integration (3 hours)
- ✅ Write tests (1 hour)

**Deliverable**: ML + SMS integration + 25 tests

### Day 4 (November 4, 2025)
**Goal**: Integration tests + documentation

**Full Day (8 hours)**:
- ✅ Task 7: Integration Tests (6 hours)
- ✅ Update documentation (1 hour)
- ✅ Final verification (1 hour)

**Deliverable**: 20 integration tests + documentation

### Day 5 (November 5, 2025) - OPTIONAL
**Goal**: Polish + bug fixes

**Full Day (8 hours)**:
- ✅ Fix any failing tests
- ✅ Performance optimization
- ✅ Code review and refactoring
- ✅ Final documentation updates

**Deliverable**: 100% production ready

---

## 🚀 GETTING STARTED

### Prerequisites
- ✅ Week 1 complete (85/85 tests passing)
- ✅ Database schema deployed (5 tables, 32 objects)
- ✅ Core modules operational (5 modules)
- ✅ app_advanced.py running on port 5002

### Environment Setup
```bash
# Navigate to project directory
cd /home/wil/iot-portal

# Activate virtual environment (if using)
source venv/bin/activate

# Install Twilio SDK (for SMS integration)
pip install twilio

# Set Twilio environment variables (if using SMS)
export TWILIO_ACCOUNT_SID="AC..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_FROM_NUMBER="+1234567890"

# Verify app running
curl http://localhost:5002/health
```

### Create API Blueprint File
```bash
# Create alert_api.py
touch alert_api.py

# Open in editor
nano alert_api.py

# Start with blueprint structure (Task 1)
```

### Run First Test
```bash
# Create test file
touch test_alert_api.py

# Write first test (test_create_alert_unauthorized)
pytest test_alert_api.py::test_create_alert_unauthorized -v

# Expected: PASSED (even before implementation)
```

---

## 💡 TIPS & BEST PRACTICES

### TDD Approach
1. **Write test first** (expect failure)
2. **Implement endpoint** (minimal code)
3. **Run test** (expect pass)
4. **Refactor** (improve code quality)
5. **Repeat** for next endpoint

### API Design
- **Consistent naming**: `/api/v1/resource`
- **HTTP methods**: POST (create), GET (read), PUT (update), DELETE (delete)
- **Status codes**: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Internal Error)
- **Response format**: `{"data": {...}, "error": null}` or `{"data": null, "error": "message"}`
- **Pagination**: `{"data": [...], "page": 1, "limit": 50, "total": 100}`

### Error Handling
```python
try:
    # Database operation
    pass
except Exception as e:
    conn.rollback()
    logger.error(f"Failed to ...: {e}")
    return jsonify({'error': 'Failed to ...'}), 500
finally:
    cur.close()
    conn.close()
```

### Testing Strategy
- **Unit tests**: Test individual endpoint logic
- **Integration tests**: Test complete workflows
- **Edge cases**: Test null values, invalid inputs, concurrent operations
- **Performance tests**: Test with 100+ concurrent requests

---

## 📝 DOCUMENTATION UPDATES

### Files to Create/Update

1. **alert_api.py** (NEW)
   - 12 REST API endpoints
   - ~1,200 lines of code

2. **ml_alert_integration.py** (NEW)
   - ML anomaly → alert creation
   - ~350 lines of code

3. **twilio_notifier.py** (NEW - OPTIONAL)
   - SMS notifications
   - ~500 lines of code

4. **test_alert_api.py** (NEW)
   - API endpoint tests
   - ~1,000 lines of code

5. **test_ml_alert_integration.py** (NEW)
   - ML integration tests
   - ~400 lines of code

6. **test_twilio_notifier.py** (NEW - OPTIONAL)
   - SMS integration tests
   - ~400 lines of code

7. **test_feature8_integration.py** (NEW)
   - End-to-end workflow tests
   - ~800 lines of code

8. **app_advanced.py** (MODIFY)
   - Register alert_api blueprint
   - ~10 lines added

9. **CLAUDE.md** (UPDATE)
   - Update Phase 3 Feature 8 progress (71% → 100%)

10. **FEATURE8_WEEK2_COMPLETE.md** (CREATE)
    - Week 2 completion summary

---

## 🎊 CONCLUSION

**Week 2 Plan Status**: 📋 **READY TO START**

Week 2 will deliver:
- ✅ 12 REST API endpoints (expose all core functionality)
- ✅ ML integration (auto-create alerts from anomalies)
- ✅ Twilio SMS integration (optional, real SMS notifications)
- ✅ 80 tests (70 minimum, 80 target)
- ✅ 100% test pass rate (maintained from Week 1)
- ✅ 100% Feature 8 complete (ready for Week 3 Grafana dashboard)

**Timeline**: 4-5 days (November 1-5, 2025)
**Confidence**: ✅ **HIGH** (Week 1 TDD methodology proven)

### Next Steps
1. ✅ Review this plan with stakeholders
2. ✅ Get approval to start Week 2
3. ✅ Set up environment (Twilio credentials if using SMS)
4. ✅ Create alert_api.py and start Task 1

**Recommendation**: Start Week 2 immediately (November 1, 2025)

---

**Plan Created**: October 28, 2025 20:00 UTC
**Platform**: INSA Advanced IIoT Platform v2.0
**Feature**: Phase 3 Feature 8 - Advanced Alerting
**Week 2 Start**: November 1, 2025
**Week 2 End**: November 5, 2025 (target)
**Status**: 📋 **PLANNING COMPLETE** - Ready to execute

---

*End of Week 2 Implementation Plan*
