# Multi-Agent Team Architecture - Enhanced Local Intelligence
**Created:** October 30, 2025
**Purpose:** Replace GitHub escalation with local AI agent collaboration
**Status:** Design Phase → Implementation

---

## 🎯 Core Philosophy

**BEFORE:** Detection → Auto-Fix → Escalate to GitHub (humans)
**AFTER:** Detection → AI Research Team → Multi-Agent Consultation → Learning → Local Escalation Dashboard

### Key Improvements
1. **Keep escalation local** - No external GitHub issues for every failure
2. **Multi-agent collaboration** - Agents consult each other for solutions
3. **Graduated intelligence** - Start simple, escalate to more powerful agents
4. **Knowledge accumulation** - Build local expertise database
5. **Human-in-the-loop** - Local dashboard for manual intervention when needed

---

## 🤖 Agent Team Structure

### 1. **Detection Agent** (EXISTS ✅ - BugScanner)
**Role:** Multi-source issue detection
**Current:** Scans logs, services, containers, HTTP, memory, ML models
**Keep as-is:** Working perfectly

```python
class BugScanner:
    # 6 detection methods
    - scan_logs()
    - check_failed_services()
    - check_failed_containers()
    - check_http_services()
    - check_container_memory()
    - check_ml_models()
```

---

### 2. **Research Agent Team** (ENHANCE 🔧)
**Current:** Single ResearchAgent using Claude Code subprocess
**Enhanced:** Multi-tiered research system

```python
class ResearchAgentTeam:
    """Graduated intelligence for problem solving"""

    def __init__(self):
        self.level1_agent = BasicResearchAgent()    # Pattern matching
        self.level2_agent = AdvancedResearchAgent()  # Claude Code (5min timeout)
        self.level3_agent = ExpertConsultation()     # Multi-agent consensus
        self.learning_db = LearningDatabase()

    def research_solution(self, issue, previous_attempts):
        # Level 1: Pattern matching (instant)
        if cached_solution := self.learning_db.get_cached_research(issue):
            return cached_solution

        # Level 2: Single AI agent (30s)
        solution = self.level2_agent.diagnose(issue, previous_attempts)
        if solution['confidence'] >= 0.80:
            return solution

        # Level 3: Multi-agent consultation (2min)
        return self.level3_agent.multi_agent_consensus(issue, previous_attempts)
```

#### 2A. **Basic Research Agent** (NEW ⭐)
- Pattern matching from learning database
- Instant response (0s)
- 80% of issues solved here (learned patterns)

#### 2B. **Advanced Research Agent** (EXISTS - ENHANCE 🔧)
- Claude Code subprocess (current implementation)
- 30-60s timeout
- Handles 15% of remaining issues

#### 2C. **Expert Consultation Agent** (NEW ⭐)
- Multi-agent voting system
- Runs 3 parallel Claude Code instances
- Takes consensus (2/3 or 3/3)
- 2-5min timeout
- Handles final 5% of complex issues

---

### 3. **Fix Implementation Agent** (EXISTS ✅ - IntelligentAutoFixer)
**Role:** Multi-strategy automated fixing
**Current:** 5 attempt levels + Platform Admin integration
**Keep as-is:** Working perfectly

```python
class IntelligentAutoFixer:
    # 5-level recovery system
    - Platform Admin (instant proven fixes)
    - Install Python modules
    - Advanced service recovery (5 levels)
    - Container memory optimization
    - AI-powered research-based fixes
```

---

### 4. **Learning Agent** (EXISTS ✅ - LearningDatabase)
**Role:** Pattern tracking and knowledge accumulation
**Current:** 3 tables (fix_patterns, fix_history, research_cache)
**Keep as-is:** Working perfectly

```python
class LearningDatabase:
    # Track what works
    - record_attempt()
    - get_best_strategy()
    - cache_research()
    - get_cached_research()
```

---

### 5. **Escalation Coordinator** (NEW ⭐)
**Role:** Local escalation management + human interface

