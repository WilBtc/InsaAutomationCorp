#!/usr/bin/env python3
"""
Web Dashboard for Local Escalations
Simple Flask UI for viewing and managing escalations

Created: October 30, 2025
Author: Insa Automation Corp
Purpose: Human-in-the-loop interface for the 5% of issues that need manual review
"""

from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from escalation_coordinator import EscalationCoordinator
from datetime import datetime
import os

app = Flask(__name__)
coordinator = EscalationCoordinator()


# HTML Templates (embedded for simplicity)
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Autonomous Orchestrator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }
        .stat-card p {
            color: #666;
            font-size: 0.9em;
        }
        .content {
            padding: 30px;
        }
        .escalation-list {
            display: grid;
            gap: 20px;
        }
        .escalation-card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
        }
        .escalation-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        .escalation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .escalation-id {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }
        .severity {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .severity.critical {
            background: #ff4444;
            color: white;
        }
        .severity.high {
            background: #ff9800;
            color: white;
        }
        .severity.medium {
            background: #ffc107;
            color: black;
        }
        .severity.low {
            background: #4caf50;
            color: white;
        }
        .escalation-info {
            margin-bottom: 15px;
        }
        .info-row {
            display: flex;
            margin-bottom: 8px;
        }
        .info-label {
            font-weight: bold;
            min-width: 150px;
            color: #666;
        }
        .info-value {
            color: #333;
        }
        .actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #4caf50;
            color: white;
        }
        .btn-success:hover {
            background: #45a049;
        }
        .btn-danger {
            background: #ff4444;
            color: white;
        }
        .btn-danger:hover {
            background: #cc0000;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .detail-section {
            margin-bottom: 30px;
        }
        .detail-section h2 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .agent-vote {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .agent-vote h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .confidence-bar {
            background: #e0e0e0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .confidence-fill {
            background: linear-gradient(90deg, #4caf50, #667eea);
            height: 100%;
            transition: width 0.5s;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #666;
        }
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-family: inherit;
            resize: vertical;
        }
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Autonomous Task Orchestrator</h1>
            <p>{{ subtitle }}</p>
        </div>
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

ESCALATIONS_LIST_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    <div class="stats">
        <div class="stat-card">
            <h3>{{ stats.total }}</h3>
            <p>Total Escalations</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.pending }}</h3>
            <p>Pending Review</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.resolved }}</h3>
            <p>Resolved</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.avg_resolution_hours }}h</h3>
            <p>Avg Resolution Time</p>
        </div>
    </div>

    <div class="content">
        {% if escalations %}
            <h2 style="margin-bottom: 20px; color: #667eea;">Pending Escalations ({{ escalations|length }})</h2>
            <div class="escalation-list">
                {% for esc in escalations %}
                <div class="escalation-card">
                    <div class="escalation-header">
                        <div class="escalation-id">
                            Escalation #{{ esc.id }}
                        </div>
                        <span class="severity {{ esc.severity }}">
                            {{ esc.severity.upper() }}
                        </span>
                    </div>

                    <div class="escalation-info">
                        <div class="info-row">
                            <span class="info-label">Issue Type:</span>
                            <span class="info-value">{{ esc.issue_type }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Service:</span>
                            <span class="info-value">{{ esc.issue_service }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">AI Confidence:</span>
                            <span class="info-value">{{ (esc.ai_confidence * 100)|round }}%</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Created:</span>
                            <span class="info-value">{{ esc.created_at }}</span>
                        </div>
                    </div>

                    <div class="actions">
                        <a href="/escalation/{{ esc.id }}" class="btn btn-primary">View Details</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="empty-state">
                <h2>🎉 No Pending Escalations!</h2>
                <p>All issues are being handled autonomously.</p>
            </div>
        {% endif %}
    </div>
{% endblock %}
"""

ESCALATION_DETAIL_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    <div class="content">
        <a href="/" class="back-link">← Back to All Escalations</a>

        <div class="escalation-header" style="margin-bottom: 30px;">
            <div class="escalation-id" style="font-size: 2em;">
                Escalation #{{ esc.id }}
            </div>
            <span class="severity {{ esc.severity }}" style="font-size: 1.2em;">
                {{ esc.severity.upper() }}
            </span>
        </div>

        <!-- Issue Details -->
        <div class="detail-section">
            <h2>📋 Issue Details</h2>
            <div class="info-row">
                <span class="info-label">Type:</span>
                <span class="info-value">{{ esc.issue.type }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Source:</span>
                <span class="info-value">{{ esc.issue.source }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Service/Container:</span>
                <span class="info-value">{{ esc.issue.service }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Created:</span>
                <span class="info-value">{{ esc.created_at }}</span>
            </div>
            <pre>{{ esc.issue.message }}</pre>
        </div>

        <!-- AI Analysis -->
        <div class="detail-section">
            <h2>🤖 AI Analysis</h2>
            <div class="info-row">
                <span class="info-label">Attempts Made:</span>
                <span class="info-value">{{ esc.ai_attempts_count }} attempts</span>
            </div>
            <div class="info-row">
                <span class="info-label">Confidence:</span>
                <span class="info-value">{{ (esc.ai_confidence * 100)|round }}%</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {{ (esc.ai_confidence * 100)|round }}%"></div>
            </div>

            <h3 style="margin-top: 20px; margin-bottom: 10px;">Diagnosis:</h3>
            <pre>{{ esc.ai_diagnosis }}</pre>

            {% if esc.ai_consensus %}
            <h3 style="margin-top: 20px; margin-bottom: 10px;">Consensus: {{ esc.ai_consensus }}</h3>
            {% endif %}
        </div>

        <!-- Agent Votes (if multi-agent consultation was used) -->
        {% if esc.agent_votes %}
        <div class="detail-section">
            <h2>🎓 Multi-Agent Consultation</h2>
            {% for vote in esc.agent_votes %}
            <div class="agent-vote">
                <h4>{{ vote.agent_name }} ({{ (vote.confidence * 100)|round }}% confidence, {{ vote.execution_time }})</h4>
                <p><strong>Diagnosis:</strong> {{ vote.diagnosis }}</p>
                <p><strong>Suggested Fix:</strong> {{ vote.suggested_fix }}</p>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Recommended Actions -->
        <div class="detail-section">
            <h2>💡 Recommended Actions</h2>
            <pre>{{ esc.recommended_action }}</pre>
        </div>

        <!-- Resolution Form -->
        {% if esc.status == 'pending_human_review' %}
        <div class="detail-section">
            <h2>✅ Mark as Resolved</h2>
            <form action="/escalation/{{ esc.id }}/resolve" method="POST">
                <div class="form-group">
                    <label for="notes">Resolution Notes:</label>
                    <textarea id="notes" name="notes" rows="4" placeholder="Describe how you resolved this issue..."></textarea>
                </div>
                <button type="submit" class="btn btn-success">Mark Resolved</button>
            </form>
        </div>
        {% else %}
        <div class="detail-section">
            <h2>✅ Resolution</h2>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value">{{ esc.status }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Resolved At:</span>
                <span class="info-value">{{ esc.resolved_at }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Method:</span>
                <span class="info-value">{{ esc.resolution_method }}</span>
            </div>
            {% if esc.human_notes %}
            <pre>{{ esc.human_notes }}</pre>
            {% endif %}
        </div>
        {% endif %}
    </div>
{% endblock %}
"""


# Routes
@app.route('/')
def index():
    """List all pending escalations"""
    escalations = coordinator.get_pending_escalations()
    stats = coordinator.get_statistics()

    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', ESCALATIONS_LIST_TEMPLATE),
        title="Escalations Dashboard",
        subtitle="Local Escalation Management - 95% Autonomous Operation",
        escalations=escalations,
        stats=stats
    )


@app.route('/escalations')
def escalations_list():
    """Alias for index"""
    return index()


@app.route('/escalation/<int:escalation_id>')
def escalation_detail(escalation_id):
    """Detailed view of single escalation"""
    esc = coordinator.get_escalation_details(escalation_id)

    if not esc:
        return f"<h1>Escalation #{escalation_id} not found</h1>", 404

    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', ESCALATION_DETAIL_TEMPLATE),
        title=f"Escalation #{escalation_id}",
        subtitle=f"{esc['severity'].upper()} - {esc['issue']['type']}",
        esc=esc
    )


@app.route('/escalation/<int:escalation_id>/resolve', methods=['POST'])
def resolve_escalation(escalation_id):
    """Mark escalation as resolved"""
    notes = request.form.get('notes', '')

    coordinator.mark_resolved(
        escalation_id=escalation_id,
        resolution_method='manual',
        human_notes=notes
    )

    return redirect(url_for('index'))


@app.route('/api/escalations')
def api_escalations():
    """API endpoint for escalation data"""
    escalations = coordinator.get_pending_escalations()
    return jsonify(escalations)


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = coordinator.get_statistics()
    return jsonify(stats)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'autonomous-orchestrator-dashboard',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🌐 Starting Web Dashboard...")
    print(f"   URL: http://localhost:8888")
    print(f"   Database: {coordinator.db_path}")
    print("")

    # Run Flask
    app.run(
        host='0.0.0.0',
        port=8888,
        debug=False
    )
