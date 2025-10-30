#!/bin/bash
# Setup ML Database Schema
# INSA Advanced IIoT Platform v2.0
# Run this to create ML tables

echo "Setting up ML database schema..."

PGPASSWORD=iiot_secure_2025 psql -h localhost -U iiot_user -d insa_iiot -f ml_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ ML database schema created successfully!"

    # Create model storage directory
    echo "Creating model storage directory..."
    sudo mkdir -p /var/lib/insa-iiot/ml_models 2>/dev/null || mkdir -p /tmp/ml_models

    if [ -d "/var/lib/insa-iiot/ml_models" ]; then
        sudo chown -R $USER:$USER /var/lib/insa-iiot/ml_models
        echo "✅ Model storage: /var/lib/insa-iiot/ml_models"
    else
        echo "⚠️  Using fallback: /tmp/ml_models"
    fi

    echo ""
    echo "ML Feature 2 database setup complete!"
    echo "Next: Add ML endpoints to app_advanced.py"
else
    echo "❌ Database setup failed"
    exit 1
fi