```python
class EscalationCoordinator:
    """
    Local escalation system (replaces GitHub issues)
    Human-in-the-loop via web dashboard
    """

    def __init__(self):
        self.db_path = "/var/lib/autonomous-orchestrator/escalations.db"
        self.dashboard_port = 8888  # Local web UI

    def escalate_locally(self, task_id, issue, all_attempts, research_results):
        """
        Store in local database instead of GitHub

        Creates:
        - Escalation record in SQLite
        - Email notification (existing)
        - Entry in local web dashboard
        - Suggested actions for human
        """
        escalation = {
            'task_id': task_id,
            'severity': self.calculate_severity(issue),
            'ai_attempts': len(all_attempts),
            'ai_consensus': research_results.get('consensus'),
            'recommended_action': research_results.get('human_steps'),
            'created_at': datetime.now(),
            'status': 'pending_human_review'
        }

        self.store_escalation(escalation)
        self.send_email_alert(escalation)
        self.update_dashboard(escalation)

        return escalation['id']

    def check_human_resolution(self, escalation_id):
        """
        Continuously check if human fixed the issue
        If detected fixed: Mark escalation resolved
        If not fixed after 24h: Escalate to GitHub (optional fallback)
        """
        # Auto-detect resolution by re-running detection
        # Close escalation if issue no longer detected
```

---

### 6. **Agent Coordinator** (NEW ⭐ - CRITICAL)
**Role:** Orchestrate the entire team workflow

```python
class AgentCoordinator:
    """
    Master orchestrator - coordinates all agents
    Decision tree for agent escalation
    """

    def __init__(self):
        self.detector = BugScanner()
        self.research_team = ResearchAgentTeam()
        self.fixer = IntelligentAutoFixer()
        self.learning = LearningDatabase()
        self.escalation = EscalationCoordinator()

    def process_issue_intelligent(self, issue, task_id):
        """
        NEW WORKFLOW (replaces current process_issue)
        """

        # Step 1: Quick fix attempt (basic strategies)
        print(f"   🔧 Phase 1: Quick Fix Attempts (30s)")
        quick_result = self.fixer.quick_fix_attempts(issue, max_attempts=2)

        if quick_result['success']:
            print(f"   ✅ Quick fix successful!")
            return self.close_task(task_id, quick_result)

        # Step 2: Research + Advanced fixing (2-5min)
        print(f"   🧠 Phase 2: AI Research + Advanced Fixing")
        research = self.research_team.research_solution(issue, quick_result['attempts'])

        print(f"      AI Confidence: {research['confidence']:.0%}")
        print(f"      Consensus: {research.get('consensus', 'N/A')}")

        advanced_result = self.fixer.research_based_attempts(issue, research, max_attempts=3)

        if advanced_result['success']:
            print(f"   ✅ AI-guided fix successful!")
            return self.close_task(task_id, advanced_result)

        # Step 3: Expert consultation (5min)
        if research['confidence'] < 0.80:
            print(f"   🎓 Phase 3: Expert Multi-Agent Consultation")
            expert_research = self.research_team.level3_agent.multi_agent_consensus(
                issue,
                quick_result['attempts'] + advanced_result['attempts']
            )

            expert_result = self.fixer.execute_expert_suggestions(issue, expert_research)

            if expert_result['success']:
                print(f"   ✅ Expert consensus fix successful!")
                return self.close_task(task_id, expert_result)

        # Step 4: Local escalation (NO GITHUB)
        print(f"   📋 Phase 4: Local Escalation (Human Review Required)")

        all_attempts = (quick_result['attempts'] +
                       advanced_result['attempts'] +
                       expert_result.get('attempts', []))

        escalation_id = self.escalation.escalate_locally(
            task_id=task_id,
            issue=issue,
            all_attempts=all_attempts,
            research_results=expert_research if 'expert_research' in locals() else research
        )

        print(f"   📧 Escalation #{escalation_id} created")
        print(f"   🌐 View at: http://localhost:8888/escalations/{escalation_id}")
        print(f"   ✅ Email sent to w.aroca@insaing.com")

        return {
            'escalated': True,
            'escalation_id': escalation_id,
            'local_dashboard': True,
            'github_created': False  # KEY DIFFERENCE
        }
```

