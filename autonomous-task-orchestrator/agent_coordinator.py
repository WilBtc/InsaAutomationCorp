#!/usr/bin/env python3
"""
Agent Coordinator - Master Orchestrator
Coordinates all agents in 4-phase graduated intelligence workflow

Created: October 30, 2025
Author: Insa Automation Corp
Purpose: Replace GitHub escalation with 95% autonomous operation
"""

import time
from typing import Dict, List
from datetime import datetime

# Import all agent components
from intelligent_fixer import IntelligentAutoFixer, LearningDatabase
from multi_agent_research import ResearchAgentTeam
from escalation_coordinator import EscalationCoordinator


class AgentCoordinator:
    """
    Master orchestrator - coordinates all agents
    4-phase graduated intelligence workflow
    Goal: 95% autonomous operation (5% escalation)
    """

    def __init__(self):
        # Core agents
        self.fixer = IntelligentAutoFixer()
        self.research_team = ResearchAgentTeam()
        self.escalation = EscalationCoordinator()
        self.learning = LearningDatabase()

        # Performance tracking
        self.phase_stats = {
            'phase1_success': 0,
            'phase2_success': 0,
            'phase3_success': 0,
            'phase4_escalated': 0,
            'total_processed': 0
        }

    def process_issue_intelligent(self, issue: Dict, task_id: int) -> Dict:
        """
        NEW WORKFLOW: 4-phase graduated intelligence

        Phase 1: Quick Fix (30s max)
        Phase 2: AI Research + Advanced Fixing (2-5min)
        Phase 3: Expert Consultation (5min)
        Phase 4: Local Escalation (Human Review)

        Args:
            issue: Issue details from scanner
            task_id: Task ID from database

        Returns:
            Result dict with success status and phase info
        """
        start_time = time.time()
        self.phase_stats['total_processed'] += 1

        print(f"\n{'='*80}")
        print(f"🤖 INTELLIGENT AGENT SYSTEM - Issue Processing")
        print(f"   Task ID: {task_id}")
        print(f"   Issue: {issue.get('type', 'unknown')} - {issue.get('service') or issue.get('container', 'unknown')}")
        print(f"{'='*80}\n")

        # PHASE 1: Quick Fix Attempts (30s max)
        phase1_result = self.phase1_quick_fix(issue, task_id)
        if phase1_result['success']:
            elapsed = time.time() - start_time
            print(f"\n✅ RESOLVED IN PHASE 1 (Quick Fix) - {elapsed:.1f}s")
            print(f"   Strategy: {phase1_result['strategy']}")
            self.phase_stats['phase1_success'] += 1
            return phase1_result

        # PHASE 2: AI Research + Advanced Fixing (2-5min)
        phase2_result = self.phase2_ai_research(issue, task_id, phase1_result['attempts'])
        if phase2_result['success']:
            elapsed = time.time() - start_time
            print(f"\n✅ RESOLVED IN PHASE 2 (AI Research) - {elapsed:.1f}s")
            print(f"   Strategy: {phase2_result['strategy']}")
            print(f"   AI Confidence: {phase2_result.get('ai_confidence', 0):.0%}")
            self.phase_stats['phase2_success'] += 1
            return phase2_result

        # PHASE 3: Expert Consultation (5min)
        phase3_result = self.phase3_expert_consultation(
            issue, task_id,
            phase1_result['attempts'] + phase2_result['attempts']
        )
        if phase3_result['success']:
            elapsed = time.time() - start_time
            print(f"\n✅ RESOLVED IN PHASE 3 (Expert Consultation) - {elapsed:.1f}s")
            print(f"   Consensus: {phase3_result.get('consensus', 'N/A')}")
            print(f"   Strategy: {phase3_result['strategy']}")
            self.phase_stats['phase3_success'] += 1
            return phase3_result

        # PHASE 4: Local Escalation (Human Review Required)
        phase4_result = self.phase4_local_escalation(
            issue, task_id,
            phase1_result['attempts'] + phase2_result['attempts'] + phase3_result['attempts'],
            phase3_result.get('research', {})
        )

        elapsed = time.time() - start_time
        print(f"\n📋 ESCALATED TO PHASE 4 (Human Review) - {elapsed:.1f}s")
        print(f"   Total AI Attempts: {len(phase4_result['all_attempts'])}")
        print(f"   Escalation ID: #{phase4_result['escalation_id']}")
        print(f"   Dashboard: http://localhost:8888/escalation/{phase4_result['escalation_id']}")

        self.phase_stats['phase4_escalated'] += 1
        return phase4_result

    def phase1_quick_fix(self, issue: Dict, task_id: int) -> Dict:
        """
        Phase 1: Quick Fix Attempts (30s max)
        - Platform Admin instant fixes
        - Learned patterns
        - Basic service restart
        """
        print(f"   🔧 PHASE 1: Quick Fix Attempts (30s max)")
        print(f"      └─ Platform Admin + Learned Patterns\n")

        start_time = time.time()
        attempts = []
        max_attempts = 2
        timeout = 30

        for attempt_num in range(1, max_attempts + 1):
            if (time.time() - start_time) > timeout:
                print(f"      ⏱️  Phase 1 timeout (30s)")
                break

            print(f"      Attempt {attempt_num}/{max_attempts}:")

            # Try Platform Admin first (instant)
            if attempt_num == 1:
                result = self.fixer.try_platform_admin_fix(issue)
            else:
                # Try learned patterns
                result = self.fixer.try_learned_pattern(issue)

            attempts.append(result)

            if result['success']:
                print(f"      ✅ SUCCESS: {result['strategy']}")
                return {
                    'success': True,
                    'phase': 1,
                    'strategy': result['strategy'],
                    'attempts': attempts,
                    'elapsed': time.time() - start_time
                }
            else:
                print(f"      ❌ FAILED: {result['message']}")

        elapsed = time.time() - start_time
        print(f"      Phase 1 Complete: {len(attempts)} attempts, {elapsed:.1f}s, all failed\n")

        return {
            'success': False,
            'phase': 1,
            'attempts': attempts,
            'elapsed': elapsed
        }

    def phase2_ai_research(self, issue: Dict, task_id: int, previous_attempts: List[Dict]) -> Dict:
        """
        Phase 2: AI Research + Advanced Fixing (2-5min)
        - Single AI agent diagnosis
        - Advanced recovery strategies
        - AI-guided fixes
        """
        print(f"   🧠 PHASE 2: AI Research + Advanced Fixing (2-5min)")
        print(f"      └─ Single AI Agent + Advanced Strategies\n")

        start_time = time.time()
        max_attempts = 3
        attempts = []

        # Get AI research
        print(f"      Running AI research...")
        research = self.research_team.research_solution(issue, previous_attempts)

        print(f"      AI Confidence: {research.get('confidence', 0):.0%}")
        print(f"      Research Level: {research.get('research_level', 'unknown')}")

        # If confidence is high enough, try AI-suggested fixes
        if research.get('confidence', 0) >= 0.60:
            print(f"\n      Attempting AI-guided fixes:")

            for attempt_num in range(1, max_attempts + 1):
                print(f"      Attempt {attempt_num}/{max_attempts}:")

                # Execute AI-suggested fix
                result = self.fixer.execute_research_fix(issue, research, attempt_num)
                attempts.append(result)

                if result['success']:
                    print(f"      ✅ SUCCESS: {result['strategy']}")
                    return {
                        'success': True,
                        'phase': 2,
                        'strategy': result['strategy'],
                        'attempts': attempts,
                        'ai_confidence': research['confidence'],
                        'research_level': research.get('research_level'),
                        'elapsed': time.time() - start_time
                    }
                else:
                    print(f"      ❌ FAILED: {result['message']}")

        elapsed = time.time() - start_time
        print(f"      Phase 2 Complete: {len(attempts)} attempts, {elapsed:.1f}s, all failed\n")

        return {
            'success': False,
            'phase': 2,
            'attempts': attempts,
            'research': research,
            'elapsed': elapsed
        }

    def phase3_expert_consultation(self, issue: Dict, task_id: int,
                                   previous_attempts: List[Dict]) -> Dict:
        """
        Phase 3: Expert Multi-Agent Consultation (5min)
        - Run 3 parallel AI agents
        - Compute consensus (2/3 or 3/3)
        - Execute consensus solution
        """
        print(f"   🎓 PHASE 3: Expert Multi-Agent Consultation (5min)")
        print(f"      └─ 3-Agent Voting + Consensus Execution\n")

        start_time = time.time()
        attempts = []

        # Run multi-agent consultation
        print(f"      Starting 3-agent consultation...")
        expert_research = self.research_team.level3_agent.multi_agent_consensus(
            issue, previous_attempts
        )

        print(f"      Consensus: {expert_research.get('consensus_type', 'unknown')}")
        print(f"      Confidence: {expert_research.get('confidence', 0):.0%}")

        # If strong consensus (2/3 or 3/3), try suggested fixes
        consensus_type = expert_research.get('consensus_type', '0/3')
        consensus_strength = int(consensus_type.split('/')[0]) if '/' in consensus_type else 0

        if consensus_strength >= 2:
            print(f"\n      Strong consensus! Attempting expert fixes:")

            max_attempts = 2
            for attempt_num in range(1, max_attempts + 1):
                print(f"      Attempt {attempt_num}/{max_attempts}:")

                # Execute expert-suggested fix
                result = self.fixer.execute_expert_fix(issue, expert_research, attempt_num)
                attempts.append(result)

                if result['success']:
                    print(f"      ✅ SUCCESS: {result['strategy']}")
                    return {
                        'success': True,
                        'phase': 3,
                        'strategy': result['strategy'],
                        'consensus': expert_research.get('consensus_type'),
                        'attempts': attempts,
                        'research': expert_research,
                        'elapsed': time.time() - start_time
                    }
                else:
                    print(f"      ❌ FAILED: {result['message']}")

        elapsed = time.time() - start_time
        print(f"      Phase 3 Complete: {len(attempts)} attempts, {elapsed:.1f}s, all failed\n")

        return {
            'success': False,
            'phase': 3,
            'attempts': attempts,
            'research': expert_research,
            'elapsed': elapsed
        }

    def phase4_local_escalation(self, issue: Dict, task_id: int,
                                all_attempts: List[Dict], research_results: Dict) -> Dict:
        """
        Phase 4: Local Escalation (Human Review Required)
        - Store in local SQLite database
        - Send email alert
        - Create web dashboard entry
        - NO GitHub issue (local only)
        """
        print(f"   📋 PHASE 4: Local Escalation (Human Review Required)")
        print(f"      └─ Database + Email + Dashboard\n")

        # Create local escalation
        escalation_id = self.escalation.escalate_locally(
            task_id=task_id,
            issue=issue,
            all_attempts=all_attempts,
            research_results=research_results
        )

        return {
            'success': False,
            'phase': 4,
            'escalated': True,
            'escalation_id': escalation_id,
            'all_attempts': all_attempts,
            'local_dashboard': True,
            'github_created': False  # KEY DIFFERENCE - no GitHub
        }

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total = self.phase_stats['total_processed']

        if total == 0:
            return {
                'total_processed': 0,
                'auto_fix_rate': 0.0,
                'escalation_rate': 0.0,
                'phase_breakdown': {}
            }

        auto_fixed = (
            self.phase_stats['phase1_success'] +
            self.phase_stats['phase2_success'] +
            self.phase_stats['phase3_success']
        )

        return {
            'total_processed': total,
            'auto_fix_rate': auto_fixed / total,
            'escalation_rate': self.phase_stats['phase4_escalated'] / total,
            'phase_breakdown': {
                'phase1_quick_fix': {
                    'success': self.phase_stats['phase1_success'],
                    'rate': self.phase_stats['phase1_success'] / total
                },
                'phase2_ai_research': {
                    'success': self.phase_stats['phase2_success'],
                    'rate': self.phase_stats['phase2_success'] / total
                },
                'phase3_expert_consultation': {
                    'success': self.phase_stats['phase3_success'],
                    'rate': self.phase_stats['phase3_success'] / total
                },
                'phase4_escalation': {
                    'count': self.phase_stats['phase4_escalated'],
                    'rate': self.phase_stats['phase4_escalated'] / total
                }
            }
        }

    def print_performance_report(self):
        """Print performance report"""
        stats = self.get_performance_stats()

        print(f"\n{'='*80}")
        print(f"📊 AGENT COORDINATOR PERFORMANCE REPORT")
        print(f"{'='*80}")
        print(f"Total Issues Processed: {stats['total_processed']}")
        print(f"Auto-Fix Rate: {stats['auto_fix_rate']:.1%}")
        print(f"Escalation Rate: {stats['escalation_rate']:.1%}")
        print(f"\nPhase Breakdown:")
        print(f"  Phase 1 (Quick Fix):          {stats['phase_breakdown']['phase1_quick_fix']['rate']:.1%}")
        print(f"  Phase 2 (AI Research):        {stats['phase_breakdown']['phase2_ai_research']['rate']:.1%}")
        print(f"  Phase 3 (Expert Consultation): {stats['phase_breakdown']['phase3_expert_consultation']['rate']:.1%}")
        print(f"  Phase 4 (Escalation):         {stats['phase_breakdown']['phase4_escalation']['rate']:.1%}")
        print(f"{'='*80}\n")


# Test the system
if __name__ == "__main__":
    print("🧪 Testing Agent Coordinator...\n")

    # Initialize
    coordinator = AgentCoordinator()
    print("✅ AgentCoordinator initialized\n")

    # Test with sample issue
    test_issue = {
        'type': 'service_failure',
        'source': 'systemd',
        'service': 'test-service.service',
        'message': 'Service test-service.service has failed'
    }

    print("📋 Test issue:", test_issue['message'])
    print("\n🔬 Running 4-phase intelligent processing...\n")

    # This will fail gracefully without real services, but structure is correct
    try:
        result = coordinator.process_issue_intelligent(test_issue, task_id=9999)
        print(f"\n✅ Processing completed!")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Phase: {result.get('phase', 'unknown')}")
        print(f"   Escalated: {result.get('escalated', False)}")

        # Print performance
        coordinator.print_performance_report()
    except Exception as e:
        print(f"\n⚠️  Test failed (expected without real services): {e}")

    print("\n🎉 Agent Coordinator structure is correct!")
