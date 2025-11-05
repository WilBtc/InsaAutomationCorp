"""
Retry Handler Integration Examples
Phase 12: Production Hardening - Week 1, Day 1

Shows how to integrate retry_handler.py with existing INSA CRM agent workers
for resilient operation with automatic retry on failures.

Author: Claude Code + Wil Aroca
Created: October 31, 2025
"""

import subprocess
import json
import logging
from retry_handler import with_retry, RetryConfig, STANDARD_RETRY, PERSISTENT_RETRY

logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Sizing Agent Worker with Retry
# ============================================================================

class SizingAgentWorker:
    """
    Sizing Agent Worker with automatic retry logic

    Uses PERSISTENT_RETRY for critical sizing operations that must succeed
    """

    def __init__(self):
        self.agent_name = "Dimensionamiento"
        logger.info(f"{self.agent_name} worker initialized with retry logic")

    @with_retry(PERSISTENT_RETRY)  # 5 attempts, 2s initial delay, up to 60s max
    def process_message(self, message: dict) -> dict:
        """
        Process sizing request with automatic retry

        If Claude Code subprocess fails (timeout, crash, etc), this will
        automatically retry up to 5 times with exponential backoff.

        Parameters:
            message: Message containing sizing request

        Returns:
            dict: Sizing results from Claude Code
        """
        logger.info(f"Processing sizing message: {message.get('id')}")

        # Extract payload
        payload = message.get('payload', {})
        prompt = self._build_sizing_prompt(payload)

        # Call Claude Code subprocess (this is the operation that may fail)
        result = self._call_claude_code(prompt)

        logger.info(f"Sizing completed successfully for message {message.get('id')}")
        return result

    def _build_sizing_prompt(self, payload: dict) -> str:
        """Build prompt for sizing operation"""
        return f"""
        INSA Dimensionamiento Request:
        Type: {payload.get('equipment_type')}
        Capacity: {payload.get('capacity')}
        Fluid: {payload.get('fluid_properties')}

        Calculate equipment sizing with ASME standards.
        """

    def _call_claude_code(self, prompt: str) -> dict:
        """
        Call Claude Code subprocess

        This may fail due to:
        - Subprocess timeout
        - Claude Code crash
        - System resource limits
        - Network issues (if using remote model)

        The @with_retry decorator will automatically handle these failures
        """
        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude Code failed: {result.stderr}")

            # Parse response
            response = json.loads(result.stdout)
            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude Code subprocess timeout (120s)")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Claude Code response: {e}")


# ============================================================================
# Example 2: CRM Agent Worker with Retry
# ============================================================================