---

## 📊 Enhanced Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  DETECTION AGENT                                            │
│  Multi-source scanning (logs, services, containers, etc)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: QUICK FIX (30s max)                              │
│  ├─ Platform Admin (instant)                               │
│  ├─ Learned patterns (instant)                             │
│  └─ Basic restart (15s)                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                  ✅ Fixed? → CLOSE
                       │ ❌ Failed
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: AI RESEARCH + ADVANCED FIX (2-5min)             │
│  ├─ Single AI agent diagnosis (Claude Code)                │
│  ├─ Advanced strategies (5-level recovery)                 │
│  └─ AI-guided fixes (3 attempts)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                  ✅ Fixed? → CLOSE
                       │ ❌ Failed + Low confidence
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: EXPERT CONSULTATION (5min)                       │
│  ├─ Run 3 parallel AI agents                               │
│  ├─ Voting system (2/3 or 3/3 consensus)                  │
│  └─ Execute consensus solution                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                  ✅ Fixed? → CLOSE
                       │ ❌ ALL AI FAILED
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: LOCAL ESCALATION (HUMAN REVIEW)                 │
│  ├─ Store in local SQLite database                         │
│  ├─ Create entry in web dashboard (port 8888)             │
│  ├─ Send email alert with full AI analysis                │
│  ├─ Monitor for human resolution                           │
│  └─ Optional: Escalate to GitHub after 24h (configurable) │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Enhanced Database Schema

### New Table: `escalations`
```sql
CREATE TABLE escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    issue_hash TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'low', 'medium', 'high', 'critical'

    -- AI Analysis
    ai_attempts_count INTEGER,
    ai_consensus TEXT, -- JSON: {agent1: vote, agent2: vote, agent3: vote}
    ai_confidence REAL,
    ai_diagnosis TEXT,
    recommended_action TEXT,

    -- Human intervention
    status TEXT DEFAULT 'pending_human_review',
    assigned_to TEXT,
    human_notes TEXT,
    resolved_at TIMESTAMP,
    resolution_method TEXT, -- 'auto_detected', 'manual', 'github_escalated'

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP,

    -- Optional GitHub fallback (if still needed after 24h)
    github_issue_number INTEGER,
    github_escalated_at TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### New Table: `agent_consultations`
```sql
CREATE TABLE agent_consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escalation_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL, -- 'agent1', 'agent2', 'agent3'
    diagnosis TEXT NOT NULL,
    confidence REAL,
    suggested_fix TEXT,
    vote TEXT, -- 'fix_a', 'fix_b', 'fix_c'
    execution_time_seconds REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (escalation_id) REFERENCES escalations(id)
);
```

---

## 🌐 Local Escalation Dashboard

### Simple Flask Web UI (port 8888)
```python
from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/escalations')
def list_escalations():
    """Show all pending escalations"""
    conn = sqlite3.connect('/var/lib/autonomous-orchestrator/escalations.db')
    escalations = conn.execute("""
        SELECT id, task_id, severity, ai_consensus,
               recommended_action, created_at, status
        FROM escalations
        WHERE status = 'pending_human_review'
        ORDER BY severity DESC, created_at DESC
    """).fetchall()
    conn.close()

    return render_template('escalations.html', escalations=escalations)

@app.route('/escalation/<int:id>')
def view_escalation(id):
    """Detailed view of single escalation"""
    # Show:
    # - Original issue
    # - All AI attempts
    # - Multi-agent votes
    # - Recommended actions
    # - Manual intervention form
    pass

@app.route('/escalation/<int:id>/resolve', methods=['POST'])
def resolve_escalation(id):
    """Mark escalation as resolved"""
    # Human provides resolution notes
    # System auto-detects if issue is truly fixed
    pass
