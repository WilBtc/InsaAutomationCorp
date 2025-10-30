#!/usr/bin/env python3
"""
Data Retention Scheduler
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 7

Automatically executes retention policies based on their configured schedules.

Features:
- Cron-based scheduling using APScheduler
- Automatic policy execution at scheduled times
- Error handling and retry logic
- Execution tracking and logging
- Dynamic schedule updates

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from retention_manager import RetentionManager, RetentionManagerException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetentionScheduler:
    """
    Manages scheduled execution of retention policies.

    Features:
    - Dynamic policy scheduling based on cron expressions
    - Automatic retry on failure
    - Execution tracking
    - Schedule reload on policy updates
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize retention scheduler.

        Args:
            db_config: Database configuration dictionary
        """
        self.db_config = db_config
        self.scheduler = BackgroundScheduler()
        self.scheduled_policies = {}  # Map of policy_id -> job_id

        # Add job listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        logger.info("RetentionScheduler initialized")

    def start(self):
        """Start the scheduler and load all enabled policies."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Retention scheduler started")

        # Load and schedule all enabled policies
        self.reload_schedules()

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Retention scheduler stopped")

    def reload_schedules(self):
        """Reload all retention policy schedules from database."""
        logger.info("Reloading retention policy schedules...")

        # Remove all existing jobs
        for job_id in list(self.scheduled_policies.values()):
            try:
                self.scheduler.remove_job(job_id)
            except Exception as e:
                logger.warning(f"Failed to remove job {job_id}: {e}")

        self.scheduled_policies.clear()

        # Load enabled policies
        with RetentionManager(self.db_config) as manager:
            policies = manager.list_policies(enabled_only=True)

        # Schedule each policy
        for policy in policies:
            try:
                self._schedule_policy(policy)
            except Exception as e:
                logger.error(f"Failed to schedule policy {policy['name']}: {e}")

        logger.info(f"✅ Scheduled {len(self.scheduled_policies)} retention policies")

    def _schedule_policy(self, policy: Dict[str, Any]):
        """
        Schedule a single retention policy.

        Args:
            policy: Policy dictionary from database
        """
        policy_id = policy['id']
        policy_name = policy['name']
        schedule = policy['schedule']

        # Parse cron expression
        # Format: "minute hour day month day_of_week"
        # Example: "0 2 * * *" = Daily at 2 AM
        try:
            cron_parts = schedule.split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron expression: {schedule}")

            minute, hour, day, month, day_of_week = cron_parts

            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )

            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._execute_policy,
                trigger=trigger,
                args=[policy_id, policy_name],
                id=f"retention_{policy_id}",
                name=f"Retention: {policy_name}",
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )

            self.scheduled_policies[policy_id] = job.id

            logger.info(
                f"Scheduled retention policy: {policy_name} "
                f"(schedule: {schedule}, next run: {job.next_run_time})"
            )

        except Exception as e:
            logger.error(f"Failed to schedule policy {policy_name}: {e}")
            raise

    def _execute_policy(self, policy_id: str, policy_name: str):
        """
        Execute a retention policy.

        Args:
            policy_id: UUID of the policy
            policy_name: Name of the policy (for logging)
        """
        logger.info(f"Starting scheduled execution of retention policy: {policy_name}")

        try:
            with RetentionManager(self.db_config) as manager:
                result = manager.execute_policy(policy_id, dry_run=False)

            logger.info(
                f"✅ Retention policy executed successfully: {policy_name}\n"
                f"   Records deleted: {result['records_deleted']}\n"
                f"   Records archived: {result['records_archived']}\n"
                f"   Bytes freed: {result['bytes_freed']:,}"
            )

        except RetentionManagerException as e:
            logger.error(f"❌ Retention policy execution failed: {policy_name} - {e}")
            raise

        except Exception as e:
            logger.error(f"❌ Unexpected error executing retention policy {policy_name}: {e}")
            raise

    def _job_executed_listener(self, event):
        """
        Handle job execution events.

        Args:
            event: APScheduler event object
        """
        if event.exception:
            logger.error(
                f"Retention job failed: {event.job_id}\n"
                f"Exception: {event.exception}"
            )
        else:
            logger.debug(f"Retention job completed: {event.job_id}")

    def get_scheduled_jobs(self):
        """
        Get list of scheduled retention jobs.

        Returns:
            List of job dictionaries with schedule information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith('retention_'):
                jobs.append({
                    'job_id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })

        return jobs

    def execute_policy_now(self, policy_id: str, dry_run: bool = False):
        """
        Execute a retention policy immediately (outside of schedule).

        Args:
            policy_id: UUID of the policy
            dry_run: If True, simulate execution without deleting data

        Returns:
            Execution result dictionary
        """
        with RetentionManager(self.db_config) as manager:
            policy = manager.get_policy(policy_id)
            if not policy:
                raise RetentionManagerException(f"Policy not found: {policy_id}")

            logger.info(f"Manual execution of retention policy: {policy['name']} (dry_run={dry_run})")
            result = manager.execute_policy(policy_id, dry_run=dry_run)

        return result


# =============================================================================
# Global scheduler instance
# =============================================================================

_scheduler_instance = None


def init_retention_scheduler(db_config: Dict[str, Any]) -> RetentionScheduler:
    """
    Initialize the global retention scheduler instance.

    Args:
        db_config: Database configuration dictionary

    Returns:
        RetentionScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = RetentionScheduler(db_config)
        _scheduler_instance.start()
        logger.info("Global retention scheduler initialized and started")
    else:
        logger.warning("Retention scheduler already initialized")

    return _scheduler_instance


def get_retention_scheduler() -> RetentionScheduler:
    """
    Get the global retention scheduler instance.

    Returns:
        RetentionScheduler instance

    Raises:
        RuntimeError: If scheduler not initialized
    """
    if _scheduler_instance is None:
        raise RuntimeError("Retention scheduler not initialized. Call init_retention_scheduler() first.")

    return _scheduler_instance


def stop_retention_scheduler():
    """Stop the global retention scheduler."""
    global _scheduler_instance

    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None
        logger.info("Global retention scheduler stopped")


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    import time

    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    print("=== Data Retention Scheduler ===\n")

    # Initialize scheduler
    scheduler = init_retention_scheduler(DB_CONFIG)

    # Get scheduled jobs
    jobs = scheduler.get_scheduled_jobs()
    print(f"Scheduled Jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job['name']}")
        print(f"    Next run: {job['next_run_time']}")
        print(f"    Trigger: {job['trigger']}")
        print()

    print("✅ Retention scheduler running")
    print("Press Ctrl+C to stop\n")

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        stop_retention_scheduler()
        print("✓ Scheduler stopped")