class CRMAgentWorker:
    """
    CRM Agent Worker with automatic retry for database operations

    Uses STANDARD_RETRY for database queries (3 attempts, 1s initial delay)
    """

    def __init__(self):
        self.agent_name = "CRM"
        logger.info(f"{self.agent_name} worker initialized with retry logic")

    @with_retry(STANDARD_RETRY)  # 3 attempts, 1s initial delay, up to 30s max
    def fetch_lead_data(self, lead_id: str) -> dict:
        """
        Fetch lead data from ERPNext with automatic retry

        Database queries may fail temporarily due to:
        - Network hiccups
        - Database locks
        - Container restarts

        The retry logic handles these transient failures automatically.
        """
        logger.info(f"Fetching lead data for: {lead_id}")

        # Call ERPNext MCP server (may fail temporarily)
        result = self._query_erpnext(lead_id)

        if not result:
            raise ValueError(f"Lead {lead_id} not found")

        return result

    def _query_erpnext(self, lead_id: str) -> dict:
        """
        Query ERPNext via MCP server

        This simulates the actual ERPNext query - replace with real implementation
        """
        # In real implementation, this would call the ERPNext MCP server
        # For now, simulate with subprocess
        result = subprocess.run(
            ["docker", "exec", "frappe_docker_backend_1",
             "bench", "--site", "insa.local", "list-leads", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"ERPNext query failed: {result.stderr}")

        # Parse and filter for specific lead
        leads = json.loads(result.stdout)
        lead = next((l for l in leads if l.get('name') == lead_id), None)

        return lead

    @with_retry(RetryConfig(max_attempts=3, initial_delay=0.5, max_delay=5.0))
    def update_lead_score(self, lead_id: str, score: int) -> bool:
        """
        Update lead score with quick retry for fast operations

        Uses custom config with faster retry (0.5s initial delay, 5s max)
        """
        logger.info(f"Updating lead {lead_id} score to {score}")

        # Update in database (may fail temporarily)
        self._update_database(lead_id, score)

        return True

    def _update_database(self, lead_id: str, score: int):
        """Update database - may fail temporarily"""
        # Simulate database update
        if not (0 <= score <= 100):
            raise ValueError(f"Invalid score: {score}")

        # In real implementation, update PostgreSQL
        logger.info(f"Database updated: lead {lead_id} = {score}")


# ============================================================================
# Example 3: Integration with Message Bus
# ============================================================================

class ResilientMessageBusWorker:
    """
    Message bus worker with retry logic for message processing

    Shows how to add retry to the message processing loop
    """

    def __init__(self, worker_class):
        self.worker = worker_class()
        self.processed_count = 0
        self.error_count = 0

    @with_retry(STANDARD_RETRY)
    def process_message_with_retry(self, message: dict):
        """
        Process message with automatic retry

        If the worker's process_message fails, this will retry automatically
        """
        result = self.worker.process_message(message)
        self.processed_count += 1
        return result

    def run(self):
        """
        Main message processing loop with retry
        """
        logger.info(f"Starting resilient message bus worker for {self.worker.agent_name}")

        while True:
            try:
                # Get next message from queue (this part doesn't need retry)
                message = self._get_next_message()

                if message:
                    # Process with retry (this is the operation that may fail)
                    try:
                        result = self.process_message_with_retry(message)
                        logger.info(f"Message {message.get('id')} processed successfully")

                    except Exception as e:
                        # After all retries failed, log and move to dead letter queue
                        self.error_count += 1
                        logger.error(
                            f"Message {message.get('id')} failed after all retries: {e}",
                            exc_info=True
                        )
                        self._send_to_dead_letter_queue(message, str(e))

            except KeyboardInterrupt:
                logger.info("Shutting down worker...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}", exc_info=True)
                import time
                time.sleep(5)  # Wait before retrying loop

    def _get_next_message(self) -> dict:
        """Get next message from queue"""
        # Simulated - replace with actual message bus implementation
        return None

    def _send_to_dead_letter_queue(self, message: dict, reason: str):
        """Send failed message to dead letter queue"""
        logger.warning(f"Message {message.get('id')} sent to dead letter queue: {reason}")
        # In real implementation, store in dead_letter_queue.db


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    """
    Demonstrate integration with existing workers
    """

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("Retry Handler Integration Examples")
    print("="*70)

    # Example 1: Sizing Agent
    print("\n=== Example 1: Sizing Agent with Retry ===")
    sizing_worker = SizingAgentWorker()
    test_message = {
        'id': 'msg-001',
        'from_agent': 'orchestrator',
        'to_agent': 'sizing',
        'topic': 'sizing_request',
        'payload': {
            'equipment_type': 'separator',
            'capacity': '50 bbl/day',
            'fluid_properties': {
                'oil_sg': 0.85,
                'water_cut': 0.3,
                'gas_oil_ratio': 500
            }
        }
    }

    print("Processing sizing request (may retry if Claude Code fails)...")
    # Note: This will fail in test because Claude Code isn't actually called
    # In production, it would retry automatically on failures

    # Example 2: CRM Agent
    print("\n=== Example 2: CRM Agent with Retry ===")
    crm_worker = CRMAgentWorker()
    print("Worker initialized with retry logic")
    print("Database operations will automatically retry on transient failures")

    # Example 3: Integration Pattern
    print("\n=== Example 3: Integration Pattern ===")
    print("To integrate retry logic with existing agents:")
    print("1. Import: from retry_handler import with_retry, PERSISTENT_RETRY")
    print("2. Decorate: @with_retry(PERSISTENT_RETRY)")
    print("3. Apply to: process_message() methods")
    print("4. That's it! Automatic retry on failures")

    print("\n" + "="*70)
    print("Integration examples complete")
    print("="*70)
    print("\nNext steps:")
    print("1. Apply @with_retry decorator to existing agent workers")
    print("2. Test with real agent operations")
    print("3. Monitor retry behavior in logs")
    print("4. Tune retry configs based on observed failure patterns")