```

### Dashboard Features
- **Severity-based prioritization** (Critical → High → Medium → Low)
- **AI analysis summary** (what was tried, what failed)
- **Multi-agent consensus** (show voting results)
- **Recommended actions** (AI-generated steps for human)
- **One-click test** (re-run detection to verify fix)
- **GitHub escalation button** (optional fallback after 24h)

---

## 📈 Expected Performance Improvement

### Current System
- **Auto-fix rate:** 27%
- **GitHub escalation:** 73%
- **Human involvement:** Required for 73% of issues
- **Knowledge growth:** Slow (only learns from auto-fixes)

### Enhanced System
- **Phase 1 fix rate:** 60% (Platform Admin + learned patterns)
- **Phase 2 fix rate:** 25% (AI research + advanced strategies)
- **Phase 3 fix rate:** 10% (Expert multi-agent consensus)
- **Local escalation:** 5% (true edge cases)
- **Total auto-fix rate:** **95%** 🎯
- **GitHub escalation:** **Optional** (0-5%, only after 24h+ manual review)
- **Knowledge growth:** **Exponential** (learns from all 4 phases)

---

## 🚀 Implementation Plan

### Phase 1: Multi-Agent Research (1-2 days)
- [ ] Create `ExpertConsultation` class
- [ ] Implement 3-agent voting system
- [ ] Add consensus logic (2/3, 3/3)
- [ ] Test with known issues

### Phase 2: Local Escalation (1 day)
- [ ] Create `EscalationCoordinator` class
- [ ] Add `escalations` database table
- [ ] Add `agent_consultations` table
- [ ] Implement email alerts (existing code)

### Phase 3: Web Dashboard (1 day)
- [ ] Simple Flask app (200 lines)
- [ ] List escalations (severity sorted)
- [ ] Detail view (show AI analysis)
- [ ] Manual resolution form
- [ ] Auto-detection verification

### Phase 4: Agent Coordinator (1 day)
- [ ] Create `AgentCoordinator` class
- [ ] Implement 4-phase workflow
- [ ] Replace `process_issue()` in orchestrator
- [ ] Add performance metrics

### Phase 5: Testing & Tuning (1 day)
- [ ] Test with real issues
- [ ] Tune timeouts and thresholds
- [ ] Verify learning works
- [ ] Measure improvement

**Total: 5-6 days for complete implementation**

---

## 🎯 Success Metrics

1. **Auto-fix rate:** 27% → 95% (3.5x improvement)
2. **Human escalations:** 73% → 5% (14.6x reduction)
3. **GitHub issues:** 100% → 0-5% (20x reduction)
4. **Knowledge base:** Linear → Exponential growth
5. **Response time:** Unchanged (still 5min cycles)
6. **Cost:** $0 (all local, Claude Code subprocess)

---

## 🔐 Security & Safety

- **Rate limiting:** Max 3 parallel AI agents (protect Claude Code)
- **Timeout protection:** Phase 1: 30s, Phase 2: 5min, Phase 3: 5min
- **Safe commands only:** No destructive operations without human approval
- **Audit trail:** All agent decisions logged in database
- **Rollback capability:** Learning database tracks what works
- **Local-only:** No external API calls (except optional GitHub fallback)

---

## 💡 Future Enhancements

1. **Agent specialization:** Dedicated agents for containers, services, networks
2. **Federated learning:** Share knowledge across multiple iac1-like servers
3. **Predictive maintenance:** Detect issues before they happen
4. **Self-optimization:** Agents tune their own parameters
5. **Mobile dashboard:** Access escalations from phone
6. **Slack integration:** Alerts via Slack instead of email
7. **Voice interface:** "Alexa, what escalations do I have?"

---

**Status:** Ready for implementation
**Approval:** Waiting for user confirmation
**Next Step:** Start with Phase 1 (Multi-Agent Research)
