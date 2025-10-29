#!/bin/bash
# SLA Monitoring Cron Jobs - INSA CRM Platform
# Install: sudo crontab -e (add these lines)

# SLA Calculation - Every 5 minutes
# */5 * * * * cd /home/wil/insa-crm-platform/crm\ voice && ./venv/bin/python sla_calculator.py >> /var/log/sla_calculator.log 2>&1

# Daily SLA Report - Every day at 9:00 AM America/Bogota
# 0 9 * * * cd /home/wil/insa-crm-platform/crm\ voice && ./venv/bin/python sla_reporter.py --daily >> /var/log/sla_reporter.log 2>&1

# Weekly SLA Report - Every Monday at 9:00 AM America/Bogota
# 0 9 * * 1 cd /home/wil/insa-crm-platform/crm\ voice && ./venv/bin/python sla_reporter.py --weekly >> /var/log/sla_reporter.log 2>&1

# Monthly SLA Report - 1st day of month at 9:00 AM America/Bogota
# 0 9 1 * * cd /home/wil/insa-crm-platform/crm\ voice && ./venv/bin/python sla_reporter.py --monthly >> /var/log/sla_reporter.log 2>&1

# Daily Summary Generation - Every day at midnight
# 0 0 * * * cd /home/wil/insa-crm-platform/crm\ voice && ./venv/bin/python -c "from sla_database import SLADatabase; db = SLADatabase(); db.generate_daily_summary(); db.close()" >> /var/log/sla_daily_summary.log 2>&1

# INSTALLATION INSTRUCTIONS
# 1. Make this file executable:
#    chmod +x sla_monitoring_cron.sh
#
# 2. Edit crontab:
#    sudo crontab -e
#
# 3. Uncomment and add the cron jobs above (remove # at start of each line)
#
# 4. Verify cron jobs are installed:
#    sudo crontab -l
#
# 5. Check logs:
#    tail -f /var/log/sla_calculator.log
#    tail -f /var/log/sla_reporter.log

# SYSTEMD SERVICE ALTERNATIVE
# For continuous SLA calculation, create a systemd service:

# File: /etc/systemd/system/sla-calculator.service
# [Unit]
# Description=INSA CRM SLA Calculator
# After=network.target prometheus.service
#
# [Service]
# Type=simple
# User=wil
# WorkingDirectory=/home/wil/insa-crm-platform/crm voice
# ExecStart=/home/wil/insa-crm-platform/crm voice/venv/bin/python sla_calculator.py --continuous --interval 300
# Restart=always
# RestartSec=10
#
# [Install]
# WantedBy=multi-user.target

# Enable and start service:
# sudo systemctl enable sla-calculator.service
# sudo systemctl start sla-calculator.service
# sudo systemctl status sla-calculator.service

echo "SLA Monitoring Cron Configuration"
echo "=================================="
echo ""
echo "To install cron jobs:"
echo "1. sudo crontab -e"
echo "2. Add the cron job lines from this file (uncomment them first)"
echo "3. Save and exit"
echo ""
echo "OR"
echo ""
echo "To run as systemd service (recommended):"
echo "1. sudo cp this file to /etc/systemd/system/sla-calculator.service"
echo "2. sudo systemctl enable sla-calculator.service"
echo "3. sudo systemctl start sla-calculator.service"
echo ""
echo "Current time (for timezone reference): $(date)"
