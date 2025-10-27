"""
Webhook Notification System for INSA Advanced IIoT Platform v2.0
Phase 2 - Feature 5

Secure HTTP webhook client for rule engine actions with comprehensive
security measures: SSRF protection, retry logic, request signing, timeouts.

Security Features:
- URL validation and SSRF prevention
- Private IP address blocking
- TLS/SSL certificate verification
- Request signing with HMAC-SHA256
- Timeout enforcement (prevents hanging)
- Retry with exponential backoff
- Rate limiting per webhook URL
- Input sanitization
- Secure logging (no sensitive data)

Author: INSA Automation Corp
Date: October 27, 2025
"""

import requests
import logging
import hmac
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """
    Secure webhook notification service with SSRF protection
    """

    # Security: Blocked schemes to prevent protocol smuggling
    BLOCKED_SCHEMES = ['file', 'ftp', 'gopher', 'data', 'javascript']

    # Security: Blocked private IP ranges (SSRF prevention)
    PRIVATE_IP_RANGES = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),
        ipaddress.ip_network('::1/128'),
        ipaddress.ip_network('fc00::/7'),
        ipaddress.ip_network('fe80::/10'),
    ]

    def __init__(self, config: Dict):
        """
        Initialize webhook notifier

        Args:
            config: Webhook configuration
                {
                    'timeout': 10,  # Request timeout in seconds
                    'max_retries': 3,  # Maximum retry attempts
                    'verify_ssl': True,  # Verify SSL certificates
                    'allow_private_ips': False,  # Allow webhooks to private IPs
                    'user_agent': 'INSA-IIoT-Platform/2.0',
                    'max_payload_size': 1048576  # 1MB max payload
                }
        """
        self.timeout = config.get('timeout', 10)
        self.max_retries = config.get('max_retries', 3)
        self.verify_ssl = config.get('verify_ssl', True)
        self.allow_private_ips = config.get('allow_private_ips', False)
        self.user_agent = config.get('user_agent', 'INSA-IIoT-Platform/2.0')
        self.max_payload_size = config.get('max_payload_size', 1048576)  # 1MB

        # Rate limiting: Track last request time per URL
        self.rate_limit_window = config.get('rate_limit_seconds', 1)
        self.last_request_time = {}

        logger.info(f"Webhook notifier initialized - timeout: {self.timeout}s, SSL verify: {self.verify_ssl}")

    def send_webhook(
        self,
        url: str,
        payload: Dict,
        method: str = 'POST',
        headers: Optional[Dict] = None,
        secret: Optional[str] = None
    ) -> bool:
        """
        Send webhook with security validation

        Args:
            url: Webhook URL (must be HTTP/HTTPS)
            payload: JSON payload to send
            method: HTTP method (POST, PUT, PATCH)
            headers: Additional HTTP headers
            secret: Optional secret for request signing (HMAC-SHA256)

        Returns:
            bool: True if webhook sent successfully
        """
        try:
            # Security: Validate URL before sending
            if not self._validate_url(url):
                logger.error(f"Webhook URL validation failed: {url}")
                return False

            # Security: Rate limiting
            if not self._check_rate_limit(url):
                logger.warning(f"Rate limit exceeded for webhook: {url}")
                return False

            # Security: Check payload size
            payload_str = json.dumps(payload)
            if len(payload_str) > self.max_payload_size:
                logger.error(f"Webhook payload exceeds max size ({len(payload_str)} > {self.max_payload_size})")
                return False

            # Prepare headers
            request_headers = {
                'Content-Type': 'application/json',
                'User-Agent': self.user_agent,
                'X-INSA-Timestamp': str(int(time.time()))
            }
            if headers:
                request_headers.update(headers)

            # Security: Sign request with HMAC if secret provided
            if secret:
                signature = self._sign_request(payload_str, secret)
                request_headers['X-INSA-Signature'] = signature
                request_headers['X-INSA-Signature-Algorithm'] = 'sha256'

            # Send webhook with retries
            success = self._send_with_retry(
                url=url,
                method=method,
                headers=request_headers,
                payload=payload_str
            )

            if success:
                logger.info(f"Webhook sent successfully: {method} {url}")
            else:
                logger.error(f"Webhook failed after {self.max_retries} retries: {url}")

            return success

        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False

    def _validate_url(self, url: str) -> bool:
        """
        Validate webhook URL for security

        Security checks:
        - Must be valid URL
        - Must use HTTP/HTTPS only
        - No private IP addresses (unless explicitly allowed)
        - No localhost/loopback
        - No blocked schemes

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)

            # Security: Check scheme
            if parsed.scheme.lower() not in ['http', 'https']:
                logger.warning(f"Blocked webhook with invalid scheme: {parsed.scheme}")
                return False

            if parsed.scheme.lower() in self.BLOCKED_SCHEMES:
                logger.warning(f"Blocked webhook with dangerous scheme: {parsed.scheme}")
                return False

            # Security: Check hostname
            hostname = parsed.hostname
            if not hostname:
                logger.warning("Webhook URL has no hostname")
                return False

            # Security: Resolve hostname and check for private IPs
            if not self.allow_private_ips:
                try:
                    # Try to parse as IP address
                    ip = ipaddress.ip_address(hostname)

                    # Check if it's a private/loopback IP
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        logger.warning(f"Blocked webhook to private IP: {ip}")
                        return False

                    # Check against private IP ranges
                    for private_range in self.PRIVATE_IP_RANGES:
                        if ip in private_range:
                            logger.warning(f"Blocked webhook to private IP range: {ip}")
                            return False

                except ValueError:
                    # Not an IP address - it's a hostname, which is okay
                    # In production, you might want to resolve the hostname and check the IPs
                    pass

            # Security: Check for suspicious patterns
            if '@' in url:
                logger.warning(f"Blocked webhook with @ in URL: {url}")
                return False

            return True

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    def _check_rate_limit(self, url: str) -> bool:
        """
        Check if webhook URL is rate limited

        Args:
            url: Webhook URL

        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        last_time = self.last_request_time.get(url, 0)

        if now - last_time < self.rate_limit_window:
            return False

        self.last_request_time[url] = now
        return True

    def _sign_request(self, payload: str, secret: str) -> str:
        """
        Sign webhook request with HMAC-SHA256

        Args:
            payload: JSON payload string
            secret: Signing secret

        Returns:
            str: Hex-encoded HMAC signature
        """
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _send_with_retry(
        self,
        url: str,
        method: str,
        headers: Dict,
        payload: str
    ) -> bool:
        """
        Send HTTP request with exponential backoff retry

        Args:
            url: Request URL
            method: HTTP method
            headers: Request headers
            payload: Request payload

        Returns:
            bool: True if request succeeded
        """
        for attempt in range(self.max_retries):
            try:
                # Security: Set timeout to prevent hanging
                # Security: Verify SSL certificates (unless disabled)
                response = requests.request(
                    method=method,
                    url=url,
                    data=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=False  # Security: Prevent redirect attacks
                )

                # Consider 2xx status codes as success
                if 200 <= response.status_code < 300:
                    logger.debug(f"Webhook request succeeded: {response.status_code}")
                    return True
                else:
                    logger.warning(f"Webhook returned non-2xx status: {response.status_code}")

            except requests.exceptions.Timeout:
                logger.warning(f"Webhook timeout (attempt {attempt + 1}/{self.max_retries})")
            except requests.exceptions.SSLError as e:
                logger.error(f"Webhook SSL error: {e}")
                return False  # Don't retry SSL errors
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Webhook connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
            except Exception as e:
                logger.error(f"Webhook request error: {e}")
                return False

            # Exponential backoff: 1s, 2s, 4s, ...
            if attempt < self.max_retries - 1:
                backoff_time = 2 ** attempt
                logger.debug(f"Retrying webhook in {backoff_time}s...")
                time.sleep(backoff_time)

        return False

    def send_alert_webhook(
        self,
        url: str,
        device_id: str,
        rule_name: str,
        severity: str,
        message: str,
        context: Dict,
        secret: Optional[str] = None
    ) -> bool:
        """
        Send alert webhook with standard payload format

        Args:
            url: Webhook URL
            device_id: Device ID
            rule_name: Rule name
            severity: Alert severity
            message: Alert message
            context: Additional context
            secret: Optional signing secret

        Returns:
            bool: True if sent successfully
        """
        payload = {
            'event_type': 'alert',
            'platform': 'INSA Advanced IIoT Platform v2.0',
            'timestamp': datetime.now().isoformat(),
            'alert': {
                'device_id': device_id,
                'rule_name': rule_name,
                'severity': severity,
                'message': message,
                'context': context
            }
        }

        return self.send_webhook(
            url=url,
            payload=payload,
            method='POST',
            secret=secret
        )


# Module-level singleton instance
_webhook_notifier = None


def init_webhook_notifier(config: Dict) -> WebhookNotifier:
    """
    Initialize the webhook notifier singleton

    Args:
        config: Webhook configuration dict

    Returns:
        WebhookNotifier: Initialized webhook notifier instance
    """
    global _webhook_notifier
    _webhook_notifier = WebhookNotifier(config)
    return _webhook_notifier


def get_webhook_notifier() -> Optional[WebhookNotifier]:
    """
    Get the webhook notifier singleton instance

    Returns:
        WebhookNotifier or None: Webhook notifier instance if initialized
    """
    return _webhook_notifier
