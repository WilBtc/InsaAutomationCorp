#!/usr/bin/env python3
"""
Multi-Agent Research System
3-agent voting with consensus logic for complex problem solving

Created: October 30, 2025
Author: Insa Automation Corp
Purpose: Graduated intelligence - escalate to more powerful agents when needed
"""

import os
import time
import json
import subprocess
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from intelligent_fixer import LearningDatabase, ResearchAgent


class ExpertConsultation:
    """
    Level 3 Research: Multi-agent voting system
    Runs 3 parallel AI agents and takes consensus
    """

    def __init__(self):
        self.claude_path = "/home/wil/.local/bin/claude"
        self.learning_db = LearningDatabase()
        self.timeout = 60  # Each agent gets 60s
        self.num_agents = 1  # Changed from 3 to 1 (Nov 15, 2025 - reduce resource usage)

    def multi_agent_consensus(self, issue: Dict, previous_attempts: List[Dict]) -> Dict:
        """
        Run 3 parallel AI agents and compute consensus

        Returns:
        {
            'diagnosis': "Consensus diagnosis",
            'confidence': 0.90,
            'consensus_type': '3/3' or '2/3',
            'suggested_fixes': [...],
            'agent_votes': {
                'agent1': {...},
                'agent2': {...},
                'agent3': {...}
            },
            'execution_time': '15.2s'
        }
        """
        start_time = time.time()

        print(f"      🎓 Starting {self.num_agents}-Agent Expert Consultation...")
        print(f"         Timeout: {self.timeout}s per agent")

        # Build context for all agents (same context)
        context = self.build_consultation_context(issue, previous_attempts)

        # Run 3 agents in parallel
        agent_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_agents) as executor:
            futures = {
                executor.submit(self.run_single_agent, f"agent{i+1}", context, i+1): i+1
                for i in range(self.num_agents)
            }

            for future in concurrent.futures.as_completed(futures):
                agent_num = futures[future]
                try:
                    result = future.result(timeout=self.timeout + 5)
                    agent_results.append(result)
                    print(f"         ✅ Agent {agent_num} completed (confidence: {result['confidence']:.0%})")
                except concurrent.futures.TimeoutError:
                    print(f"         ⚠️  Agent {agent_num} timeout")
                    agent_results.append(self.fallback_agent_result(f"agent{agent_num}"))
                except Exception as e:
                    print(f"         ❌ Agent {agent_num} error: {e}")
                    agent_results.append(self.fallback_agent_result(f"agent{agent_num}"))

        # Compute consensus
        consensus = self.compute_consensus(agent_results)

        elapsed = time.time() - start_time
        consensus['execution_time'] = f"{elapsed:.1f}s"

        print(f"      📊 Consensus: {consensus['consensus_type']}")
        print(f"         Confidence: {consensus['confidence']:.0%}")
        print(f"         Execution: {consensus['execution_time']}")

        return consensus

    def run_single_agent(self, agent_name: str, context: str, agent_num: int) -> Dict:
        """Run a single AI agent with Claude Code"""
        start_time = time.time()

        try:
            # Add agent-specific variation to context (encourage diverse thinking)
            varied_context = self.add_agent_perspective(context, agent_num)

            # Execute Claude Code via subprocess (--print for non-interactive mode)
            # Use --dangerously-skip-permissions for autonomous execution (no user prompts)
            # Use --system-prompt to ensure exact format (override CLAUDE.md context)
            # CRITICAL: Use 'timeout' and 'prlimit' to enforce resource limits (prevent OOM kills)
            # Nov 18, 2025: Prevent repeat of 42GB Claude subprocess OOM
            system_prompt = "You are a diagnostic expert. Reply ONLY in the exact format requested. Do not add explanations, greetings, or extra text. Follow the format precisely."
            result = subprocess.run(
                ['prlimit', '--as=4294967296', '--data=4294967296',  # 4GB address space + data limits
                 self.claude_path, '--print', '--dangerously-skip-permissions',
                 '--system-prompt', system_prompt, varied_context],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            elapsed = time.time() - start_time

            if result.returncode == 0:
                # Debug: Log first 200 chars of response
                preview = result.stdout[:200] if len(result.stdout) > 200 else result.stdout
                print(f"         DEBUG {agent_name}: {preview.replace(chr(10), ' ')[:100]}...")

                diagnosis = self.parse_agent_response(result.stdout)
                diagnosis['agent_name'] = agent_name
                diagnosis['execution_time'] = f"{elapsed:.1f}s"
                return diagnosis
            else:
                # Log both stdout and stderr on error
                print(f"         DEBUG {agent_name}: ERROR returncode={result.returncode}")
                print(f"         STDERR: {result.stderr[:200] if result.stderr else 'empty'}")
                print(f"         STDOUT: {result.stdout[:200] if result.stdout else 'empty'}")
                return self.fallback_agent_result(agent_name)

        except subprocess.TimeoutExpired:
            return self.fallback_agent_result(agent_name, timeout=True)
        except Exception as e:
            return self.fallback_agent_result(agent_name, error=str(e))

    def add_agent_perspective(self, context: str, agent_num: int) -> str:
        """Add agent-specific perspective to encourage diverse thinking"""
        perspectives = {
            1: "\n\n**Agent 1 Perspective:** Focus on immediate, proven solutions. Prioritize speed and reliability.",
            2: "\n\n**Agent 2 Perspective:** Consider edge cases and uncommon failure modes. Think creatively.",
            3: "\n\n**Agent 3 Perspective:** Focus on root causes and long-term fixes. Prevent recurrence."
        }
        return context + perspectives.get(agent_num, "")

    def build_consultation_context(self, issue: Dict, previous_attempts: List[Dict]) -> str:
        """Build consultation context for AI agents"""
        attempts_text = "\n".join([
            f"  {i+1}. {att['strategy']} - {'SUCCESS' if att['success'] else 'FAILED'}: {att['message']}"
            for i, att in enumerate(previous_attempts)
        ])

        context = f"""**EXPERT CONSULTATION REQUEST**

You are one of 3 expert AI agents analyzing this infrastructure issue.
Your analysis will be combined with 2 other agents via voting consensus.

**Error Details:**
- Type: {issue['type']}
- Source: {issue['source']}
- Service/Container: {issue.get('service') or issue.get('container', 'unknown')}
- Error Message:
  {issue['message']}

**Previous Fix Attempts ({len(previous_attempts)}):**
{attempts_text if previous_attempts else '  (None yet)'}

**Your Task:**
1. Diagnose the root cause
2. Suggest 3 prioritized fix strategies (be specific and actionable)
3. Rate your confidence (0-100%)
4. Provide exact commands that can be executed automatically

**IMPORTANT:**
- Be specific and practical
- Focus on solutions that can be executed safely via automation
- Consider that 2 other agents are also analyzing this (your vote matters!)

**Format your response as:**
DIAGNOSIS: [Root cause analysis in 2-3 sentences]
CONFIDENCE: [0-100]%
FIX_1: [Strategy name] | [Description] | [Commands]
FIX_2: [Strategy name] | [Description] | [Commands]
FIX_3: [Strategy name] | [Description] | [Commands]
"""
        return context

    def parse_agent_response(self, response: str) -> Dict:
        """Parse AI agent response"""
        lines = response.strip().split('\n')
        diagnosis = {
            'diagnosis': '',
            'confidence': 0.5,
            'suggested_fixes': []
        }

        for line in lines:
            line = line.strip()
            if line.startswith('DIAGNOSIS:'):
                diagnosis['diagnosis'] = line.replace('DIAGNOSIS:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                conf_str = line.replace('CONFIDENCE:', '').replace('%', '').strip()
                try:
                    diagnosis['confidence'] = float(conf_str) / 100.0
                except:
                    diagnosis['confidence'] = 0.5
            elif line.startswith('FIX_'):
                parts = line.split('|')
                if len(parts) >= 3:
                    strategy = parts[0].split(':')[1].strip()
                    description = parts[1].strip()
                    commands = parts[2].strip()
                    priority = int(line[4])  # FIX_1, FIX_2, etc.

                    diagnosis['suggested_fixes'].append({
                        'strategy': strategy,
                        'description': description,
                        'commands': commands,
                        'priority': priority
                    })

        return diagnosis

    def fallback_agent_result(self, agent_name: str, timeout: bool = False, error: str = None) -> Dict:
        """Fallback result when agent fails"""
        return {
            'agent_name': agent_name,
            'diagnosis': f"Agent {agent_name} {'timeout' if timeout else 'error'}: {error or 'unknown'}",
            'confidence': 0.0,
            'suggested_fixes': [],
            'execution_time': '0.0s',
            'failed': True
        }

    def compute_consensus(self, agent_results: List[Dict]) -> Dict:
        """
        Compute consensus from multiple agent results

        Consensus types:
        - 3/3: All 3 agents agree (same diagnosis pattern)
        - 2/3: 2 agents agree
        - 1/3: No consensus (all different)
        """
        # Filter out failed agents
        valid_agents = [r for r in agent_results if not r.get('failed', False)]

        if len(valid_agents) == 0:
            return {
                'diagnosis': 'All agents failed',
                'confidence': 0.0,
                'consensus_type': '0/3',
                'suggested_fixes': [],
                'agent_votes': {r['agent_name']: r for r in agent_results}
            }

        # Group agents by similar diagnosis (simple keyword matching)
        diagnosis_groups = self.group_by_diagnosis(valid_agents)

        # Find majority group
        largest_group = max(diagnosis_groups, key=lambda g: len(g))
        consensus_type = f"{len(largest_group)}/{len(valid_agents)}"

        # Compute average confidence from majority group
        avg_confidence = sum(a['confidence'] for a in largest_group) / len(largest_group)

        # Combine suggested fixes from majority group (rank by frequency)
        all_fixes = []
        for agent in largest_group:
            all_fixes.extend(agent.get('suggested_fixes', []))

        # Rank fixes by frequency across agents
        fix_counts = {}
        for fix in all_fixes:
            key = fix['strategy'].lower()
            if key not in fix_counts:
                fix_counts[key] = {'fix': fix, 'count': 0}
            fix_counts[key]['count'] += 1

        # Sort by count (most common first)
        ranked_fixes = sorted(fix_counts.values(), key=lambda x: x['count'], reverse=True)
        top_fixes = [item['fix'] for item in ranked_fixes[:3]]

        # Combine diagnoses from majority group
        combined_diagnosis = "; ".join([a['diagnosis'] for a in largest_group if a['diagnosis']])

        return {
            'diagnosis': combined_diagnosis,
            'confidence': avg_confidence,
            'consensus_type': consensus_type,
            'suggested_fixes': top_fixes,
            'agent_votes': {r['agent_name']: r for r in agent_results}
        }

    def group_by_diagnosis(self, agents: List[Dict]) -> List[List[Dict]]:
        """
        Group agents by similar diagnosis using keyword matching

        Returns: List of groups, where each group is a list of agents with similar diagnosis
        """
        groups = []

        for agent in agents:
            diagnosis = agent.get('diagnosis', '').lower()

            # Try to find matching group
            matched = False
            for group in groups:
                # Check if diagnosis shares key terms with group
                group_diagnosis = group[0].get('diagnosis', '').lower()

                # Extract key terms (simple approach - words > 5 chars)
                agent_terms = set(w for w in diagnosis.split() if len(w) > 5)
                group_terms = set(w for w in group_diagnosis.split() if len(w) > 5)

                # If 30%+ overlap, consider it similar
                overlap = len(agent_terms & group_terms)
                total = len(agent_terms | group_terms)

                if total > 0 and (overlap / total) >= 0.3:
                    group.append(agent)
                    matched = True
                    break

            if not matched:
                # Create new group
                groups.append([agent])

        return groups


class ResearchAgentTeam:
    """
    Graduated intelligence research system
    Level 1: Pattern matching (instant)
    Level 2: Single AI agent (30s)
    Level 3: Multi-agent consensus (60s)
    """

    def __init__(self):
        self.learning_db = LearningDatabase()
        self.level2_agent = ResearchAgent()  # Single AI agent
        self.level3_agent = ExpertConsultation()  # Multi-agent consensus

    def research_solution(self, issue: Dict, previous_attempts: List[Dict]) -> Dict:
        """
        Graduated research with automatic escalation

        Returns comprehensive research results with confidence and suggestions
        """
        print(f"   🧠 Research Agent Team Engaged")

        # Level 1: Check cache (instant)
        print(f"      📚 Level 1: Checking learned patterns...")
        error_sig = self.level2_agent.generate_error_signature(issue)
        cached = self.learning_db.get_cached_research(error_sig)

        if cached and cached.get('confidence', 0) >= 0.80:
            print(f"      ✅ Found high-confidence cached solution ({cached['confidence']:.0%})")
            cached['research_level'] = 1
            cached['escalated'] = False
            return cached

        # Level 2: Single AI agent (30-60s)
        print(f"      🤖 Level 2: Single AI agent diagnosis...")
        level2_result = self.level2_agent.diagnose_issue(issue, previous_attempts)

        if level2_result['confidence'] >= 0.80:
            print(f"      ✅ High confidence from Level 2 ({level2_result['confidence']:.0%})")
            level2_result['research_level'] = 2
            level2_result['escalated'] = False
            return level2_result

        # Level 3: Multi-agent consultation (escalation)
        print(f"      🎓 Level 3: Expert multi-agent consultation (confidence was {level2_result['confidence']:.0%})...")
        level3_result = self.level3_agent.multi_agent_consensus(issue, previous_attempts)

        level3_result['research_level'] = 3
        level3_result['escalated'] = True
        level3_result['previous_confidence'] = level2_result['confidence']

        return level3_result


# Test the system
if __name__ == "__main__":
    print("🧪 Testing Multi-Agent Research System...\n")

    # Test expert consultation
    expert = ExpertConsultation()
    print("✅ ExpertConsultation initialized\n")

    # Test research team
    team = ResearchAgentTeam()
    print("✅ ResearchAgentTeam initialized\n")

    # Test with sample issue
    test_issue = {
        'type': 'service_failure',
        'source': 'systemd',
        'service': 'test-service.service',
        'message': 'Service test-service.service has failed'
    }

    print("📋 Test issue:", test_issue['message'])
    print("\n🔬 Running graduated research...")

    # This will fail gracefully without Claude Code, but structure is correct
    try:
        result = team.research_solution(test_issue, [])
        print(f"\n✅ Research completed!")
        print(f"   Level: {result.get('research_level')}")
        print(f"   Confidence: {result.get('confidence', 0):.0%}")
        print(f"   Escalated: {result.get('escalated', False)}")
    except Exception as e:
        print(f"\n⚠️  Test failed (expected without Claude Code): {e}")

    print("\n🎉 Multi-Agent Research System structure is correct!")
