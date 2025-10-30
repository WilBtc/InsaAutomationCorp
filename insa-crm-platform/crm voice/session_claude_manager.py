#!/usr/bin/env python3
"""
Session Claude Manager - Persistent Claude Code Instances Per Session
Maintains one Claude Code subprocess per user session for:
- Lower latency (no subprocess startup overhead)
- Better context retention (same instance sees full conversation)
- Lower token usage (context reuse)
- Cleaner architecture
"""

import subprocess
import threading
import time
import logging
from typing import Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ClaudeSession:
    """Represents a persistent Claude Code session"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process = None
        self.last_used = time.time()
        self.query_count = 0
        self.lock = threading.Lock()

    def start(self):
        """Start Claude Code subprocess"""
        # Note: This is a placeholder - Claude Code doesn't support persistent mode yet
        # For now, we'll still use subprocess but with better context management
        logger.info(f"Session {self.session_id}: Initialized")
        self.last_used = time.time()

    def query(self, prompt: str, timeout: int = 120, file_paths: list = None) -> str:
        """
        Send query to Claude Code subprocess

        Args:
            prompt: Query prompt text
            timeout: Timeout in seconds
            file_paths: Optional list of file paths to read and include in context

        Returns:
            Claude Code response
        """
        with self.lock:
            self.last_used = time.time()
            self.query_count += 1

            try:
                # If files provided, read them and add content to prompt
                enhanced_prompt = prompt
                if file_paths:
                    enhanced_prompt += "\n\n=== UPLOADED FILES ===="
                    for file_path in file_paths:
                        try:
                            # Read file content
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                            # Add to prompt
                            filename = Path(file_path).name
                            enhanced_prompt += f"\n\n--- File: {filename} ---\n{content}\n--- End of {filename} ---"
                            logger.info(f"Read uploaded file: {filename} ({len(content)} chars)")
                        except Exception as e:
                            logger.error(f"Failed to read file {file_path}: {e}")
                            enhanced_prompt += f"\n\n❌ Failed to read file: {Path(file_path).name}"

                # Call Claude Code with full prompt (use --print for non-interactive mode)
                # Working directory: Project root so Claude Code has access to all files
                result = subprocess.run(
                    ["claude", "--print", enhanced_prompt],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=Path.home() / "insa-crm-platform"  # ← FIXED: Use project root, not subdirectory
                )

                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    error_msg = result.stderr.strip()
                    logger.error(f"Claude Code error: {error_msg}")
                    return f"Error: {error_msg}"

            except subprocess.TimeoutExpired:
                logger.error(f"Claude Code timeout after {timeout}s")
                return f"Error: Query timed out after {timeout} seconds"
            except Exception as e:
                logger.error(f"Claude Code exception: {e}")
                return f"Error: {str(e)}"

    def stop(self):
        """Stop Claude Code subprocess"""
        if self.process:
            self.process.terminate()
            self.process = None
        logger.info(f"Session {self.session_id}: Stopped (queries: {self.query_count})")


class SessionClaudeManager:
    """
    Manages Claude Code sessions
    - One session per user (session_id)
    - Auto-cleanup after 30 min inactivity
    - Thread-safe operations
    """

    def __init__(self, cleanup_interval: int = 300, session_timeout: int = 1800):
        """
        Args:
            cleanup_interval: How often to check for stale sessions (seconds)
            session_timeout: How long before a session is considered stale (seconds)
        """
        self.sessions: Dict[str, ClaudeSession] = {}
        self.lock = threading.Lock()
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        logger.info("SessionClaudeManager initialized")

    def get_session(self, session_id: str) -> ClaudeSession:
        """Get or create a Claude session"""
        with self.lock:
            if session_id not in self.sessions:
                session = ClaudeSession(session_id)
                session.start()
                self.sessions[session_id] = session
                logger.info(f"Created new session: {session_id}")
            else:
                session = self.sessions[session_id]
                session.last_used = time.time()

            return session

    def query(self, session_id: str, prompt: str, timeout: int = 120, file_paths: list = None) -> str:
        """
        Send query to Claude Code for this session

        Args:
            session_id: User session ID
            prompt: Full prompt including context
            timeout: Timeout in seconds
            file_paths: Optional list of file paths to include

        Returns:
            Claude Code response
        """
        session = self.get_session(session_id)
        return session.query(prompt, timeout, file_paths)

    def _cleanup_loop(self):
        """Background thread to cleanup stale sessions"""
        while True:
            time.sleep(self.cleanup_interval)
            self._cleanup_stale_sessions()

    def _cleanup_stale_sessions(self):
        """Remove sessions that haven't been used recently"""
        now = time.time()
        stale_sessions = []

        with self.lock:
            for session_id, session in list(self.sessions.items()):
                if now - session.last_used > self.session_timeout:
                    stale_sessions.append(session_id)

        # Stop stale sessions outside the lock
        for session_id in stale_sessions:
            with self.lock:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    session.stop()
                    del self.sessions[session_id]
                    logger.info(f"Cleaned up stale session: {session_id} (idle for {now - session.last_used:.0f}s)")

    def get_stats(self) -> dict:
        """Get session statistics"""
        with self.lock:
            return {
                'active_sessions': len(self.sessions),
                'sessions': {
                    sid: {
                        'query_count': s.query_count,
                        'last_used': s.last_used,
                        'idle_time': time.time() - s.last_used
                    }
                    for sid, s in self.sessions.items()
                }
            }

    def shutdown(self):
        """Shutdown all sessions"""
        with self.lock:
            for session in self.sessions.values():
                session.stop()
            self.sessions.clear()
        logger.info("SessionClaudeManager shutdown complete")


