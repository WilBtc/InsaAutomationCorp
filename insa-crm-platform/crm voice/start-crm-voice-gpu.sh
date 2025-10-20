#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🚀 Starting CRM Voice Assistant Backend (GPU)..."
echo "Backend will be available at: http://localhost:5000"
echo ""
python3 crm-backend.py --device cuda "$@"
