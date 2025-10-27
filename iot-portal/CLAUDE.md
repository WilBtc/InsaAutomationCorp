# IoT Portal - Professional Reporting

**Type**: Flask Web Application + IoT Dashboard
**Stack**: Python, Flask, PostgreSQL (ThingsBoard), Pandas, Plotly
**Port**: 5000 (default Flask)
**Server**: LU1 Workstation (100.81.103.99)

## Quick Start
```bash
# Start portal
python3 app.py
# or
./app.py

# Enhanced version
python3 app_enhanced.py

# Background mode
nohup python3 app.py > portal.log 2>&1 &
```

## Key Paths
- **App**: `/home/wil/iot-portal/app.py` (main)
- **Enhanced**: `/home/wil/iot-portal/app_enhanced.py` (latest)
- **Reports**: `/home/wil/iot-portal/*.xlsx`, `*.zip`
- **Logs**: `/home/wil/iot-portal/*.log`

## Important Commands
```bash
# Generate reports
python3 generate_historicos_report.py
python3 generate_humidity_report.py

# Test database
PGPASSWORD='110811081108***' psql -h localhost -U postgres -d thingsboard -c "SELECT COUNT(*) FROM device;"

# Check running
ps aux | grep app.py
```

## Database
- **ThingsBoard DB**: `localhost:5432/thingsboard`
- **User**: `postgres`
- **Password**: `110811081108***`

## Protected Operations ❌
- Changing database credentials
- `DROP TABLE` on ThingsBoard database
- Deleting generated reports without backup

## Full Documentation
- App versions: `app.py`, `app_enhanced.py`, `app_mcp_upgraded.py`
- Reports: Check `*.xlsx` and `*.zip` files for examples

## Related
- ThingsBoard @ `100.105.64.109:7777` (data source)
- Grafana @ `100.81.103.99:3001` (complementary analytics)
- PostgreSQL @ Port 5432 (shared)

---
*Updated: 2025-10-04 | Connects to 47+ IoT devices, 109M+ records*