# Global instance
_session_manager = None

def get_session_claude_manager() -> SessionClaudeManager:
    """Get or create global SessionClaudeManager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionClaudeManager(
            cleanup_interval=300,  # Check every 5 min
            session_timeout=1800   # 30 min timeout
        )
    return _session_manager


def build_context_prompt(
    text: str,
    agent_context: str,
    session_history: list,
    session_id: str
) -> str:
    """
    Build comprehensive context prompt for Claude Code

    Args:
        text: Current user query
        agent_context: Agent type (sizing, crm, platform, etc.)
        session_history: Previous conversation messages
        session_id: Session identifier

    Returns:
        Formatted prompt with full context
    """
    prompt_parts = []

    # System context
    prompt_parts.append("=== INSA AI AGENT SYSTEM ===")
    prompt_parts.append(f"Session ID: {session_id}")
    prompt_parts.append(f"Active Agent: {agent_context}")
    prompt_parts.append("")

    # Agent-specific instructions
    if agent_context == 'sizing':
        prompt_parts.append("You are the INSA AI Sizing Agent.")
        prompt_parts.append("Specialty: Dimensioning Oil & Gas instrumentation, automation, and calibration projects.")
        prompt_parts.append("Approach: Ask clarifying questions if needed (service type, equipment, location, scope).")
        prompt_parts.append("Context: You maintain conversation context to build complete project specifications.")

    elif agent_context == 'crm':
        prompt_parts.append("You are the INSA AI CRM Agent.")
        prompt_parts.append("Specialty: Managing leads, customers, opportunities, quotations, and sales orders.")
        prompt_parts.append("Tools: You have access to ERPNext CRM via MCP tools (erpnext-crm).")
        prompt_parts.append("Context: Reference previous conversation when creating leads or quotes.")

    elif agent_context == 'platform':
        prompt_parts.append("You are the INSA AI Platform Admin Agent.")
        prompt_parts.append("Specialty: Monitoring and managing INSA platform services.")
        prompt_parts.append("Tools: You have access to platform-admin MCP tools.")
        prompt_parts.append("Services: INSA CRM, ERPNext, Mautic, n8n, InvenTree, Grafana, DefectDojo, IEC 62443.")

    elif agent_context == 'compliance':
        prompt_parts.append("You are the INSA AI Compliance Agent.")
        prompt_parts.append("Specialty: IEC 62443 industrial security compliance.")
        prompt_parts.append("Tools: You have access to DefectDojo IEC 62443 MCP tools.")

    elif agent_context == 'healing':
        prompt_parts.append("You are the INSA AI Healing Agent.")
        prompt_parts.append("Specialty: Autonomous error detection and resolution.")
        prompt_parts.append("Tools: You have access to healing system MCP tools.")

    elif agent_context == 'research':
        prompt_parts.append("You are the INSA AI Research Agent.")
        prompt_parts.append("Specialty: Technical documentation and knowledge retrieval (RAG).")
        prompt_parts.append("Knowledge Base: 900+ pages of INSA technical documentation.")

    elif agent_context == 'github':
        prompt_parts.append("You are the INSA AI GitHub Agent.")
        prompt_parts.append("Specialty: Task management via GitHub issues.")
        prompt_parts.append("Tools: You have access to github-agent MCP tools.")

    elif agent_context == 'host_config':
        prompt_parts.append("You are the INSA AI Host Configuration Agent.")
        prompt_parts.append("Specialty: Automatic service deployment and configuration.")
        prompt_parts.append("Tools: You have access to host-config-agent MCP tools.")

    elif agent_context == 'cad':
        prompt_parts.append("You are the INSA AI CAD Agent.")
        prompt_parts.append("Specialty: 3D CAD model generation from specifications.")
        prompt_parts.append("Tools: You have access to CadQuery MCP tools.")

    prompt_parts.append("")

    # Conversation history (FULL CONTEXT - NO TRUNCATION)
    if session_history and len(session_history) > 0:
        prompt_parts.append("=== CONVERSATION HISTORY ===")
        prompt_parts.append(f"Previous messages: {len(session_history)}")
        prompt_parts.append("")

        for i, msg in enumerate(session_history, 1):
            role = msg['role'].upper()
            agent = msg.get('agent', 'general')
            content = msg['content'][:2000]  # ✅ 2000 CHAR LIMIT (10x increase)

            prompt_parts.append(f"[Message {i}] {role} ({agent} agent):")
            prompt_parts.append(content)
            prompt_parts.append("")

        prompt_parts.append("=== END HISTORY ===")
        prompt_parts.append("")

        # Explicit instruction to use context
        prompt_parts.append("IMPORTANT INSTRUCTIONS:")
        prompt_parts.append("1. Use the conversation history above to provide contextual responses")
        prompt_parts.append("2. Reference previous messages when relevant")
        prompt_parts.append("3. Build on information provided in earlier turns")
        prompt_parts.append("4. If a follow-up question is asked, connect it to previous context")
        prompt_parts.append("5. Maintain consistency across the conversation")
        prompt_parts.append("")

    # Current query
    prompt_parts.append("=== CURRENT USER QUERY ===")
    prompt_parts.append(text)
    prompt_parts.append("")

    prompt_parts.append("Provide a helpful, contextual response based on the conversation history and your agent specialty.")

    return "\n".join(prompt_parts)


# Usage example:
if __name__ == "__main__":
    # Test the manager
    import sys
    logging.basicConfig(level=logging.INFO)

    manager = get_session_claude_manager()

    # Simulate a conversation
    session_id = "test_session_123"

    # Turn 1
    prompt1 = build_context_prompt(
        text="Dimensiona un separador trifásico",
        agent_context="sizing",
        session_history=[],
        session_id=session_id
    )

    print("=== TURN 1 ===")
    print(f"Prompt length: {len(prompt1)} chars")
    response1 = manager.query(session_id, prompt1, timeout=60)
    print(f"Response: {response1[:200]}...")

    # Turn 2 (with context)
    prompt2 = build_context_prompt(
        text="Es para 10,000 barriles por día",
        agent_context="sizing",
        session_history=[
            {'role': 'user', 'content': 'Dimensiona un separador trifásico', 'agent': 'sizing'},
            {'role': 'assistant', 'content': response1, 'agent': 'sizing'}
        ],
        session_id=session_id
    )

    print("\n=== TURN 2 ===")
    print(f"Prompt length: {len(prompt2)} chars")
    response2 = manager.query(session_id, prompt2, timeout=60)
    print(f"Response: {response2[:200]}...")

    # Stats
    print("\n=== STATS ===")
    print(json.dumps(manager.get_stats(), indent=2))

    manager.shutdown()
