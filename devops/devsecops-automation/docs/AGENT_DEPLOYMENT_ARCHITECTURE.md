# Agent Deployment Architecture
**Project**: Insa Automation Corp SecureOps Platform
**Component**: Multi-Scenario Agent Architecture
**Date**: 2025-10-11
**Version**: 1.0
**Status**: Design Phase

---

## Executive Summary

This document defines the **Insa SecureOps Agent** architecture supporting three distinct deployment scenarios:

1. **Direct Internet**: Standard SaaS deployment with agents connecting directly to cloud platform
2. **Corporate Proxy/Firewall**: Enterprise IT environments with strict egress filtering
3. **IT/OT Gateway**: Industrial/OT networks with air-gapped environments using jump box in DMZ

The agent is designed to be lightweight (<50MB, <5% CPU), secure (mTLS, certificate pinning), and resilient (offline caching, auto-recovery).

---

## Architecture Overview

### Agent Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Insa SecureOps Agent                         │
│                        (Version 2.0)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Agent Controller (Core)                      │ │
│  │  - Orchestration                                          │ │
│  │  - Health monitoring                                      │ │
│  │  - Auto-update mechanism                                  │ │
│  │  - Configuration management                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────┼───────────────────────────────┐    │
│  │                        │                               │    │
│  ▼                        ▼                               ▼    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │   Security   │  │  Scanning    │  │   Log Collection │    │
│  │   Module     │  │  Module      │  │   Module         │    │
│  ├──────────────┤  ├──────────────┤  ├──────────────────┤    │
│  │ Wazuh Agent  │  │ Trivy        │  │ File Watcher     │    │
│  │ FIM          │  │ Nmap         │  │ Syslog           │    │
│  │ Rootkit Det  │  │ OWASP ZAP    │  │ App Logs         │    │
│  │ Log Analysis │  │ Custom       │  │ JSON Parsing     │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Communication Layer                               │ │
│  │  - mTLS encryption                                        │ │
│  │  - Certificate pinning                                    │ │
│  │  - Heartbeat (60s)                                        │ │
│  │  - Data batching                                          │ │
│  │  - Local queue (offline caching)                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Transport Adapter (Scenario-Specific)             │ │
│  │  - Direct HTTPS                                           │ │
│  │  - HTTP Proxy                                             │ │
│  │  - Gateway Forward                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Insa SecureOps Platform     │
              │  (iac1: 100.100.101.1)       │
              │  api.insa-automation.com     │
              └──────────────────────────────┘
```

### Key Design Principles

1. **Modularity**: Each component (security, scanning, log collection) is independent
2. **Resilience**: Local caching ensures no data loss during network outages
3. **Security-First**: All communications encrypted, certificates pinned, zero-trust model
4. **Lightweight**: Minimal resource footprint for edge/IoT deployments
5. **Auto-Update**: Self-updating mechanism with rollback capability
6. **Multi-Platform**: Linux, Windows, macOS, Docker, Kubernetes support

---

## Deployment Scenario 1: Direct Internet

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Infrastructure                      │
│                         (On-Premises)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│   │  Web Server  │     │  App Server  │     │  Database    │  │
│   │              │     │              │     │              │  │
│   │ [Agent]      │     │ [Agent]      │     │ [Agent]      │  │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘  │
│          │                    │                    │           │
│          └────────────────────┼────────────────────┘           │
│                               │                                │
│   ┌──────────────┐            │            ┌──────────────┐   │
│   │  IoT Device  │            │            │  Container   │   │
│   │              │            │            │  Host        │   │
│   │ [Agent]      │            │            │ [Agent]      │   │
│   └──────┬───────┘            │            └──────┬───────┘   │
│          │                    │                   │            │
│          └────────────────────┼───────────────────┘            │
│                               │                                │
└───────────────────────────────┼────────────────────────────────┘
                                │
                                │ HTTPS/TLS 1.3
                                │ Port 443
                                │ mTLS Authentication
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Internet Firewall   │
                    │   (Client Egress)     │
                    └───────────┬───────────┘
                                │
                                │ Allowed Outbound:
                                │ - api.insa-automation.com:443
                                │ - updates.insa-automation.com:443
                                │
                                ▼
                    ┌───────────────────────┐
                    │      Internet         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   WAF / CDN           │
                    │   (Cloudflare)        │
                    └───────────┬───────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │   Insa SecureOps Platform (SaaS)          │
        │   api.insa-automation.com                 │
        │   (iac1: 100.100.101.1)                   │
        ├───────────────────────────────────────────┤
        │                                           │
        │  ┌─────────────────────────────────────┐ │
        │  │      API Gateway                    │ │
        │  │  - Rate Limiting (per client)       │ │
        │  │  - mTLS Verification                │ │
        │  │  - Client ID Extraction             │ │
        │  └─────────────────────────────────────┘ │
        │                   │                       │
        │  ┌────────────────┼──────────────────┐   │
        │  │                │                  │   │
        │  ▼                ▼                  ▼   │
        │  [Findings]   [Metrics]          [Logs]  │
        │  DefectDojo   Prometheus         Loki    │
        │                                           │
        └───────────────────────────────────────────┘
```

### Communication Protocol

