#!/usr/bin/env python3
"""
Local Escalation Coordinator
Replaces GitHub issue escalation with local database tracking
Human-in-the-loop via web dashboard

Created: October 30, 2025
Author: Insa Automation Corp
Purpose: Keep escalation local, reduce human dependency to <5%
"""

import os
import sqlite3
import hashlib
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EscalationCoordinator:
    """
    Local escalation management system
    Replaces GitHub issues with local SQLite database
    Provides web dashboard for human review
    """

    def __init__(self, db_path: str = "/var/lib/autonomous-orchestrator/escalations.db"):
        self.db_path = db_path
        self.dashboard_port = 8888
        self.admin_email = "w.aroca@insaing.com"
        self.smtp_host = "localhost"
        self.smtp_port = 25

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self.init_database()

    def init_database(self):
        """Initialize escalation database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Escalations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                issue_hash TEXT NOT NULL,
                severity TEXT NOT NULL,

                -- Issue details
                issue_type TEXT,
                issue_source TEXT,
                issue_service TEXT,
                issue_message TEXT,

                -- AI Analysis
                ai_attempts_count INTEGER,
                ai_consensus TEXT,
                ai_confidence REAL,
                ai_diagnosis TEXT,
                recommended_action TEXT,

                -- Human intervention
                status TEXT DEFAULT 'pending_human_review',
                assigned_to TEXT,
                human_notes TEXT,
                resolved_at TIMESTAMP,
                resolution_method TEXT,

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP,

                -- Optional GitHub fallback
                github_issue_number INTEGER,
                github_escalated_at TIMESTAMP,

                UNIQUE(issue_hash)
            )
        """)

        # Agent consultations table (for multi-agent voting records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                escalation_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                confidence REAL,
                suggested_fix TEXT,
                vote TEXT,
                execution_time_seconds REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (escalation_id) REFERENCES escalations(id)
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_escalations_severity ON escalations(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_escalations_created ON escalations(created_at)")

        conn.commit()
        conn.close()

    def escalate_locally(self, task_id: int, issue: Dict, all_attempts: List[Dict],
                        research_results: Dict) -> int:
        """
        Store escalation in local database instead of GitHub

        Args:
            task_id: ID from tasks database
            issue: Original issue details
            all_attempts: List of all fix attempts made
            research_results: AI research results (diagnosis, confidence, consensus)

        Returns:
            escalation_id: ID of created escalation
        """
        # Calculate severity based on issue type and AI confidence
        severity = self.calculate_severity(issue, research_results)

        # Generate unique hash for this issue
        issue_hash = self.generate_issue_hash(issue)

        # Extract consensus data if multi-agent was used
        consensus_data = None
        if 'agent_votes' in research_results:
            consensus_data = {
                'consensus_type': research_results.get('consensus_type', 'unknown'),
                'agent_votes': research_results.get('agent_votes', {})
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert escalation
            cursor.execute("""
                INSERT INTO escalations (
                    task_id, issue_hash, severity,
                    issue_type, issue_source, issue_service, issue_message,
                    ai_attempts_count, ai_consensus, ai_confidence, ai_diagnosis,
                    recommended_action, status, last_checked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                issue_hash,
                severity,
                issue.get('type', 'unknown'),
                issue.get('source', 'unknown'),
                issue.get('service') or issue.get('container', 'unknown'),
                issue.get('message', ''),
                len(all_attempts),
                str(consensus_data) if consensus_data else None,
                research_results.get('confidence', 0.0),
                research_results.get('diagnosis', 'No diagnosis available'),
                self.generate_recommended_action(research_results),
                'pending_human_review',
                datetime.now().isoformat()
            ))

            escalation_id = cursor.lastrowid

            # If multi-agent consultation was used, store agent votes
            if 'agent_votes' in research_results:
                for agent_name, agent_result in research_results['agent_votes'].items():
                    cursor.execute("""
                        INSERT INTO agent_consultations (
                            escalation_id, agent_name, diagnosis, confidence,
                            suggested_fix, vote, execution_time_seconds
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        escalation_id,
                        agent_name,
                        agent_result.get('diagnosis', ''),
                        agent_result.get('confidence', 0.0),
                        str(agent_result.get('suggested_fixes', [])),
                        agent_result.get('vote', 'unknown'),
                        float(agent_result.get('execution_time', '0s').replace('s', ''))
                    ))

            conn.commit()

            # Send email notification
            self.send_email_alert(escalation_id, issue, severity, research_results)

            print(f"   📋 Escalation #{escalation_id} created in local database")
            print(f"   🌐 View at: http://localhost:{self.dashboard_port}/escalations/{escalation_id}")
            print(f"   📧 Email sent to {self.admin_email}")

            return escalation_id

        except sqlite3.IntegrityError:
            # Duplicate issue (already escalated)
            cursor.execute("SELECT id FROM escalations WHERE issue_hash = ?", (issue_hash,))
            existing_id = cursor.fetchone()[0]
            print(f"   ⚠️  Issue already escalated as #{existing_id}")
            return existing_id
        finally:
            conn.close()

    def generate_issue_hash(self, issue: Dict) -> str:
        """Generate unique hash for issue to prevent duplicates"""
        issue_string = f"{issue.get('type')}:{issue.get('source')}:{issue.get('message')}"
        return hashlib.sha256(issue_string.encode()).hexdigest()[:16]

    def calculate_severity(self, issue: Dict, research_results: Dict) -> str:
        """
        Calculate severity based on issue type and AI confidence

        Returns: 'critical', 'high', 'medium', or 'low'
        """
        # Base severity on issue type
        issue_type = issue.get('type', 'unknown')

        if issue_type in ['service_failure', 'container_crash', 'critical_error']:
            base_severity = 3  # Critical
        elif issue_type in ['memory_leak', 'disk_full', 'connection_timeout']:
            base_severity = 2  # High
        elif issue_type in ['warning', 'performance_degradation']:
            base_severity = 1  # Medium
        else:
            base_severity = 0  # Low

        # Adjust by AI confidence (low confidence = higher severity)
        ai_confidence = research_results.get('confidence', 0.5)
        if ai_confidence < 0.5:
            base_severity += 1  # Escalate severity if AI is uncertain

        # Map to severity string
        severity_map = {
            0: 'low',
            1: 'medium',
            2: 'high',
            3: 'critical',
            4: 'critical'  # Cap at critical
        }

        return severity_map.get(base_severity, 'medium')

    def generate_recommended_action(self, research_results: Dict) -> str:
        """Generate human-readable recommended actions"""
        recommended = []

        # From AI diagnosis
        if research_results.get('diagnosis'):
            recommended.append(f"AI Diagnosis: {research_results['diagnosis']}")

        # From suggested fixes
        suggested_fixes = research_results.get('suggested_fixes', [])
        if suggested_fixes:
            recommended.append("\nSuggested Fixes:")
            for i, fix in enumerate(suggested_fixes[:3], 1):
                recommended.append(f"  {i}. {fix.get('strategy', 'Unknown')}: {fix.get('description', '')}")

        # From multi-agent consensus
        if research_results.get('consensus_type'):
            recommended.append(f"\nAI Consensus: {research_results['consensus_type']}")

        return '\n'.join(recommended) if recommended else "Manual investigation required"

    def send_email_alert(self, escalation_id: int, issue: Dict, severity: str,
                        research_results: Dict):
        """Send email notification about escalation"""
        try:
            msg = MIMEMultipart()
            msg['From'] = 'iac1-orchestrator@insaing.com'
            msg['To'] = self.admin_email
            msg['Subject'] = f"[{severity.upper()}] Local Escalation #{escalation_id}: {issue.get('type', 'Unknown')}"

            # Email body
            body = f"""
Autonomous Task Orchestrator - Local Escalation Alert

Escalation ID: #{escalation_id}
Severity: {severity.upper()}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

ISSUE DETAILS:
--------------
Type: {issue.get('type', 'unknown')}
Source: {issue.get('source', 'unknown')}
Service/Container: {issue.get('service') or issue.get('container', 'unknown')}
Message: {issue.get('message', 'No message')}

AI ANALYSIS:
-----------
Confidence: {research_results.get('confidence', 0):.0%}
Diagnosis: {research_results.get('diagnosis', 'No diagnosis')}
Research Level: {research_results.get('research_level', 'unknown')}
Consensus: {research_results.get('consensus_type', 'N/A')}

RECOMMENDED ACTION:
------------------
{self.generate_recommended_action(research_results)}

VIEW ESCALATION:
---------------
Dashboard: http://localhost:{self.dashboard_port}/escalations/{escalation_id}
Database: {self.db_path}

This escalation requires human review. All AI attempts have been exhausted.

---
Autonomous Task Orchestrator v2.0
Insa Automation Corp
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)

        except Exception as e:
            print(f"   ⚠️  Failed to send email alert: {e}")

    def check_human_resolution(self, escalation_id: int) -> Optional[str]:
        """
        Check if human has resolved the escalation

        Returns:
            resolution_method if resolved, None if still pending
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, resolved_at, resolution_method
            FROM escalations
            WHERE id = ?
        """, (escalation_id,))

        result = cursor.fetchone()
        conn.close()

        if result and result[0] != 'pending_human_review':
            return result[2]  # resolution_method

        return None

    def mark_resolved(self, escalation_id: int, resolution_method: str = 'manual',
                     human_notes: str = None):
        """Mark escalation as resolved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE escalations
            SET status = 'resolved',
                resolved_at = ?,
                resolution_method = ?,
                human_notes = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), resolution_method, human_notes, escalation_id))

        conn.commit()
        conn.close()

        print(f"   ✅ Escalation #{escalation_id} marked as resolved ({resolution_method})")

    def get_pending_escalations(self, severity: Optional[str] = None) -> List[Dict]:
        """Get all pending escalations, optionally filtered by severity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if severity:
            cursor.execute("""
                SELECT id, task_id, severity, issue_type, issue_service,
                       ai_confidence, created_at, recommended_action
                FROM escalations
                WHERE status = 'pending_human_review' AND severity = ?
                ORDER BY severity DESC, created_at DESC
            """, (severity,))
        else:
            cursor.execute("""
                SELECT id, task_id, severity, issue_type, issue_service,
                       ai_confidence, created_at, recommended_action
                FROM escalations
                WHERE status = 'pending_human_review'
                ORDER BY severity DESC, created_at DESC
            """)

        results = cursor.fetchall()
        conn.close()

        escalations = []
        for row in results:
            escalations.append({
                'id': row[0],
                'task_id': row[1],
                'severity': row[2],
                'issue_type': row[3],
                'issue_service': row[4],
                'ai_confidence': row[5],
                'created_at': row[6],
                'recommended_action': row[7]
            })

        return escalations

    def get_escalation_details(self, escalation_id: int) -> Optional[Dict]:
        """Get detailed information about specific escalation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, task_id, severity, issue_type, issue_source, issue_service,
                   issue_message, ai_attempts_count, ai_consensus, ai_confidence,
                   ai_diagnosis, recommended_action, status, created_at, resolved_at,
                   resolution_method, human_notes
            FROM escalations
            WHERE id = ?
        """, (escalation_id,))

        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        # Get agent consultations if available
        cursor.execute("""
            SELECT agent_name, diagnosis, confidence, suggested_fix, vote,
                   execution_time_seconds, timestamp
            FROM agent_consultations
            WHERE escalation_id = ?
        """, (escalation_id,))

        agent_votes = cursor.fetchall()
        conn.close()

        escalation = {
            'id': result[0],
            'task_id': result[1],
            'severity': result[2],
            'issue': {
                'type': result[3],
                'source': result[4],
                'service': result[5],
                'message': result[6]
            },
            'ai_attempts_count': result[7],
            'ai_consensus': result[8],
            'ai_confidence': result[9],
            'ai_diagnosis': result[10],
            'recommended_action': result[11],
            'status': result[12],
            'created_at': result[13],
            'resolved_at': result[14],
            'resolution_method': result[15],
            'human_notes': result[16],
            'agent_votes': []
        }

        # Add agent votes
        for vote in agent_votes:
            escalation['agent_votes'].append({
                'agent_name': vote[0],
                'diagnosis': vote[1],
                'confidence': vote[2],
                'suggested_fix': vote[3],
                'vote': vote[4],
                'execution_time': f"{vote[5]:.1f}s",
                'timestamp': vote[6]
            })

        return escalation

    def get_statistics(self) -> Dict:
        """Get escalation statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total escalations
        cursor.execute("SELECT COUNT(*) FROM escalations")
        stats['total'] = cursor.fetchone()[0]

        # Pending
        cursor.execute("SELECT COUNT(*) FROM escalations WHERE status = 'pending_human_review'")
        stats['pending'] = cursor.fetchone()[0]

        # Resolved
        cursor.execute("SELECT COUNT(*) FROM escalations WHERE status = 'resolved'")
        stats['resolved'] = cursor.fetchone()[0]

        # By severity
        cursor.execute("SELECT severity, COUNT(*) FROM escalations GROUP BY severity")
        stats['by_severity'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Average resolution time
        cursor.execute("""
            SELECT AVG(JULIANDAY(resolved_at) - JULIANDAY(created_at)) * 24
            FROM escalations
            WHERE status = 'resolved'
        """)
        avg_hours = cursor.fetchone()[0]
        stats['avg_resolution_hours'] = round(avg_hours, 1) if avg_hours else 0

        conn.close()

        return stats


# Test the system
if __name__ == "__main__":
    print("🧪 Testing Local Escalation Coordinator...\n")

    # Initialize
    coordinator = EscalationCoordinator()
    print("✅ EscalationCoordinator initialized\n")

    # Test escalation
    test_issue = {
        'type': 'service_failure',
        'source': 'systemd',
        'service': 'test-service.service',
        'message': 'Service test-service.service has failed'
    }

    test_research = {
        'confidence': 0.65,
        'diagnosis': 'Service binary not found in expected location',
        'research_level': 3,
        'consensus_type': '2/3',
        'suggested_fixes': [
            {'strategy': 'Reinstall service', 'description': 'apt-get install --reinstall test-service'},
            {'strategy': 'Check binary path', 'description': 'which test-service'}
        ],
        'agent_votes': {
            'agent1': {'diagnosis': 'Binary missing', 'confidence': 0.7, 'execution_time': '5.2s'},
            'agent2': {'diagnosis': 'Binary missing', 'confidence': 0.8, 'execution_time': '4.8s'},
            'agent3': {'diagnosis': 'Config error', 'confidence': 0.5, 'execution_time': '6.1s'}
        }
    }

    # Create escalation
    print("📋 Creating test escalation...")
    escalation_id = coordinator.escalate_locally(
        task_id=999,
        issue=test_issue,
        all_attempts=[],
        research_results=test_research
    )

    print(f"\n✅ Escalation #{escalation_id} created!\n")

    # Get statistics
    stats = coordinator.get_statistics()
    print("📊 Statistics:")
    print(f"   Total escalations: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Resolved: {stats['resolved']}")
    print(f"   By severity: {stats['by_severity']}")

    print("\n🎉 Local Escalation Coordinator is ready!")
