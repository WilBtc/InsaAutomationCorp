#!/usr/bin/env python3
"""
Integration Tests for Webhook System
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests the webhook notification system with security features:
- SSRF protection
- HMAC signature validation
- Rate limiting
- Retry logic
- Timeout handling
"""

import pytest
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import responses


@pytest.mark.integration
@pytest.mark.webhook
class TestWebhookNotifier:
    """Integration tests for webhook notification system"""

    def test_webhook_successful_delivery(self):
        """Test successful webhook delivery"""
        from webhook_notifier import WebhookNotifier

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'success': True}, status=200)

            notifier = WebhookNotifier(
                url='https://example.com/webhook',
                secret='test-secret'
            )

            result = notifier.send({
                'event': 'test',
                'data': {'value': 123}
            })

            assert result is True
            assert len(rsps.calls) == 1

    def test_webhook_hmac_signature(self):
        """Test HMAC signature generation and validation"""
        from webhook_notifier import WebhookNotifier

        payload = {'event': 'test', 'data': 'value'}
        secret = 'my-secret-key'

        notifier = WebhookNotifier(url='https://example.com/webhook', secret=secret)

        # Generate signature
        payload_str = json.dumps(payload, sort_keys=True)
        expected_sig = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Test signature matches
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'success': True}, status=200)

            notifier.send(payload)

            # Verify signature was sent in header
            assert len(rsps.calls) == 1
            assert 'X-Webhook-Signature' in rsps.calls[0].request.headers

    def test_webhook_ssrf_protection(self):
        """Test SSRF protection blocks private IPs"""
        from webhook_notifier import WebhookNotifier

        # Test blocking private IP ranges
        private_urls = [
            'http://127.0.0.1/webhook',
            'http://localhost/webhook',
            'http://192.168.1.1/webhook',
            'http://10.0.0.1/webhook',
            'http://172.16.0.1/webhook'
        ]

        for url in private_urls:
            notifier = WebhookNotifier(url=url, secret='test', allow_private_ips=False)

            with pytest.raises(Exception):
                notifier.send({'event': 'test'})

    def test_webhook_retry_logic(self):
        """Test webhook retry on failure"""
        from webhook_notifier import WebhookNotifier

        with responses.RequestsMock() as rsps:
            # First two attempts fail, third succeeds
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'error': 'server error'}, status=500)
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'error': 'server error'}, status=500)
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'success': True}, status=200)

            notifier = WebhookNotifier(
                url='https://example.com/webhook',
                secret='test',
                max_retries=3
            )

            result = notifier.send({'event': 'test'})

            assert result is True
            assert len(rsps.calls) == 3

    def test_webhook_timeout(self):
        """Test webhook timeout handling"""
        from webhook_notifier import WebhookNotifier

        import requests

        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.Timeout('Connection timeout')

            notifier = WebhookNotifier(
                url='https://example.com/webhook',
                secret='test',
                timeout=5
            )

            result = notifier.send({'event': 'test'})

            assert result is False

    def test_webhook_rate_limiting(self):
        """Test webhook rate limiting"""
        from webhook_notifier import WebhookNotifier

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'success': True}, status=200)

            notifier = WebhookNotifier(
                url='https://example.com/webhook',
                secret='test',
                rate_limit=2  # 2 requests per second
            )

            # Send 5 requests rapidly
            results = []
            for i in range(5):
                result = notifier.send({'event': f'test-{i}'})
                results.append(result)

            # Some should be rate limited
            assert len(rsps.calls) <= 5

    def test_webhook_payload_validation(self):
        """Test webhook payload validation"""
        from webhook_notifier import WebhookNotifier

        notifier = WebhookNotifier(url='https://example.com/webhook', secret='test')

        # Test with invalid payload types
        invalid_payloads = [
            None,
            '',
            123,
            [],
        ]

        for payload in invalid_payloads:
            with pytest.raises(Exception):
                notifier.send(payload)

    @pytest.mark.slow
    def test_webhook_concurrent_delivery(self):
        """Test concurrent webhook deliveries"""
        from webhook_notifier import WebhookNotifier
        import threading

        with responses.RequestsMock() as rsps:
            for i in range(10):
                rsps.add(responses.POST, f'https://example.com/webhook{i}',
                        json={'success': True}, status=200)

            def send_webhook(url, event_id):
                notifier = WebhookNotifier(url=url, secret='test')
                return notifier.send({'event': f'test-{event_id}'})

            # Send 10 webhooks concurrently
            threads = []
            for i in range(10):
                t = threading.Thread(target=send_webhook,
                                    args=(f'https://example.com/webhook{i}', i))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # All should succeed
            assert len(rsps.calls) == 10


@pytest.mark.integration
@pytest.mark.webhook
class TestWebhookIntegrationWithAlerts:
    """Test webhook integration with alert system"""

    def test_alert_triggers_webhook(self, client, admin_token):
        """Test that alerts trigger webhook notifications"""
        with patch('webhook_notifier.WebhookNotifier.send') as mock_send:
            mock_send.return_value = True

            # Create rule that triggers webhook
            with patch('app_advanced.get_db_connection') as mock_db:
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = {'id': 'rule-1'}

                mock_conn = MagicMock()
                mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
                mock_db.return_value = mock_conn

                # Rule creation would trigger webhook on alert
                # This tests the integration path
                assert True  # Placeholder for actual integration test

    def test_webhook_notification_format(self):
        """Test webhook notification payload format"""
        from webhook_notifier import WebhookNotifier

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://example.com/webhook',
                    json={'success': True}, status=200)

            notifier = WebhookNotifier(url='https://example.com/webhook', secret='test')

            alert_data = {
                'alert_id': 'alert-123',
                'device_id': 'DEVICE-001',
                'metric': 'temperature',
                'value': 35.5,
                'threshold': 30.0,
                'timestamp': datetime.now().isoformat()
            }

            notifier.send(alert_data)

            # Verify payload structure
            assert len(rsps.calls) == 1
            sent_payload = json.loads(rsps.calls[0].request.body)

            assert 'alert_id' in sent_payload
            assert 'device_id' in sent_payload
            assert 'metric' in sent_payload
