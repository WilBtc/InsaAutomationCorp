#!/usr/bin/env python3
"""
Provision ML Anomaly Detection Dashboard to Grafana
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 2

This script imports the ML monitoring dashboard into Grafana.

Usage:
    python3 provision_ml_dashboard.py

Requirements:
    - Grafana running on http://100.100.101.1:3002
    - PostgreSQL data source configured in Grafana
"""

import json
import requests
import sys

# Grafana Configuration
GRAFANA_URL = "http://100.100.101.1:3002"
GRAFANA_API_KEY = None  # Optional - set if using API key authentication
GRAFANA_USERNAME = "admin"  # Default Grafana credentials
GRAFANA_PASSWORD = "admin"  # Change if different

# Dashboard JSON file
DASHBOARD_JSON_FILE = "/home/wil/iot-portal/grafana_ml_dashboard.json"

def load_dashboard():
    """Load dashboard JSON from file"""
    try:
        with open(DASHBOARD_JSON_FILE, 'r') as f:
            dashboard_data = json.load(f)
        return dashboard_data
    except Exception as e:
        print(f"❌ Error loading dashboard JSON: {e}")
        sys.exit(1)

def provision_dashboard(dashboard_data):
    """Import dashboard into Grafana"""
    # Prepare dashboard for import
    payload = {
        "dashboard": dashboard_data,
        "overwrite": True,
        "message": "ML Anomaly Detection Dashboard - Auto-provisioned"
    }

    # API endpoint
    url = f"{GRAFANA_URL}/api/dashboards/db"

    # Prepare authentication
    if GRAFANA_API_KEY:
        headers = {
            "Authorization": f"Bearer {GRAFANA_API_KEY}",
            "Content-Type": "application/json"
        }
        auth = None
    else:
        headers = {
            "Content-Type": "application/json"
        }
        auth = (GRAFANA_USERNAME, GRAFANA_PASSWORD)

    # Import dashboard
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=auth,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            dashboard_url = f"{GRAFANA_URL}/d/{result['uid']}"
            print("✅ Dashboard provisioned successfully!")
            print(f"📊 Dashboard URL: {dashboard_url}")
            print(f"   UID: {result['uid']}")
            print(f"   ID: {result['id']}")
            print(f"   Version: {result['version']}")
            return True
        else:
            print(f"❌ Failed to provision dashboard")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Grafana: {e}")
        print(f"   Make sure Grafana is running at {GRAFANA_URL}")
        return False

def check_grafana_connection():
    """Verify Grafana is accessible"""
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Grafana is accessible at {GRAFANA_URL}")
            return True
        else:
            print(f"⚠️  Grafana returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Grafana at {GRAFANA_URL}")
        print(f"   Error: {e}")
        print(f"   Make sure Grafana is running")
        return False

def check_postgres_datasource():
    """Check if PostgreSQL data source exists in Grafana"""
    url = f"{GRAFANA_URL}/api/datasources"

    if GRAFANA_API_KEY:
        headers = {"Authorization": f"Bearer {GRAFANA_API_KEY}"}
        auth = None
    else:
        headers = {}
        auth = (GRAFANA_USERNAME, GRAFANA_PASSWORD)

    try:
        response = requests.get(url, headers=headers, auth=auth, timeout=10)

        if response.status_code == 200:
            datasources = response.json()
            postgres_ds = [ds for ds in datasources if ds['type'] == 'postgres']

            if postgres_ds:
                print(f"✅ Found {len(postgres_ds)} PostgreSQL data source(s)")
                for ds in postgres_ds:
                    print(f"   - {ds['name']} (UID: {ds['uid']})")
                return True
            else:
                print("⚠️  No PostgreSQL data source found in Grafana")
                print("   Please add a PostgreSQL data source first:")
                print("   - URL: localhost:5432")
                print("   - Database: insa_iiot")
                print("   - User: iiot_user")
                print("   - Password: iiot_secure_2025")
                return False
        else:
            print(f"⚠️  Could not check data sources (status: {response.status_code})")
            return False

    except Exception as e:
        print(f"⚠️  Could not check data sources: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("ML Anomaly Detection Dashboard Provisioner")
    print("=" * 60)

    # Step 1: Check Grafana connection
    print("\n📡 Step 1: Checking Grafana connection...")
    if not check_grafana_connection():
        print("\n❌ Cannot proceed without Grafana connection")
        sys.exit(1)

    # Step 2: Check PostgreSQL data source
    print("\n📊 Step 2: Checking PostgreSQL data source...")
    check_postgres_datasource()  # Warning only, not blocking

    # Step 3: Load dashboard
    print("\n📄 Step 3: Loading dashboard JSON...")
    dashboard_data = load_dashboard()
    print(f"✅ Loaded dashboard: {dashboard_data.get('title', 'Unknown')}")
    print(f"   Panels: {len(dashboard_data.get('panels', []))}")
    print(f"   Tags: {', '.join(dashboard_data.get('tags', []))}")

    # Step 4: Provision dashboard
    print("\n🚀 Step 4: Provisioning dashboard...")
    success = provision_dashboard(dashboard_data)

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ PROVISIONING COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Open Grafana: http://100.100.101.1:3002")
        print("2. Navigate to Dashboards > ML Anomaly Detection Dashboard")
        print("3. Verify all panels are displaying data")
        print("\nNote: If panels show 'No data', ensure:")
        print("- PostgreSQL data source is configured")
        print("- ML models table exists (run setup_ml_database.sh)")
        print("- ML API is running (python3 app_advanced.py)")
    else:
        print("❌ PROVISIONING FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("- Verify Grafana is running: systemctl status grafana-server")
        print("- Check credentials (default: admin/admin)")
        print("- Check Grafana logs: journalctl -u grafana-server -n 50")
        sys.exit(1)

if __name__ == "__main__":
    main()
