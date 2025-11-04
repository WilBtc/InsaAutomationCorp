#!/usr/bin/env python3
"""
n8n Complete CLI Setup - Owner & API Key Creation
==================================================

Creates n8n owner account and API key directly in SQLite database.
100% CLI automation - NO WEB UI REQUIRED!

Organization: INSA Automation Corp
Server: iac1 (100.100.101.1)
Date: October 31, 2025 20:30 UTC
"""

import sqlite3
import secrets
import uuid
from datetime import datetime
import subprocess
import os

# Configuration
DB_PATH = "/tmp/n8n_database.sqlite"
OWNER_EMAIL = "w.aroca@insaing.com"
OWNER_FIRST_NAME = "INSA"
OWNER_LAST_NAME = "Admin"
OWNER_PASSWORD = "n8n_admin_2025"
OWNER_ROLE = "global:owner"
API_KEY_LABEL = "Claude Code MCP Server"
API_KEY_FILE = "/home/wil/.n8n_api_key"

def hash_password(password):
    """Hash password using bcrypt"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        print("⚠️  bcrypt not installed, installing...")
        subprocess.run(["pip3", "install", "bcrypt"], check=True)
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_api_key():
    """Generate secure n8n API key"""
    return f"n8n_{secrets.token_urlsafe(32)}"

def main():
    print("=" * 70)
    print("n8n Complete CLI Setup - Owner & API Key Creation")
    print("=" * 70)
    print()

    # Step 1: Copy database from container
    print("[1/9] Copying database from n8n container...")
    try:
        subprocess.run([
            "docker", "cp",
            "n8n_mautic_erpnext:/home/node/.n8n/database.sqlite",
            DB_PATH
        ], check=True, capture_output=True)
        print(f"✅ Database copied to: {DB_PATH}")
    except Exception as e:
        print(f"❌ Failed to copy database: {e}")
        return False

    # Step 2: Connect to database
    print("\n[2/9] Opening database connection...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("✅ Connected to database")

    # Step 3: Check for existing owner
    print("\n[3/9] Checking for existing owner...")
    cursor.execute("SELECT id, email, roleSlug FROM user WHERE roleSlug = ?", (OWNER_ROLE,))
    existing_owner = cursor.fetchone()

    if existing_owner:
        user_id = existing_owner[0]
        print(f"ℹ️  Owner already exists: {existing_owner[1]} (ID: {user_id})")
        print("   Using existing owner account")
    else:
        print("   No owner found, creating new owner account...")

        # Generate user ID
        user_id = str(uuid.uuid4())

        # Hash password
        print("   Hashing password...")
        password_hash = hash_password(OWNER_PASSWORD)

        # Insert owner
        cursor.execute("""
            INSERT INTO user (
                id, email, firstName, lastName, password,
                roleSlug, createdAt, updatedAt, disabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            OWNER_EMAIL,
            OWNER_FIRST_NAME,
            OWNER_LAST_NAME,
            password_hash,
            OWNER_ROLE,
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%f'),
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%f'),
            0  # disabled = false
        ))

        conn.commit()
        print(f"✅ Owner created: {OWNER_EMAIL} (ID: {user_id})")

    # Step 4: Generate API key
    print("\n[4/9] Generating API key...")
    api_key = generate_api_key()
    print(f"✅ API Key generated: {api_key[:25]}...")

    # Step 5: Store API key in database
    print("\n[5/9] Storing API key in database...")

    # Check if API key already exists for this user
    cursor.execute("SELECT id FROM user_api_keys WHERE userId = ? AND label = ?", (user_id, API_KEY_LABEL))
    existing_key = cursor.fetchone()

    if existing_key:
        print(f"   API key with label '{API_KEY_LABEL}' already exists, updating...")
        cursor.execute("""
            UPDATE user_api_keys
            SET apiKey = ?, updatedAt = ?
            WHERE userId = ? AND label = ?
        """, (
            api_key,
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%f'),
            user_id,
            API_KEY_LABEL
        ))
    else:
        # Insert new API key
        api_key_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO user_api_keys (
                id, userId, label, apiKey, createdAt, updatedAt, audience
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            api_key_id,
            user_id,
            API_KEY_LABEL,
            api_key,
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%f'),
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%f'),
            'public-api'
        ))

    conn.commit()
    print(f"✅ API key stored with label: {API_KEY_LABEL}")

    # Step 6: Close database
    print("\n[6/9] Closing database connection...")
    cursor.close()
    conn.close()
    print("✅ Database connection closed")

    # Step 7: Copy database back to container
    print("\n[7/9] Copying updated database back to n8n container...")
    try:
        subprocess.run([
            "docker", "cp",
            DB_PATH,
            "n8n_mautic_erpnext:/home/node/.n8n/database.sqlite"
        ], check=True, capture_output=True)
        print("✅ Database updated in container")
    except Exception as e:
        print(f"❌ Failed to copy database back: {e}")
        return False

    # Step 8: Restart n8n container
    print("\n[8/9] Restarting n8n container...")
    try:
        subprocess.run(["docker", "restart", "n8n_mautic_erpnext"], check=True, capture_output=True)
        print("✅ Container restarted")
        print("   Waiting 10 seconds for startup...")
        import time
        time.sleep(10)
    except Exception as e:
        print(f"⚠️  Failed to restart container: {e}")

    # Step 9: Save API key to file
    print("\n[9/9] Saving API key to file...")
    try:
        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        os.chmod(API_KEY_FILE, 0o600)
        print(f"✅ API key saved to: {API_KEY_FILE}")
    except Exception as e:
        print(f"⚠️  Failed to save API key: {e}")

    # Success summary
    print()
    print("=" * 70)
    print("✅ SUCCESS! n8n Owner & API Key Created via CLI")
    print("=" * 70)
    print()
    print("Owner Account Credentials:")
    print(f"  Email:    {OWNER_EMAIL}")
    print(f"  Password: {OWNER_PASSWORD}")
    print(f"  Role:     {OWNER_ROLE}")
    print(f"  User ID:  {user_id}")
    print()
    print("API Key:")
    print(f"  {api_key}")
    print(f"  Saved to: {API_KEY_FILE}")
    print()
    print("Web UI Access:")
    print(f"  URL: http://100.100.101.1:5678")
    print(f"  Login: {OWNER_EMAIL} / {OWNER_PASSWORD}")
    print()
    print("Next Steps:")
    print("  1. Configure n8n MCP server with this API key")
    print("  2. Add n8n-mcp to ~/.mcp.json")
    print("  3. Restart Claude Code")
    print("  4. Deploy workflows via Claude Code!")
    print()

    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
