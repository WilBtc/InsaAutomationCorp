#!/usr/bin/env python3
"""
SLA Reporter - INSA CRM Platform
Generates and emails automated SLA compliance reports

Report Types:
- Daily: Summary of SLA status (sent at 9 AM)
- Weekly: Detailed SLA report (sent Monday 9 AM)
- Monthly: Executive summary (sent 1st of month)
- Breach: Immediate notification when SLA is breached
"""

import smtplib
import logging
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from jinja2 import Template
from sla_database import SLADatabase
from sla_calculator import SLACalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SLAReporter:
    """Generate and send SLA compliance reports"""

    def __init__(self, config_path: str = "sla_thresholds.yml",
                 prometheus_url: str = "http://localhost:9090",
                 db_path: str = "/var/lib/insa-crm/sla_tracking.db",
                 smtp_host: str = "localhost",
                 smtp_port: int = 25):
        """
        Initialize SLA reporter

        Args:
            config_path: Path to SLA thresholds YAML
            prometheus_url: Prometheus URL
            db_path: SLA database path
            smtp_host: SMTP server host
            smtp_port: SMTP server port
        """
        self.db = SLADatabase(db_path)
        self.calculator = SLACalculator(config_path, prometheus_url, db_path)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info("SLA Reporter initialized")

    def _send_email(self, to: List[str], subject: str, html_body: str, text_body: Optional[str] = None):
        """
        Send email via SMTP

        Args:
            to: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = 'insa-crm-alerts@insaing.com'
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject

            # Add plain text version
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)

            logger.info(f"Email sent to {', '.join(to)}: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def generate_daily_report(self) -> str:
        """
        Generate daily SLA summary report

        Returns:
            HTML report
        """
        # Get SLA status for last 24 hours
        status = self.db.get_current_sla_status(hours=24)
        breaches = self.db.get_active_breaches()

        # Calculate overall compliance
        if status:
            avg_compliance = sum(s['compliance_pct'] for s in status) / len(status)
        else:
            avg_compliance = 0.0

        # Determine status color
        if avg_compliance >= 99.9:
            status_color = '#28a745'  # Green
            status_text = 'EXCELLENT'
        elif avg_compliance >= 99.0:
            status_color = '#ffc107'  # Yellow
            status_text = 'GOOD'
        elif avg_compliance >= 95.0:
            status_color = '#fd7e14'  # Orange
            status_text = 'POOR'
        else:
            status_color = '#dc3545'  # Red
            status_text = 'CRITICAL'

        # Generate HTML report
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .header {
            background-color: #0066cc;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .summary {
            background-color: {{ status_color }};
            color: white;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #0066cc;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .compliant {
            color: #28a745;
            font-weight: bold;
        }
        .non-compliant {
            color: #dc3545;
            font-weight: bold;
        }
        .breach {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 10px;
            margin: 10px 0;
        }
        .footer {
            margin-top: 30px;
            padding: 20px;
            background-color: #f2f2f2;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>INSA CRM Platform - Daily SLA Report</h1>
        <p>{{ date }}</p>
    </div>

    <div class="summary">
        Overall Status: {{ status_text }} ({{ overall_compliance }}%)
    </div>

    <div style="text-align: center; margin: 20px 0;">
        <div class="metric">
            <div class="metric-label">Total SLAs</div>
            <div class="metric-value">{{ total_slas }}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Active Breaches</div>
            <div class="metric-value" style="color: {{ '#dc3545' if active_breaches > 0 else '#28a745' }}">
                {{ active_breaches }}
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Compliance</div>
            <div class="metric-value">{{ overall_compliance }}%</div>
        </div>
    </div>

    <h2>SLA Status (Last 24 Hours)</h2>
    <table>
        <thead>
            <tr>
                <th>SLA Name</th>
                <th>Category</th>
                <th>Target</th>
                <th>Actual</th>
                <th>Compliance</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for sla in slas %}
            <tr>
                <td>{{ sla.sla_name }}</td>
                <td>{{ sla.category }}</td>
                <td>{{ sla.target }} {{ sla.unit }}</td>
                <td>{{ "%.2f"|format(sla.avg_actual) }} {{ sla.unit }}</td>
                <td>{{ "%.1f"|format(sla.compliance_pct) }}%</td>
                <td class="{{ 'compliant' if sla.compliance_pct >= 99.0 else 'non-compliant' }}">
                    {{ 'PASS' if sla.compliance_pct >= 99.0 else 'FAIL' }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if breaches %}
    <h2>Active SLA Breaches</h2>
    {% for breach in breaches %}
    <div class="breach">
        <strong>{{ breach.sla_name }}</strong><br>
        Started: {{ breach.breach_start }}<br>
        Duration: {{ breach.duration_seconds or 'Ongoing' }}<br>
        Target: {{ breach.target_value }}, Actual: {{ breach.actual_value }}<br>
        Severity: {{ breach.severity.value.upper() }}
    </div>
    {% endfor %}
    {% endif %}

    <div class="footer">
        <p>This is an automated report from the INSA CRM SLA Monitoring System</p>
        <p>For questions, contact: <a href="mailto:w.aroca@insaing.com">w.aroca@insaing.com</a></p>
        <p>Dashboard: <a href="http://100.100.101.1:3002/d/insa-sla-monitoring">View SLA Dashboard</a></p>
    </div>
</body>
</html>
        """)

        html = template.render(
            date=datetime.now().strftime("%Y-%m-%d"),
            status_color=status_color,
            status_text=status_text,
            overall_compliance=f"{avg_compliance:.1f}",
            total_slas=len(status),
            active_breaches=len(breaches),
            slas=status,
            breaches=breaches
        )

        return html

    def generate_weekly_report(self) -> str:
        """
        Generate weekly detailed SLA report

        Returns:
            HTML report
        """
        # Get SLA status for last 7 days
        status = self.db.get_current_sla_status(hours=168)  # 7 days

        # Get all breaches from last 7 days
        cursor = self.db.conn.cursor()
        since = datetime.utcnow() - timedelta(days=7)
        cursor.execute("""
            SELECT
                d.sla_name,
                b.breach_start,
                b.breach_end,
                b.duration_seconds,
                b.severity
            FROM sla_breaches b
            JOIN sla_definitions d ON b.sla_id = d.sla_id
            WHERE b.breach_start >= ?
            ORDER BY b.breach_start DESC
        """, (since,))

        all_breaches = cursor.fetchall()

        # Group SLAs by category
        slas_by_category = {}
        for sla in status:
            category = sla['category']
            if category not in slas_by_category:
                slas_by_category[category] = []
            slas_by_category[category].append(sla)

        # Calculate category compliance
        category_compliance = {}
        for category, slas in slas_by_category.items():
            avg = sum(s['compliance_pct'] for s in slas) / len(slas)
            category_compliance[category] = avg

        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .header {
            background-color: #0066cc;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .category {
            margin: 20px 0;
            border-left: 4px solid #0066cc;
            padding-left: 15px;
        }
        .category-header {
            font-size: 20px;
            font-weight: bold;
            color: #0066cc;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .trend-up {
            color: #28a745;
        }
        .trend-down {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>INSA CRM Platform - Weekly SLA Report</h1>
        <p>Week of {{ week_start }} to {{ week_end }}</p>
    </div>

    <h2>SLA Compliance by Category (Last 7 Days)</h2>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Average Compliance</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for category, compliance in category_compliance.items() %}
            <tr>
                <td>{{ category.title() }}</td>
                <td>{{ "%.2f"|format(compliance) }}%</td>
                <td>{{ 'PASS' if compliance >= 99.0 else 'FAIL' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% for category, slas in slas_by_category.items() %}
    <div class="category">
        <div class="category-header">{{ category.title() }} SLAs</div>
        <table>
            <thead>
                <tr>
                    <th>SLA Name</th>
                    <th>Target</th>
                    <th>Avg Actual</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Compliance</th>
                </tr>
            </thead>
            <tbody>
                {% for sla in slas %}
                <tr>
                    <td>{{ sla.sla_name }}</td>
                    <td>{{ sla.target }} {{ sla.unit }}</td>
                    <td>{{ "%.2f"|format(sla.avg_actual) }} {{ sla.unit }}</td>
                    <td>{{ "%.2f"|format(sla.min_actual) }}</td>
                    <td>{{ "%.2f"|format(sla.max_actual) }}</td>
                    <td>{{ "%.1f"|format(sla.compliance_pct) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endfor %}

    <h2>Breach Summary (Last 7 Days)</h2>
    <p>Total Breaches: {{ all_breaches|length }}</p>
    {% if all_breaches %}
    <table>
        <thead>
            <tr>
                <th>SLA Name</th>
                <th>Start Time</th>
                <th>Duration</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            {% for breach in all_breaches %}
            <tr>
                <td>{{ breach.sla_name }}</td>
                <td>{{ breach.breach_start }}</td>
                <td>{{ (breach.duration_seconds // 60) if breach.duration_seconds else 'Ongoing' }} min</td>
                <td>{{ breach.severity.upper() }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <div class="footer">
        <p>Generated by INSA CRM SLA Monitoring System</p>
    </div>
</body>
</html>
        """)

        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_end = datetime.now().strftime("%Y-%m-%d")

        html = template.render(
            week_start=week_start,
            week_end=week_end,
            category_compliance=category_compliance,
            slas_by_category=slas_by_category,
            all_breaches=all_breaches
        )

        return html

    def generate_monthly_report(self) -> str:
        """
        Generate monthly executive summary

        Returns:
            HTML report
        """
        # Get SLA status for last 30 days
        status = self.db.get_current_sla_status(hours=720)  # 30 days

        # Calculate overall statistics
        total_slas = len(status)
        if status:
            avg_compliance = sum(s['compliance_pct'] for s in status) / len(status)
            slas_meeting_target = sum(1 for s in status if s['compliance_pct'] >= 99.0)
        else:
            avg_compliance = 0.0
            slas_meeting_target = 0

        # Get total breaches
        cursor = self.db.conn.cursor()
        since = datetime.utcnow() - timedelta(days=30)
        cursor.execute("SELECT COUNT(*) as count FROM sla_breaches WHERE breach_start >= ?", (since,))
        total_breaches = cursor.fetchone()['count']

        # Get total downtime
        cursor.execute("SELECT SUM(duration_seconds) as total FROM sla_breaches WHERE breach_start >= ? AND resolved = 1", (since,))
        total_downtime_seconds = cursor.fetchone()['total'] or 0
        total_downtime_minutes = total_downtime_seconds // 60

        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .header {
            background-color: #0066cc;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .executive-summary {
            background-color: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #0066cc;
        }
        .kpi {
            display: inline-block;
            width: 23%;
            margin: 10px 1%;
            padding: 20px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .kpi-value {
            font-size: 48px;
            font-weight: bold;
            color: #0066cc;
        }
        .kpi-label {
            font-size: 14px;
            color: #666;
            margin-top: 10px;
        }
        .recommendations {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>INSA CRM Platform</h1>
        <h2>Monthly SLA Executive Summary</h2>
        <p>{{ month_year }}</p>
    </div>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>
            This report provides a comprehensive overview of SLA compliance for the INSA CRM Platform
            during the past 30 days. Overall platform performance {{ 'meets' if avg_compliance >= 99.0 else 'does not meet' }}
            the established SLA targets.
        </p>
    </div>

    <div style="text-align: center;">
        <div class="kpi">
            <div class="kpi-value">{{ "%.1f"|format(avg_compliance) }}%</div>
            <div class="kpi-label">Overall Compliance</div>
        </div>
        <div class="kpi">
            <div class="kpi-value">{{ slas_meeting_target }}/{{ total_slas }}</div>
            <div class="kpi-label">SLAs Meeting Target</div>
        </div>
        <div class="kpi">
            <div class="kpi-value">{{ total_breaches }}</div>
            <div class="kpi-label">Total Breaches</div>
        </div>
        <div class="kpi">
            <div class="kpi-value">{{ total_downtime }}</div>
            <div class="kpi-label">Total Downtime (min)</div>
        </div>
    </div>

    <h2>SLA Performance (Last 30 Days)</h2>
    <table style="width:100%; border-collapse: collapse;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px; text-align: left;">SLA Name</th>
                <th style="padding: 10px; text-align: left;">Category</th>
                <th style="padding: 10px; text-align: right;">Target</th>
                <th style="padding: 10px; text-align: right;">Actual</th>
                <th style="padding: 10px; text-align: right;">Compliance</th>
                <th style="padding: 10px; text-align: center;">Status</th>
            </tr>
        </thead>
        <tbody>
            {% for sla in slas %}
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px;">{{ sla.sla_name }}</td>
                <td style="padding: 8px;">{{ sla.category }}</td>
                <td style="padding: 8px; text-align: right;">{{ sla.target }} {{ sla.unit }}</td>
                <td style="padding: 8px; text-align: right;">{{ "%.2f"|format(sla.avg_actual) }} {{ sla.unit }}</td>
                <td style="padding: 8px; text-align: right;">{{ "%.1f"|format(sla.compliance_pct) }}%</td>
                <td style="padding: 8px; text-align: center; color: {{ '#28a745' if sla.compliance_pct >= 99.0 else '#dc3545' }};">
                    {{ '✓ PASS' if sla.compliance_pct >= 99.0 else '✗ FAIL' }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if avg_compliance < 99.0 %}
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
            <li>Review and address recurring SLA breaches</li>
            <li>Consider infrastructure scaling for performance improvements</li>
            <li>Implement additional monitoring for early breach detection</li>
            <li>Schedule technical review meeting with platform team</li>
        </ul>
    </div>
    {% endif %}

    <div class="footer" style="margin-top: 30px; padding: 20px; background-color: #f2f2f2; text-align: center;">
        <p>For detailed analysis, visit the <a href="http://100.100.101.1:3002/d/insa-sla-monitoring">SLA Dashboard</a></p>
        <p>Contact: <a href="mailto:w.aroca@insaing.com">w.aroca@insaing.com</a></p>
    </div>
</body>
</html>
        """)

        month_year = datetime.now().strftime("%B %Y")

        html = template.render(
            month_year=month_year,
            avg_compliance=avg_compliance,
            total_slas=total_slas,
            slas_meeting_target=slas_meeting_target,
            total_breaches=total_breaches,
            total_downtime=total_downtime_minutes,
            slas=status
        )

        return html

    def send_daily_report(self):
        """Generate and send daily SLA report"""
        logger.info("Generating daily SLA report...")

        html = self.generate_daily_report()

        # Get recipients from config
        recipients = self.config.get('reporting', {}).get('daily', {}).get('recipients', [])

        if not recipients:
            recipients = ['w.aroca@insaing.com']

        self._send_email(
            to=recipients,
            subject=f"[INSA CRM] Daily SLA Report - {datetime.now().strftime('%Y-%m-%d')}",
            html_body=html
        )

    def send_weekly_report(self):
        """Generate and send weekly SLA report"""
        logger.info("Generating weekly SLA report...")

        html = self.generate_weekly_report()

        # Get recipients from config
        recipients = self.config.get('reporting', {}).get('weekly', {}).get('recipients', [])

        if not recipients:
            recipients = ['w.aroca@insaing.com', 'platform-team@insaing.com']

        self._send_email(
            to=recipients,
            subject=f"[INSA CRM] Weekly SLA Report - Week of {datetime.now().strftime('%Y-%m-%d')}",
            html_body=html
        )

    def send_monthly_report(self):
        """Generate and send monthly executive summary"""
        logger.info("Generating monthly SLA report...")

        html = self.generate_monthly_report()

        # Get recipients from config
        recipients = self.config.get('reporting', {}).get('monthly', {}).get('recipients', [])

        if not recipients:
            recipients = ['w.aroca@insaing.com', 'platform-team@insaing.com', 'management@insaing.com']

        self._send_email(
            to=recipients,
            subject=f"[INSA CRM] Monthly SLA Executive Summary - {datetime.now().strftime('%B %Y')}",
            html_body=html
        )

    def send_breach_notification(self, breach_id: int):
        """
        Send immediate notification for SLA breach

        Args:
            breach_id: Breach ID from database
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT
                d.sla_name,
                b.breach_start,
                b.target_value,
                b.actual_value,
                b.severity,
                d.description
            FROM sla_breaches b
            JOIN sla_definitions d ON b.sla_id = d.sla_id
            WHERE b.breach_id = ?
        """, (breach_id,))

        row = cursor.fetchone()
        if not row:
            logger.error(f"Breach ID {breach_id} not found")
            return

        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .alert {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
        }
        .alert-title {
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="alert">
        <div class="alert-title">🚨 SLA BREACH DETECTED</div>
        <p><strong>SLA:</strong> {{ sla_name }}</p>
        <p><strong>Time:</strong> {{ breach_start }}</p>
        <p><strong>Target:</strong> {{ target_value }}</p>
        <p><strong>Actual:</strong> {{ actual_value }}</p>
        <p><strong>Severity:</strong> {{ severity.upper() }}</p>
        <p><strong>Description:</strong> {{ description }}</p>
    </div>
    <p>View details: <a href="http://100.100.101.1:3002/d/insa-sla-monitoring">SLA Dashboard</a></p>
</body>
</html>
        """)

        html = template.render(
            sla_name=row['sla_name'],
            breach_start=row['breach_start'],
            target_value=row['target_value'],
            actual_value=row['actual_value'],
            severity=row['severity'],
            description=row['description']
        )

        # Get recipients from config
        recipients = self.config.get('reporting', {}).get('breach', {}).get('recipients', [])

        if not recipients:
            recipients = ['w.aroca@insaing.com', 'platform-oncall@insaing.com']

        self._send_email(
            to=recipients,
            subject=f"🚨 [CRITICAL] SLA Breach: {row['sla_name']}",
            html_body=html
        )

        # Mark as notified
        cursor.execute("UPDATE sla_breaches SET notified = 1 WHERE breach_id = ?", (breach_id,))
        self.db.conn.commit()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="INSA CRM SLA Reporter")
    parser.add_argument('--daily', action='store_true', help='Send daily report')
    parser.add_argument('--weekly', action='store_true', help='Send weekly report')
    parser.add_argument('--monthly', action='store_true', help='Send monthly report')
    parser.add_argument('--breach', type=int, help='Send breach notification for breach ID')
    parser.add_argument('--test', action='store_true', help='Generate test reports (no email)')

    args = parser.parse_args()

    reporter = SLAReporter()

    if args.test:
        print("=== DAILY REPORT ===")
        print(reporter.generate_daily_report())
        print("\n=== WEEKLY REPORT ===")
        print(reporter.generate_weekly_report())
        print("\n=== MONTHLY REPORT ===")
        print(reporter.generate_monthly_report())
    elif args.daily:
        reporter.send_daily_report()
    elif args.weekly:
        reporter.send_weekly_report()
    elif args.monthly:
        reporter.send_monthly_report()
    elif args.breach:
        reporter.send_breach_notification(args.breach)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
