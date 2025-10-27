#!/usr/bin/env python3
"""
Grafana Integration for INSA Advanced IIoT Platform v2.0
Phase 2 - Feature 7

Provides comprehensive monitoring dashboards:
- Device health and status monitoring
- Real-time telemetry visualization
- Alert history and analysis
- Rule evaluation metrics
- System performance monitoring

Integrates with Grafana Admin MCP server for:
- Datasource provisioning
- Dashboard creation and updates
- Panel configuration
- Data queries

Author: INSA Automation Corp
Date: October 27, 2025
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GrafanaIntegration:
    """
    Grafana dashboard provisioner for INSA IIoT Platform
    """

    def __init__(self, grafana_url: str, api_key: Optional[str] = None):
        """
        Initialize Grafana integration

        Args:
            grafana_url: Grafana server URL (e.g., http://localhost:3002)
            api_key: Optional Grafana API key for authentication
        """
        self.grafana_url = grafana_url
        self.api_key = api_key

        logger.info(f"Grafana integration initialized - {grafana_url}")

    def get_datasource_config(self, db_config: Dict) -> Dict:
        """
        Generate PostgreSQL datasource configuration

        Args:
            db_config: Database configuration dict

        Returns:
            Grafana datasource configuration
        """
        return {
            "name": "INSA IIoT Platform",
            "type": "postgres",
            "url": f"{db_config['host']}:{db_config['port']}",
            "database": db_config['database'],
            "user": db_config['user'],
            "secureJsonData": {
                "password": db_config['password']
            },
            "jsonData": {
                "sslmode": "disable",
                "maxOpenConns": 10,
                "maxIdleConns": 2,
                "connMaxLifetime": 14400,
                "postgresVersion": 1400,
                "timescaledb": False
            },
            "access": "proxy",
            "isDefault": False
        }

    def create_device_overview_dashboard(self, datasource_uid: str) -> Dict:
        """
        Create device overview dashboard

        Args:
            datasource_uid: Datasource UID for queries

        Returns:
            Dashboard JSON configuration
        """
        dashboard = {
            "dashboard": {
                "title": "6. INSA IIoT - Device Overview",
                "tags": ["iiot", "devices", "monitoring"],
                "timezone": "browser",
                "schemaVersion": 38,
                "refresh": "30s",
                "panels": [
                    # Panel 1: Total Devices (Stat)
                    {
                        "id": 1,
                        "type": "stat",
                        "title": "Total Devices",
                        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": "SELECT COUNT(*) as count FROM devices WHERE active = true",
                            "format": "table"
                        }],
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "text": {},
                            "textMode": "auto",
                            "colorMode": "value",
                            "graphMode": "none",
                            "justifyMode": "auto",
                            "orientation": "auto"
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 1, "color": "green"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 2: Online Devices (Stat)
                    {
                        "id": 2,
                        "type": "stat",
                        "title": "Online Devices",
                        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT COUNT(*) as count
                                FROM devices
                                WHERE active = true
                                AND last_seen > NOW() - INTERVAL '5 minutes'
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "colorMode": "value",
                            "graphMode": "none"
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 1, "color": "green"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 3: Active Alerts (Stat)
                    {
                        "id": 3,
                        "type": "stat",
                        "title": "Active Alerts",
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT COUNT(*) as count
                                FROM alerts
                                WHERE acknowledged = false
                                AND created_at > NOW() - INTERVAL '24 hours'
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "colorMode": "value",
                            "graphMode": "none"
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "green"},
                                        {"value": 1, "color": "yellow"},
                                        {"value": 10, "color": "red"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 4: Active Rules (Stat)
                    {
                        "id": 4,
                        "type": "stat",
                        "title": "Active Rules",
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": "SELECT COUNT(*) as count FROM rules WHERE enabled = true",
                            "format": "table"
                        }],
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "colorMode": "value",
                            "graphMode": "none"
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "gray"},
                                        {"value": 1, "color": "green"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 5: Device List (Table)
                    {
                        "id": 5,
                        "type": "table",
                        "title": "Device Status",
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    name,
                                    device_type,
                                    location,
                                    active,
                                    last_seen,
                                    CASE
                                        WHEN last_seen > NOW() - INTERVAL '5 minutes' THEN 'Online'
                                        WHEN last_seen > NOW() - INTERVAL '1 hour' THEN 'Idle'
                                        ELSE 'Offline'
                                    END as status
                                FROM devices
                                ORDER BY last_seen DESC
                                LIMIT 20
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "showHeader": True,
                            "sortBy": []
                        },
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "align": "auto",
                                    "displayMode": "auto"
                                }
                            },
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "status"},
                                    "properties": [{
                                        "id": "custom.cellOptions",
                                        "value": {
                                            "type": "color-background",
                                            "mode": "basic"
                                        }
                                    }, {
                                        "id": "mappings",
                                        "value": [
                                            {"type": "value", "options": {"Online": {"color": "green"}}},
                                            {"type": "value", "options": {"Idle": {"color": "yellow"}}},
                                            {"type": "value", "options": {"Offline": {"color": "red"}}}
                                        ]
                                    }]
                                }
                            ]
                        }
                    },
                    # Panel 6: Telemetry Activity (Time series)
                    {
                        "id": 6,
                        "type": "timeseries",
                        "title": "Telemetry Data Points (Last 24h)",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    date_trunc('hour', timestamp) as time,
                                    COUNT(*) as data_points
                                FROM telemetry
                                WHERE timestamp > NOW() - INTERVAL '24 hours'
                                GROUP BY time
                                ORDER BY time
                            """,
                            "format": "time_series"
                        }],
                        "options": {
                            "tooltip": {"mode": "single"},
                            "legend": {"displayMode": "list", "placement": "bottom"}
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "fillOpacity": 10
                                }
                            }
                        }
                    },
                    # Panel 7: Alert Severity Distribution (Pie)
                    {
                        "id": 7,
                        "type": "piechart",
                        "title": "Alert Severity (Last 24h)",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    severity,
                                    COUNT(*) as count
                                FROM alerts
                                WHERE created_at > NOW() - INTERVAL '24 hours'
                                GROUP BY severity
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "legend": {"displayMode": "list", "placement": "bottom"},
                            "pieType": "pie",
                            "tooltip": {"mode": "single"}
                        },
                        "fieldConfig": {
                            "defaults": {
                                "mappings": [],
                                "color": {"mode": "palette-classic"}
                            },
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "critical"},
                                    "properties": [{"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}]
                                },
                                {
                                    "matcher": {"id": "byName", "options": "warning"},
                                    "properties": [{"id": "color", "value": {"fixedColor": "yellow", "mode": "fixed"}}]
                                },
                                {
                                    "matcher": {"id": "byName", "options": "info"},
                                    "properties": [{"id": "color", "value": {"fixedColor": "blue", "mode": "fixed"}}]
                                }
                            ]
                        }
                    }
                ]
            },
            "overwrite": True,
            "folderUid": "",
            "message": "Created by INSA IIoT Platform - Phase 2 Feature 7"
        }

        return dashboard

    def create_telemetry_dashboard(self, datasource_uid: str) -> Dict:
        """
        Create telemetry visualization dashboard

        Args:
            datasource_uid: Datasource UID for queries

        Returns:
            Dashboard JSON configuration
        """
        dashboard = {
            "dashboard": {
                "title": "7. INSA IIoT - Telemetry Visualization",
                "tags": ["iiot", "telemetry", "sensors"],
                "timezone": "browser",
                "schemaVersion": 38,
                "refresh": "30s",
                "panels": [
                    # Panel 1: Temperature Trends
                    {
                        "id": 1,
                        "type": "timeseries",
                        "title": "Temperature Readings (Last 6h)",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    timestamp as time,
                                    device_id,
                                    CAST(value AS FLOAT) as temperature
                                FROM telemetry
                                WHERE key = 'temperature'
                                AND timestamp > NOW() - INTERVAL '6 hours'
                                ORDER BY timestamp
                            """,
                            "format": "time_series"
                        }],
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {"displayMode": "list", "placement": "bottom"}
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "fillOpacity": 10
                                },
                                "unit": "celsius"
                            }
                        }
                    },
                    # Panel 2: Humidity Trends
                    {
                        "id": 2,
                        "type": "timeseries",
                        "title": "Humidity Readings (Last 6h)",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    timestamp as time,
                                    device_id,
                                    CAST(value AS FLOAT) as humidity
                                FROM telemetry
                                WHERE key = 'humidity'
                                AND timestamp > NOW() - INTERVAL '6 hours'
                                ORDER BY timestamp
                            """,
                            "format": "time_series"
                        }],
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {"displayMode": "list", "placement": "bottom"}
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "fillOpacity": 10
                                },
                                "unit": "percent"
                            }
                        }
                    },
                    # Panel 3: Recent Telemetry Data (Table)
                    {
                        "id": 3,
                        "type": "table",
                        "title": "Latest Telemetry Readings",
                        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 8},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    d.name as device,
                                    t.key as metric,
                                    t.value,
                                    t.timestamp
                                FROM telemetry t
                                JOIN devices d ON t.device_id = d.id
                                WHERE t.timestamp > NOW() - INTERVAL '1 hour'
                                ORDER BY t.timestamp DESC
                                LIMIT 50
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "showHeader": True,
                            "sortBy": [{"displayName": "timestamp", "desc": True}]
                        }
                    }
                ]
            },
            "overwrite": True,
            "folderUid": "",
            "message": "Created by INSA IIoT Platform - Phase 2 Feature 7"
        }

        return dashboard

    def create_alerts_dashboard(self, datasource_uid: str) -> Dict:
        """
        Create alerts and rule evaluation dashboard

        Args:
            datasource_uid: Datasource UID for queries

        Returns:
            Dashboard JSON configuration
        """
        dashboard = {
            "dashboard": {
                "title": "8. INSA IIoT - Alerts & Rules",
                "tags": ["iiot", "alerts", "rules"],
                "timezone": "browser",
                "schemaVersion": 38,
                "refresh": "30s",
                "panels": [
                    # Panel 1: Alert Timeline
                    {
                        "id": 1,
                        "type": "timeseries",
                        "title": "Alert Frequency (Last 24h)",
                        "gridPos": {"h": 8, "w": 16, "x": 0, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    date_trunc('hour', created_at) as time,
                                    severity,
                                    COUNT(*) as count
                                FROM alerts
                                WHERE created_at > NOW() - INTERVAL '24 hours'
                                GROUP BY time, severity
                                ORDER BY time
                            """,
                            "format": "time_series"
                        }],
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {"displayMode": "list", "placement": "bottom"}
                        },
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "bars",
                                    "fillOpacity": 80
                                }
                            }
                        }
                    },
                    # Panel 2: Alert Stats
                    {
                        "id": 2,
                        "type": "stat",
                        "title": "Total Alerts (24h)",
                        "gridPos": {"h": 4, "w": 8, "x": 16, "y": 0},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT COUNT(*) as count
                                FROM alerts
                                WHERE created_at > NOW() - INTERVAL '24 hours'
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "colorMode": "value",
                            "graphMode": "area"
                        }
                    },
                    # Panel 3: Acknowledgement Rate
                    {
                        "id": 3,
                        "type": "stat",
                        "title": "Acknowledged Rate",
                        "gridPos": {"h": 4, "w": 8, "x": 16, "y": 4},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    ROUND(100.0 * SUM(CASE WHEN acknowledged THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
                                FROM alerts
                                WHERE created_at > NOW() - INTERVAL '24 hours'
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "colorMode": "value",
                            "graphMode": "none"
                        },
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 50, "color": "yellow"},
                                        {"value": 80, "color": "green"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 4: Recent Alerts (Table)
                    {
                        "id": 4,
                        "type": "table",
                        "title": "Recent Alerts",
                        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 8},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    d.name as device,
                                    r.name as rule,
                                    a.severity,
                                    a.message,
                                    a.acknowledged,
                                    a.created_at
                                FROM alerts a
                                JOIN devices d ON a.device_id = d.id
                                LEFT JOIN rules r ON a.rule_id = r.id
                                WHERE a.created_at > NOW() - INTERVAL '24 hours'
                                ORDER BY a.created_at DESC
                                LIMIT 50
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "showHeader": True,
                            "sortBy": [{"displayName": "created_at", "desc": True}]
                        },
                        "fieldConfig": {
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "severity"},
                                    "properties": [{
                                        "id": "mappings",
                                        "value": [
                                            {"type": "value", "options": {"critical": {"color": "red"}}},
                                            {"type": "value", "options": {"warning": {"color": "yellow"}}},
                                            {"type": "value", "options": {"info": {"color": "blue"}}}
                                        ]
                                    }]
                                }
                            ]
                        }
                    },
                    # Panel 5: Rule Trigger Count
                    {
                        "id": 5,
                        "type": "bargauge",
                        "title": "Most Triggered Rules (Last 24h)",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 18},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    r.name,
                                    COUNT(*) as trigger_count
                                FROM alerts a
                                JOIN rules r ON a.rule_id = r.id
                                WHERE a.created_at > NOW() - INTERVAL '24 hours'
                                GROUP BY r.name
                                ORDER BY trigger_count DESC
                                LIMIT 10
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "orientation": "horizontal",
                            "displayMode": "gradient"
                        }
                    },
                    # Panel 6: Device Alert Count
                    {
                        "id": 6,
                        "type": "bargauge",
                        "title": "Devices with Most Alerts (Last 24h)",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 18},
                        "targets": [{
                            "datasource": {"uid": datasource_uid},
                            "rawSql": """
                                SELECT
                                    d.name,
                                    COUNT(*) as alert_count
                                FROM alerts a
                                JOIN devices d ON a.device_id = d.id
                                WHERE a.created_at > NOW() - INTERVAL '24 hours'
                                GROUP BY d.name
                                ORDER BY alert_count DESC
                                LIMIT 10
                            """,
                            "format": "table"
                        }],
                        "options": {
                            "orientation": "horizontal",
                            "displayMode": "gradient"
                        }
                    }
                ]
            },
            "overwrite": True,
            "folderUid": "",
            "message": "Created by INSA IIoT Platform - Phase 2 Feature 7"
        }

        return dashboard

    def provision_dashboards(self, datasource_uid: str) -> Dict[str, bool]:
        """
        Provision all dashboards (call this from MCP tool)

        Args:
            datasource_uid: PostgreSQL datasource UID

        Returns:
            Dictionary with provisioning status for each dashboard
        """
        results = {}

        try:
            # Create Device Overview Dashboard
            device_dashboard = self.create_device_overview_dashboard(datasource_uid)
            results['device_overview'] = True
            logger.info("Created Device Overview dashboard configuration")

            # Create Telemetry Dashboard
            telemetry_dashboard = self.create_telemetry_dashboard(datasource_uid)
            results['telemetry'] = True
            logger.info("Created Telemetry Visualization dashboard configuration")

            # Create Alerts Dashboard
            alerts_dashboard = self.create_alerts_dashboard(datasource_uid)
            results['alerts'] = True
            logger.info("Created Alerts & Rules dashboard configuration")

        except Exception as e:
            logger.error(f"Error provisioning dashboards: {e}")
            results['error'] = str(e)

        return results


# Module-level singleton
_grafana_integration = None


def init_grafana_integration(grafana_url: str, api_key: Optional[str] = None) -> GrafanaIntegration:
    """
    Initialize Grafana integration singleton

    Args:
        grafana_url: Grafana server URL
        api_key: Optional API key

    Returns:
        GrafanaIntegration instance
    """
    global _grafana_integration
    _grafana_integration = GrafanaIntegration(grafana_url, api_key)
    return _grafana_integration


def get_grafana_integration() -> Optional[GrafanaIntegration]:
    """
    Get Grafana integration singleton

    Returns:
        GrafanaIntegration instance or None
    """
    return _grafana_integration
