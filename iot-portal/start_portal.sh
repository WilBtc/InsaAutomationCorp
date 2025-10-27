#!/bin/bash
# INSA IoT Portal Startup Script
# Uses port 5001 to avoid conflict with CRM backend (5000)

cd /home/wil/iot-portal
export PORT=5001
/home/wil/iot-portal/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/home/wil/iot-portal')
from app_enhanced import app
app.run(host='0.0.0.0', port=5001, debug=False)
"