```yaml
Agent → Platform Communication:

1. Heartbeat (Every 60 seconds):
   POST https://api.insa-automation.com/v2/agents/heartbeat
   Headers:
     Authorization: Bearer <client_api_key>
     X-Agent-ID: agent_acme_webserver01
     X-Agent-Version: 2.0.5
     Content-Type: application/json
   Body:
     {
       "agent_id": "agent_acme_webserver01",
       "hostname": "webserver01.acme.com",
       "client_id": "client_acme",
       "status": "healthy",
       "uptime_seconds": 86400,
       "cpu_usage_percent": 3.2,
       "memory_usage_mb": 42,
       "disk_usage_percent": 65,
       "last_scan": "2025-10-11T20:00:00Z",
       "modules": {
         "wazuh": "active",
         "trivy": "active",
         "nmap": "idle",
         "log_collector": "active"
       }
     }
   Response:
     {
       "status": "ok",
       "commands": [],  # Remote commands from platform
       "config_version": "1.2.3",
       "config_updated": false,
       "update_available": false
     }

2. Finding Submission (On Detection):
   POST https://api.insa-automation.com/v2/findings/submit
   Headers:
     Authorization: Bearer <client_api_key>
     X-Agent-ID: agent_acme_webserver01
     Content-Type: application/json
   Body:
     {
       "agent_id": "agent_acme_webserver01",
       "client_id": "client_acme",
       "findings": [
         {
           "title": "CVE-2024-1234: Critical RCE in nginx",
           "severity": "Critical",
           "cve": "CVE-2024-1234",
           "cvss": 9.8,
           "affected_component": "nginx/1.18.0",
           "description": "Remote code execution vulnerability...",
           "remediation": "Update to nginx 1.20.2 or later",
           "detected_at": "2025-10-11T20:15:30Z",
           "source": "trivy"
         }
       ]
     }
   Response:
     {
       "status": "accepted",
       "findings_count": 1,
       "defectdojo_ids": [12345]
     }

3. Log Submission (Batched every 5 minutes):
   POST https://api.insa-automation.com/v2/logs/submit
   Headers:
     Authorization: Bearer <client_api_key>
     X-Agent-ID: agent_acme_webserver01
     Content-Type: application/json
     Content-Encoding: gzip
   Body: (gzipped JSON)
     {
       "agent_id": "agent_acme_webserver01",
       "client_id": "client_acme",
       "logs": [
         {
           "timestamp": "2025-10-11T20:10:00Z",
           "level": "ERROR",
           "source": "/var/log/nginx/error.log",
           "message": "Failed to connect to upstream"
         }
       ]
     }

4. Scan Results (On Completion):
   POST https://api.insa-automation.com/v2/scans/results
   Headers:
     Authorization: Bearer <client_api_key>
     X-Agent-ID: agent_acme_webserver01
     Content-Type: application/json
   Body:
     {
       "agent_id": "agent_acme_webserver01",
       "client_id": "client_acme",
       "scan_type": "trivy",
       "target": "nginx:1.18.0",
       "scan_duration_seconds": 45,
       "findings_count": 23,
       "results_file": "base64_encoded_trivy_json"
     }

Platform → Agent Communication:

1. Configuration Update (Push via heartbeat response):
   Response to heartbeat:
     {
       "status": "ok",
       "config_updated": true,
       "config_version": "1.2.4",
       "config_download_url": "https://api.insa-automation.com/v2/agents/config/download?token=<signed_url>"
     }

   Agent downloads new config:
     GET https://api.insa-automation.com/v2/agents/config/download?token=<signed_url>
     Response: (JSON config file)

2. Remote Commands (via heartbeat response):
   Response to heartbeat:
     {
       "status": "ok",
       "commands": [
         {
           "command_id": "cmd_789",
           "type": "scan",
           "params": {
             "scan_type": "nmap",
             "target": "192.168.1.0/24",
             "options": "-sV"
           },
           "priority": "high"
         }
       ]
     }

   Agent executes command and reports back:
     POST https://api.insa-automation.com/v2/commands/report
     Body:
       {
         "command_id": "cmd_789",
         "status": "completed",
         "result": "Scan completed, 12 hosts discovered"
       }

3. Agent Update (via heartbeat response):
   Response to heartbeat:
     {
       "status": "ok",
       "update_available": true,
       "update_version": "2.0.6",
       "update_url": "https://updates.insa-automation.com/agent/v2.0.6/linux-amd64",
       "update_checksum": "sha256:abc123..."
     }

   Agent downloads, verifies, and updates itself
```

### Security Features

```yaml
Transport Security:
  Protocol: HTTPS/TLS 1.3
  Certificate: Let's Encrypt (auto-renewed)
  mTLS: Client certificate issued per agent
  Certificate Pinning: Agent verifies server certificate thumbprint
  Cipher Suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
    - TLS_AES_128_GCM_SHA256

Authentication:
  Method 1: API Key (Bearer token)
    - Unique per client
    - Rotatable via portal
    - Scoped permissions

  Method 2: Client Certificate (mTLS)
    - Issued during onboarding
    - Embedded in agent binary
    - Short-lived (90 days), auto-renewed

Authorization:
  Client Isolation: Row-level security in database
  Rate Limiting:
    - Basic: 100 requests/min
    - Pro: 500 requests/min
    - Enterprise: 2000 requests/min

Data Encryption:
  In Transit: TLS 1.3 encryption
  At Rest: AES-256 encryption of local cache
  Secrets: API keys stored in OS keychain (Linux: libsecret, Windows: DPAPI, macOS: Keychain)

Certificate Pinning Implementation:
  # Python example
  import requests
  import hashlib

  PINNED_CERT_SHA256 = "abc123...def456"  # Server cert thumbprint

  def verify_pin(cert_der):
      cert_hash = hashlib.sha256(cert_der).hexdigest()
      if cert_hash != PINNED_CERT_SHA256:
          raise Exception("Certificate pinning failed!")

  # Custom SSLContext with pinning
  session = requests.Session()
  session.verify = verify_pin
```

### Firewall Rules Required (Client Side)

```bash
# Outbound HTTPS to Insa API
iptables -A OUTPUT -p tcp -d api.insa-automation.com --dport 443 -j ACCEPT

# Outbound HTTPS to Insa Updates Server
iptables -A OUTPUT -p tcp -d updates.insa-automation.com --dport 443 -j ACCEPT

# DNS resolution
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Block all other outbound by default (optional, for strict environments)
iptables -A OUTPUT -j DROP
```

---

## Deployment Scenario 2: Corporate Proxy/Firewall

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  Client Corporate Network                       │
│                    (Enterprise IT)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Internal Network (10.0.0.0/8)                 │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Server A │  │ Server B │  │ Server C │              │   │
│  │  │ [Agent]  │  │ [Agent]  │  │ [Agent]  │              │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │   │
│  │       │             │             │                     │   │
│  │       └─────────────┼─────────────┘                     │   │
│  │                     │                                   │   │
│  └─────────────────────┼───────────────────────────────────┘   │
│                        │                                       │
│                        │ Proxy configured in agent             │
│                        │ HTTP_PROXY=proxy.corp.com:8080        │
│                        │ HTTPS_PROXY=proxy.corp.com:8080       │
│                        │                                       │
│                        ▼                                       │
│            ┌──────────────────────┐                            │
│            │  Corporate Proxy     │                            │
│            │  (Squid/Zscaler)     │                            │
│            │  proxy.corp.com:8080 │                            │
│            ├──────────────────────┤                            │
│            │ - SSL Inspection     │ ◄─ Option 1: SSL Intercept│
│            │ - URL Filtering      │ ◄─ Option 2: Allow CONNECT│
│            │ - Authentication     │                            │
│            └──────────┬───────────┘                            │
│                       │                                        │
└───────────────────────┼────────────────────────────────────────┘
                        │
                        │ HTTPS CONNECT tunnel
                        │ or
                        │ Proxy-forwarded HTTPS
                        │
                        ▼
            ┌──────────────────────┐
            │  Corporate Firewall  │
            │  (Palo Alto/Fortinet)│
            ├──────────────────────┤
            │ Allowed Destinations:│
            │ - api.insa-automation.com:443         │
            │ - updates.insa-automation.com:443     │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │      Internet        │
            └──────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Insa SecureOps Platform     │
        │  api.insa-automation.com     │
        └──────────────────────────────┘
```

### Proxy Configuration

```yaml
Agent Configuration File: /etc/insa-agent/config.yaml

network:
  # Option 1: HTTP/HTTPS Proxy
  proxy:
    enabled: true
    http_proxy: "http://proxy.corp.com:8080"
    https_proxy: "http://proxy.corp.com:8080"
    no_proxy: "localhost,127.0.0.1,10.0.0.0/8"  # Exclude local networks

    # Proxy Authentication (if required)
    auth:
      username: "agent_user"
      password: "encrypted:abc123..."  # Encrypted in config file

    # SSL Inspection Handling
    ssl_inspection:
      enabled: true  # If corporate proxy does SSL interception
      trust_custom_ca: true
      custom_ca_bundle: "/etc/ssl/certs/corporate-ca.pem"

  # Option 2: SOCKS5 Proxy
  socks5_proxy:
    enabled: false
    host: "socks.corp.com"
    port: 1080
    auth:
      username: "agent_user"
      password: "encrypted:abc123..."

  # Fallback / Retry Configuration
  retry:
    max_retries: 5
    backoff_multiplier: 2  # 1s, 2s, 4s, 8s, 16s
    timeout_seconds: 30

  # Certificate Pinning (still enforced even with proxy)
  certificate_pinning:
    enabled: true
    expected_thumbprint: "sha256:abc123...def456"
    allow_custom_ca: true  # For corporate SSL inspection
```

### Python Agent Implementation (Proxy Support)

```python
#!/usr/bin/env python3
# /opt/insa-agent/agent.py

import requests
import yaml
import os
import sys
import logging

# Load configuration
with open('/etc/insa-agent/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InsaAgent:
    def __init__(self, config):
        self.config = config
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()

        # Configure proxy if enabled
        if self.config['network']['proxy']['enabled']:
            proxies = {
                'http': self.config['network']['proxy']['http_proxy'],
                'https': self.config['network']['proxy']['https_proxy']
            }
            session.proxies.update(proxies)
            logger.info(f"Proxy enabled: {proxies['https']}")

            # Proxy authentication
            if 'auth' in self.config['network']['proxy']:
                from requests.auth import HTTPProxyAuth
                proxy_auth = HTTPProxyAuth(
                    self.config['network']['proxy']['auth']['username'],
                    self._decrypt_password(self.config['network']['proxy']['auth']['password'])
                )
                session.auth = proxy_auth

        # SSL verification with custom CA bundle (for corporate SSL inspection)
        if self.config['network']['proxy'].get('ssl_inspection', {}).get('enabled'):
            custom_ca = self.config['network']['proxy']['ssl_inspection']['custom_ca_bundle']
            if os.path.exists(custom_ca):
                session.verify = custom_ca
                logger.info(f"Using custom CA bundle: {custom_ca}")
            else:
                logger.warning(f"Custom CA bundle not found: {custom_ca}")

        # Certificate pinning (verify after SSL inspection)
        # Note: This is complex with SSL inspection, may need to pin the corporate CA cert instead

        # Set timeout
        session.timeout = self.config['network']['retry']['timeout_seconds']

        return session

    def _decrypt_password(self, encrypted_password):
        # Decrypt password using OS keychain or AES decryption
        if encrypted_password.startswith('encrypted:'):
            # Implementation depends on OS keychain integration
            pass
        return encrypted_password  # Placeholder

    def send_heartbeat(self):
        url = f"{self.config['platform']['api_url']}/v2/agents/heartbeat"
        headers = {
            'Authorization': f"Bearer {self.config['platform']['api_key']}",
            'X-Agent-ID': self.config['agent']['id'],
            'X-Agent-Version': self.config['agent']['version'],
            'Content-Type': 'application/json'
        }
        payload = {
            'agent_id': self.config['agent']['id'],
            'hostname': os.uname().nodename,
            'status': 'healthy',
            # ... other heartbeat data
        }

        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Heartbeat sent successfully: {response.status_code}")
            return response.json()
        except requests.exceptions.ProxyError as e:
            logger.error(f"Proxy error: {e}")
            # Retry with backoff
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error: {e}")
            # Check certificate pinning
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return None

if __name__ == '__main__':
    agent = InsaAgent(config)

    # Main loop
    import time
    while True:
        agent.send_heartbeat()
        time.sleep(60)  # Heartbeat every 60 seconds
```

### Corporate Firewall Rules

```bash
# Firewall Configuration (Palo Alto/Fortinet/pfSense)

# Allow outbound HTTPS to Insa API
Rule 1:
  Name: Allow_Insa_Agent_API
  Source: Internal_Servers (10.0.0.0/8)
  Destination: api.insa-automation.com
  Service: HTTPS (TCP/443)
  Action: Allow
  Logging: Enabled

# Allow outbound HTTPS to Insa Updates
Rule 2:
  Name: Allow_Insa_Agent_Updates
  Source: Internal_Servers (10.0.0.0/8)
  Destination: updates.insa-automation.com
  Service: HTTPS (TCP/443)
  Action: Allow
  Logging: Enabled

# URL Filtering (if using proxy)
Allowed URLs:
  - https://api.insa-automation.com/*
  - https://updates.insa-automation.com/*

# DNS resolution
Rule 3:
  Name: Allow_DNS
  Source: Internal_Servers
  Destination: Corporate_DNS_Servers
  Service: DNS (UDP/53, TCP/53)
  Action: Allow
```

### SSL Inspection Considerations

```yaml
Option 1: Allow SSL Inspection (Recommended for Enterprise)
  Pros:
    - Full visibility into encrypted traffic
    - Corporate policy compliance
    - DLP and malware scanning

  Cons:
    - Certificate pinning must be disabled or adjusted
    - Agent must trust corporate CA certificate
    - Increased latency

  Implementation:
    - Agent config: ssl_inspection.enabled = true
    - Install corporate CA cert: /etc/ssl/certs/corporate-ca.pem
    - Pin corporate CA cert instead of Insa cert

Option 2: Bypass SSL Inspection (HTTPS CONNECT Tunnel)
  Pros:
    - End-to-end encryption preserved
    - Certificate pinning works
    - No trust of corporate CA needed

  Cons:
    - No visibility for corporate IT
    - May violate corporate policy
    - Proxy can only see destination hostname

  Implementation:
    - Proxy config: Allow CONNECT method for api.insa-automation.com
    - Agent uses HTTPS CONNECT tunnel
    - Certificate pinning enforced

Recommendation:
  - Enterprise environments: Option 1 (SSL Inspection)
  - Sensitive environments: Option 2 (HTTPS Tunnel)
```

### Proxy Authentication Methods

```yaml
Method 1: Basic Authentication
  HTTP Header: Proxy-Authorization: Basic <base64(username:password)>
  Security: Weak (credentials in every request)
  Use case: Internal proxies only

Method 2: NTLM Authentication (Windows)
  Protocol: NT LAN Manager
  Integration: requests_ntlm Python library
  Security: Strong (challenge-response)
  Use case: Active Directory environments

Method 3: Kerberos Authentication
  Protocol: GSSAPI
  Integration: requests_kerberos Python library
  Security: Strong (ticket-based)
  Use case: Enterprise Windows/Linux with AD

Method 4: API Key in Proxy
  Header: X-Proxy-Token: <api_key>
  Security: Strong (rotatable keys)
  Use case: Custom corporate proxy

Example (NTLM):
  from requests_ntlm import HttpNtlmAuth

  session.proxies = {
      'http': 'http://proxy.corp.com:8080',
      'https': 'http://proxy.corp.com:8080'
  }
  session.auth = HttpNtlmAuth('DOMAIN\\username', 'password')
```

---

## Deployment Scenario 3: IT/OT Gateway (Industrial Networks)

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    OT Network (Air-Gapped)                       │
│                      (192.168.100.0/24)                          │
│                   Purdue Model Level 0-2                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │     PLC     │   │     HMI     │   │  SCADA      │           │
│  │ (Level 1)   │   │ (Level 1-2) │   │ (Level 2)   │           │
│  │             │   │             │   │             │           │
│  │ [Agent]     │   │ [Agent]     │   │ [Agent]     │           │
│  │ READ-ONLY   │   │ READ-ONLY   │   │ READ-ONLY   │           │
│  └─────┬───────┘   └─────┬───────┘   └─────┬───────┘           │
│        │                 │                 │                    │
│        └─────────────────┼─────────────────┘                    │
│                          │                                      │
│  ┌────────────────────────────────────────────────────┐         │
│  │       OT Network Switch (Industrial Grade)         │         │
│  │       - VLAN Segmentation                          │         │
│  │       - Port Security                              │         │
│  └─────────────────────┬──────────────────────────────┘         │
│                        │                                        │
│                        │ VLAN 100 (OT Monitoring)               │
│                        │                                        │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         │ Data Diode or Firewall (Unidirectional)
                         │ OT → DMZ ONLY (no reverse traffic)
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                       DMZ (Level 3)                              │
│                   (172.16.0.0/24)                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          IT/OT Gateway / Jump Box                       │    │
│  │          (Ubuntu/RHEL Server)                           │    │
│  │          172.16.0.10                                    │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │     Insa SecureOps Gateway Agent                 │  │    │
│  │  │     (Aggregator + Forwarder)                     │  │    │
│  │  ├──────────────────────────────────────────────────┤  │    │
│  │  │  - Collects data from OT agents                  │  │    │
│  │  │  - Local buffer (72 hours)                       │  │    │
│  │  │  - Encryption & compression                      │  │    │
│  │  │  - Forwards to cloud when connected              │  │    │
│  │  └──────────────────┬───────────────────────────────┘  │    │
│  │                     │                                  │    │
│  │  ┌──────────────────┴──────────────────────────────┐   │    │
│  │  │     Local Storage (SQLite/PostgreSQL)           │   │    │
│  │  │     - Buffered findings                         │   │    │
│  │  │     - Buffered logs                             │   │    │
│  │  │     - Metrics history                           │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                         │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │ HTTPS/TLS 1.3
                             │ Port 443
                             │ Outbound only
                             │
                             ▼
                 ┌──────────────────────┐
                 │  Corporate Firewall  │
                 │  (Level 3.5)         │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │     Internet         │
                 └──────────┬───────────┘
                            │
                            ▼
         ┌──────────────────────────────────┐
         │  Insa SecureOps Platform (SaaS)  │
         │  api.insa-automation.com         │
         └──────────────────────────────────┘
```

### OT Agent Configuration (Read-Only Mode)

```yaml
# /etc/insa-agent/config.yaml (OT Network Agents)

agent:
  id: "agent_acme_ot_plc01"
  mode: "ot_readonly"  # Special mode for OT environments
  hostname: "plc01.ot.acme.com"

# OT Network Configuration
network:
  gateway:
    enabled: true
    gateway_host: "172.16.0.10"  # DMZ jump box
    gateway_port: 8443
    protocol: "https"

    # Agent pushes data to gateway (not directly to cloud)
    direct_cloud: false

  # Offline caching (extended for OT environments)
  offline_cache:
    enabled: true
    max_size_mb: 1000  # 1GB local cache
    retention_hours: 168  # 7 days
    cache_path: "/var/lib/insa-agent/cache"

# OT-Specific Safety Controls
safety:
  # Never interfere with safety systems
  read_only: true  # Agent NEVER writes to OT devices

  # No active scanning on OT networks
  scanning:
    active_scans: false  # No Nmap, no ZAP
    passive_monitoring: true  # Only log collection

  # Resource limits (critical for OT devices)
  resources:
    max_cpu_percent: 2  # Very low CPU usage
    max_memory_mb: 30   # Very low memory
    priority: "low"     # Background process

  # No remote commands from platform
  remote_commands:
    enabled: false  # Disable all remote execution

# Modules enabled in OT mode
modules:
  wazuh:
    enabled: true
    mode: "read_only"
    monitored_files:
      - "/var/log/plc/*.log"
      - "/etc/plc/config/*"
    fim_enabled: true
    rootkit_check: false  # Too invasive for OT

  trivy:
    enabled: false  # No container scanning on PLCs

  nmap:
    enabled: false  # No network scanning in OT

  log_collector:
    enabled: true
    sources:
      - "/var/log/plc/operations.log"
      - "/var/log/plc/alarms.log"
      - "/var/log/plc/security.log"
    batch_size: 100
    batch_interval_seconds: 300  # Every 5 minutes
```

### Gateway Agent Configuration (DMZ Jump Box)

```yaml
# /etc/insa-gateway/config.yaml (DMZ Gateway)

gateway:
  id: "gateway_acme_ot_dmz01"
  role: "aggregator"
  hostname: "ot-gateway.dmz.acme.com"

# Listening for OT agents
listener:
  enabled: true
  bind_address: "0.0.0.0"
  port: 8443
  protocol: "https"

  # mTLS for OT agents
  tls:
    cert: "/etc/insa-gateway/certs/gateway.crt"
    key: "/etc/insa-gateway/certs/gateway.key"
    client_ca: "/etc/insa-gateway/certs/ot-agents-ca.crt"
    require_client_cert: true

  # Rate limiting per OT agent
  rate_limiting:
    enabled: true
    max_requests_per_minute: 60
    max_connections: 50

# Cloud forwarding
cloud:
  api_url: "https://api.insa-automation.com"
  api_key: "dd_api_key_acme_gateway_xyz789"

  # Batch forwarding (aggregate OT data)
  batching:
    enabled: true
    batch_size: 500  # Forward 500 findings at once
    batch_interval_seconds: 300  # Every 5 minutes

  # Retry with exponential backoff
  retry:
    max_retries: 10
    backoff_multiplier: 2
    max_backoff_seconds: 3600  # 1 hour

# Local buffer database
storage:
  type: "postgresql"  # Or SQLite for smaller deployments
  host: "localhost"
  port: 5432
  database: "insa_gateway_buffer"
  user: "insa_gateway"
  password: "encrypted:abc123..."

  # Buffer retention
  retention:
    max_days: 7  # Keep 7 days of buffered data
    max_size_gb: 10  # Purge old data if exceeds 10GB
    auto_cleanup: true

# Security controls
security:
  # Data diode simulation (unidirectional)
  unidirectional:
    enabled: true
    direction: "ot_to_cloud"  # Only OT → Cloud, never Cloud → OT

    # Block any commands from cloud to OT
    block_remote_commands: true

  # Encryption at rest
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_file: "/etc/insa-gateway/keys/encryption.key"

# Monitoring
monitoring:
  enabled: true

  # Gateway health metrics
  metrics:
    - buffer_size_bytes
    - ot_agents_connected
    - findings_queued
    - findings_forwarded
    - cloud_connection_status
    - last_successful_sync

  # Alerts (email to OT team)
  alerts:
    - condition: buffer_size_gb > 8
      action: email
      recipients: ["ot-team@acme.com"]

    - condition: cloud_connection_down > 1h
      action: email
      recipients: ["ot-team@acme.com"]

    - condition: ot_agent_offline > 10m
      action: email
      recipients: ["ot-team@acme.com"]
```

### Data Flow (OT → Cloud)

```yaml
Step 1: OT Agent Collects Data
  PLC Agent detects finding:
    - Log entry: "Unauthorized access attempt to PLC"
    - FIM change: "/etc/plc/config/network.conf modified"

  Agent formats finding:
    {
      "agent_id": "agent_acme_ot_plc01",
      "client_id": "client_acme",
      "timestamp": "2025-10-11T20:30:00Z",
      "severity": "High",
      "title": "Unauthorized PLC access attempt",
      "description": "Failed login from 192.168.100.50",
      "source": "wazuh",
      "ot_context": {
        "device_type": "PLC",
        "purdue_level": 1,
        "safety_critical": false
      }
    }

Step 2: OT Agent Pushes to Gateway
  HTTPS POST to gateway:
    POST https://172.16.0.10:8443/v2/findings/submit
    Headers:
      Authorization: Bearer <ot_agent_token>
      X-Agent-ID: agent_acme_ot_plc01
    Body: (finding JSON from step 1)

  Gateway authenticates via mTLS:
    - Verifies client certificate
    - Validates agent_id matches cert CN
    - Checks rate limits

  Gateway stores in local buffer:
    INSERT INTO findings_buffer (agent_id, finding_data, received_at)
    VALUES ('agent_acme_ot_plc01', '...', NOW());

Step 3: Gateway Aggregates Data
  Every 5 minutes, gateway collects buffered data:
    SELECT * FROM findings_buffer
    WHERE forwarded = FALSE
    ORDER BY received_at ASC
    LIMIT 500;  # Batch of 500

  Gateway compresses batch:
    - Converts to JSON array
    - Gzip compression
    - AES-256 encryption

  Batch structure:
    {
      "gateway_id": "gateway_acme_ot_dmz01",
      "client_id": "client_acme",
      "batch_id": "batch_20251011_203000",
      "findings_count": 500,
      "compressed": true,
      "encrypted": true,
      "findings": [...]  # Encrypted & compressed array
    }

Step 4: Gateway Forwards to Cloud
  HTTPS POST to Insa platform:
    POST https://api.insa-automation.com/v2/gateway/findings/batch
    Headers:
      Authorization: Bearer <gateway_api_key>
      X-Gateway-ID: gateway_acme_ot_dmz01
      Content-Encoding: gzip
      Content-Type: application/json
    Body: (encrypted batch from step 3)

  Platform receives and processes:
    - Decrypts batch
    - Decompresses
    - Validates signatures
    - Imports to DefectDojo (500 findings)
    - Queues for AI triage

  Platform responds:
    {
      "status": "accepted",
      "batch_id": "batch_20251011_203000",
      "findings_imported": 500,
      "defectdojo_ids": [12345, 12346, ...]
    }

Step 5: Gateway Marks as Forwarded
  UPDATE findings_buffer
  SET forwarded = TRUE, forwarded_at = NOW()
  WHERE id IN (ids_from_batch);

  Gateway logs success:
    [2025-10-11 20:30:05] Batch batch_20251011_203000 forwarded successfully (500 findings)

Step 6: Cleanup Old Data
  Daily cleanup job:
    DELETE FROM findings_buffer
    WHERE forwarded = TRUE
    AND forwarded_at < NOW() - INTERVAL '7 days';
```

### Firewall Rules (OT → DMZ → Internet)

```bash
# Firewall 1: OT Network → DMZ
# Rule: Allow OT agents to push to gateway ONLY

# Allow OT agents to gateway (port 8443)
iptables -A FORWARD -s 192.168.100.0/24 -d 172.16.0.10 -p tcp --dport 8443 -j ACCEPT

# Allow return traffic (stateful)
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Deny all other OT → DMZ traffic
iptables -A FORWARD -s 192.168.100.0/24 -d 172.16.0.0/24 -j DROP

# CRITICAL: Deny all DMZ → OT traffic (Data Diode)
iptables -A FORWARD -s 172.16.0.0/24 -d 192.168.100.0/24 -j DROP

# Logging for auditing
iptables -A FORWARD -j LOG --log-prefix "OT-DMZ-FW: "


# Firewall 2: DMZ → Internet
# Rule: Allow gateway to cloud ONLY

# Allow gateway to Insa API
iptables -A FORWARD -s 172.16.0.10 -d api.insa-automation.com -p tcp --dport 443 -j ACCEPT

# Allow gateway to Insa Updates
iptables -A FORWARD -s 172.16.0.10 -d updates.insa-automation.com -p tcp --dport 443 -j ACCEPT

# Allow return traffic (stateful)
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Deny all other DMZ → Internet traffic
iptables -A FORWARD -s 172.16.0.0/24 -j DROP

# Logging
iptables -A FORWARD -j LOG --log-prefix "DMZ-INTERNET-FW: "
```

### Purdue Model Compliance

```yaml
Purdue Model Alignment:

Level 0 (Physical Process):
  - No agents installed (sensors, actuators, etc.)
  - Safety systems never touched

Level 1 (Basic Control):
  - PLCs, RTUs with Insa agent
  - READ-ONLY mode
  - Passive monitoring only
  - No active scans
  - No remote commands

Level 2 (Supervisory Control):
  - SCADA, HMI with Insa agent
  - READ-ONLY mode
  - Log collection enabled
  - No active scans

Level 3 (Operations Management):
  - DMZ gateway/jump box
  - Aggregates data from Level 1-2
  - Forwards to cloud
  - Data diode enforced (unidirectional)

Level 3.5 (DMZ):
  - Firewall separates OT from IT/Internet
  - Strict rules (OT → DMZ → Cloud, never reverse)

Level 4-5 (Business/Enterprise):
  - Insa cloud platform
  - Security analysts use portal
  - No direct access to OT networks
```

### Safety Considerations

```yaml
Golden Rules for OT Deployments:

1. Never Touch Safety Systems:
   - IEC 61508 compliant devices: NO AGENT
   - Safety PLCs (e.g., Siemens FS CPU): NO AGENT
   - Emergency shutdown systems: NO AGENT
   - Fire & gas detection: NO AGENT

2. Read-Only Operations:
   - Agent never writes to OT devices
   - No configuration changes
   - No file modifications
   - No process control

3. Resource Protection:
   - Max 2% CPU usage
   - Max 30MB memory
   - Low OS priority
   - No impact on real-time operations

4. Network Segmentation:
   - VLANs separate OT traffic
   - Data diode (unidirectional)
   - No remote access from cloud to OT

5. Testing Before Deployment:
   - Test in dev/staging OT environment
   - Monitor resource usage for 7 days
   - Get approval from OT engineers
   - Document rollback plan

6. Incident Response:
   - If agent causes issues: KILL IMMEDIATELY
   - Pre-configured kill switch: systemctl stop insa-agent
   - Emergency contact: ot-support@insa-automation.com
   - Rollback procedure documented

7. Compliance:
   - IEC 62443 (Industrial Cybersecurity)
   - NERC CIP (Critical Infrastructure Protection)
   - ISA-99 (Security for Industrial Automation)
   - Industry-specific (FDA, FAA, etc.)
```

---

## Agent Installation Package

### Installation Methods

```yaml
Method 1: One-Line Installer (Linux)
  curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
    --api-key <your_api_key> \
    --client-id <your_client_id> \
    --scenario direct  # or proxy or ot-gateway

  What it does:
    1. Detects OS and architecture
    2. Downloads appropriate binary
    3. Verifies checksum
    4. Installs to /opt/insa-agent/
    5. Creates systemd service
    6. Generates initial config
    7. Starts agent
    8. Registers with platform

Method 2: Package Managers
  # Debian/Ubuntu
  wget https://releases.insa-automation.com/insa-agent_2.0.5_amd64.deb
  sudo dpkg -i insa-agent_2.0.5_amd64.deb
  sudo insa-agent configure --api-key <key> --client-id <id>
  sudo systemctl start insa-agent

  # RHEL/CentOS
  sudo yum install https://releases.insa-automation.com/insa-agent-2.0.5.x86_64.rpm
  sudo insa-agent configure --api-key <key> --client-id <id>
  sudo systemctl start insa-agent

  # Windows (MSI installer)
  Download: https://releases.insa-automation.com/insa-agent-2.0.5.msi
  Run installer (GUI or silent: msiexec /i insa-agent-2.0.5.msi /quiet)
  Configure via: C:\Program Files\Insa\Agent\insa-agent.exe configure

Method 3: Docker Container
  docker run -d \
    --name insa-agent \
    --restart always \
    -v /var/log:/host/var/log:ro \
    -v /etc:/host/etc:ro \
    -e INSA_API_KEY=<your_api_key> \
    -e INSA_CLIENT_ID=<your_client_id> \
    insaautomation/agent:2.0.5

Method 4: Kubernetes DaemonSet
  kubectl apply -f https://install.insa-automation.com/k8s-daemonset.yaml

  # Or with Helm
  helm repo add insa https://charts.insa-automation.com
  helm install insa-agent insa/agent \
    --set apiKey=<your_api_key> \
    --set clientId=<your_client_id>

Method 5: Offline Installer (for air-gapped environments)
  Download: https://releases.insa-automation.com/insa-agent-2.0.5-offline.tar.gz

  Contains:
    - Agent binary
    - All dependencies (Trivy DB, Nmap scripts, etc.)
    - Offline documentation
    - Configuration wizard

  Extract and run:
    tar -xzf insa-agent-2.0.5-offline.tar.gz
    cd insa-agent-2.0.5-offline/
    sudo ./install.sh --offline --api-key <key> --client-id <id>
```

### Agent Binary Structure

```yaml
Agent Package Contents:

/opt/insa-agent/
  ├── bin/
  │   ├── insa-agent           # Main agent binary (20MB)
  │   ├── trivy                # Trivy scanner (15MB)
  │   ├── nmap                 # Nmap scanner (10MB)
  │   └── wazuh-agent          # Wazuh agent (8MB)
  │
  ├── etc/
  │   ├── config.yaml          # Main configuration
  │   ├── modules.d/           # Module-specific configs
  │   │   ├── wazuh.yaml
  │   │   ├── trivy.yaml
  │   │   └── nmap.yaml
  │   └── certs/               # Certificates
  │       ├── agent.crt        # Agent client cert
  │       ├── agent.key        # Agent private key
  │       └── ca.crt           # Platform CA cert
  │
  ├── var/
  │   ├── cache/               # Local cache (for offline mode)
  │   ├── logs/                # Agent logs
  │   │   ├── agent.log
  │   │   └── modules/
  │   ├── run/                 # PID files
  │   └── lib/                 # Databases (e.g., Trivy DB)
  │
  ├── lib/
  │   └── systemd/system/
  │       └── insa-agent.service  # Systemd service file
  │
  └── share/
      ├── docs/                # Documentation
      └── examples/            # Example configs

Total Size: ~48MB (compressed), ~75MB (extracted)
```

### Auto-Update Mechanism

```yaml
Update Process:

1. Agent checks for updates (every 24 hours via heartbeat):
   Response from platform:
     {
       "update_available": true,
       "update_version": "2.0.6",
       "update_url": "https://updates.insa-automation.com/agent/v2.0.6/linux-amd64",
       "update_checksum": "sha256:abc123...def456",
       "update_release_notes": "https://docs.insa-automation.com/changelog/v2.0.6",
       "update_critical": false  # If true, update immediately
     }

2. Agent downloads update:
   - Download to /opt/insa-agent/var/updates/insa-agent-2.0.6
   - Verify checksum
   - Verify GPG signature

3. Agent prepares update:
   - Backup current binary: /opt/insa-agent/bin/insa-agent.bak
   - Stop all modules gracefully
   - Flush local cache to platform

4. Agent installs update:
   - Replace binary: mv insa-agent-2.0.6 /opt/insa-agent/bin/insa-agent
   - Set permissions: chmod +x
   - Update config if needed

5. Agent restarts:
   - systemctl restart insa-agent
   - New version checks in with platform
   - Platform confirms successful update

6. Rollback on failure:
   - If new version fails health check
   - Restore backup: mv insa-agent.bak insa-agent
   - Restart
   - Report rollback to platform

Update Policies:
  - Automatic updates: Enabled by default
  - Maintenance window: Configurable (e.g., 2-4 AM)
  - Rollout strategy: Phased (10% → 50% → 100%)
  - Critical updates: Immediate (security patches)
  - Agent can opt-out: update.auto_update = false
```

---

## Performance & Resource Requirements

```yaml
Agent Resource Footprint:

Idle State:
  CPU: <1%
  Memory: 25MB
  Disk: 50MB (binary + cache)
  Network: 1 KB/min (heartbeat only)

Active Scanning (Trivy):
  CPU: 10-20% (short burst)
  Memory: 150MB
  Disk: +100MB (temp scan data)
  Network: 5 MB (download vulnerabilities DB)
  Duration: 30-60 seconds per image

Active Scanning (Nmap):
  CPU: 5-10%
  Memory: 50MB
  Network: 100 KB (per /24 subnet)
  Duration: 5-10 minutes per /24

Log Collection:
  CPU: <1%
  Memory: 10MB
  Disk: +50MB (log buffer)
  Network: 10 KB/min (batch upload)

Total Maximum:
  CPU: <5% (average), 20% (peak during scans)
  Memory: <50MB (idle), <200MB (scanning)
  Disk: 200MB
  Network: 100 KB/min (average), 5 MB/min (scan results upload)

Platform Support:
  Linux:
    - Ubuntu 20.04+ (x86_64, ARM64)
    - RHEL/CentOS 7+ (x86_64)
    - Debian 10+ (x86_64, ARM64)
    - Alpine 3.14+ (x86_64, ARM64)

  Windows:
    - Windows Server 2016+ (x86_64)
    - Windows 10/11 (x86_64)

  macOS:
    - macOS 11+ (x86_64, ARM64/Apple Silicon)

  Containers:
    - Docker 20.10+
    - Podman 3.0+
    - Kubernetes 1.20+

  IoT/Embedded:
    - Raspberry Pi 3+ (ARM64)
    - Industrial PCs (x86_64)
    - EdgeX Foundry compatible
```

---

## Security Architecture Summary

```yaml
Encryption:
  In Transit: TLS 1.3 (AES-256-GCM)
  At Rest: AES-256-GCM (local cache)
  Certificates: mTLS with certificate pinning

Authentication:
  Method 1: API Key (Bearer token)
  Method 2: Client Certificate (mTLS)
  Method 3: Gateway Token (for OT agents)

Authorization:
  Row-Level Security: PostgreSQL RLS
  Client Isolation: Strict per-client filtering
  Rate Limiting: Per-client quotas

Data Protection:
  PII Filtering: Automatic redaction
  Log Sanitization: Remove sensitive data
  Compliance: GDPR, HIPAA, SOC 2

Zero Trust Model:
  - Every request authenticated
  - Every request authorized
  - Every request logged
  - No implicit trust
```

---

## Next Steps

This architecture supports:
1. ✅ Direct Internet (standard SaaS)
2. ✅ Corporate Proxy (enterprise IT)
3. ✅ IT/OT Gateway (industrial/OT with jump box)

Next documents:
1. **AGENT_INSTALLATION_GUIDE.md** (OS-specific installation steps)
2. **IT_OT_GATEWAY_SETUP.md** (Detailed jump box configuration)

---

**Document**: AGENT_DEPLOYMENT_ARCHITECTURE.md
**Status**: Complete
**Date**: 2025-10-11
**Author**: Claude Code for Insa Automation Corp
