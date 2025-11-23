#!/usr/bin/env python3
"""
ML Training Scheduler for the Alkhorayef ESP IoT Platform.

This script automatically trains ML models for all active wells on a weekly schedule.
It can be run as a cron job or standalone script.

Usage:
    # Train all wells
    python scripts/ml_training_scheduler.py

    # Train specific well
    python scripts/ml_training_scheduler.py --well-id WELL-001

    # Dry run (no training, just list wells)
    python scripts/ml_training_scheduler.py --dry-run

    # Custom training days
    python scripts/ml_training_scheduler.py --days 45
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import get_logger, DatabaseError, ValidationError
from app.db import get_db_pool
from app.services.ml import (
    AnomalyDetectionService,
    PredictiveMaintenanceService,
)


logger = get_logger(__name__)


class MLTrainingScheduler:
    """Scheduler for automated ML model training."""

    def __init__(self):
        """Initialize scheduler."""
        self.db_pool = get_db_pool()
        self.anomaly_service = AnomalyDetectionService()
        self.predictive_service = PredictiveMaintenanceService()

    def get_active_wells(self, hours: int = 24) -> List[str]:
        """
        Get list of wells with recent telemetry data.

        Args:
            hours: Number of hours to look back for activity

        Returns:
            List of active well IDs
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            query = """
                SELECT DISTINCT well_id, COUNT(*) as reading_count
                FROM esp_telemetry
                WHERE timestamp >= %s
                GROUP BY well_id
                HAVING COUNT(*) >= 50
                ORDER BY well_id
            """

            result = self.db_pool.execute_query(
                query,
                params=(start_time,),
                fetch=True,
                return_dict=True
            )

            wells = [row["well_id"] for row in result] if result else []

            logger.info(
                f"Found {len(wells)} active wells",
                extra={"extra_fields": {"wells": wells, "hours": hours}}
            )

            return wells

        except Exception as e:
            logger.error("Failed to get active wells", exc_info=e)
            return []

    def train_well(
        self,
        well_id: str,
        days: int = 30,
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train all ML models for a specific well.

        Args:
            well_id: Well identifier
            days: Days of training data
            contamination: Expected anomaly rate

        Returns:
            Dictionary with training results
        """
        results = {
            "well_id": well_id,
            "started_at": datetime.utcnow().isoformat(),
            "anomaly_detection": None,
            "predictive_maintenance": None,
            "success": False,
            "errors": []
        }

        try:
            logger.info(
                f"Starting training for well {well_id}",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "days": days,
                        "contamination": contamination,
                    }
                }
            )

            # Train anomaly detection
            try:
                anomaly_result = self.anomaly_service.train_model(
                    well_id=well_id,
                    days=days,
                    contamination=contamination,
                    n_estimators=100
                )
                results["anomaly_detection"] = {
                    "success": True,
                    "version": anomaly_result.get("version"),
                    "training_records": anomaly_result.get("training_records"),
                    "anomaly_rate": anomaly_result.get("anomaly_rate"),
                }
                logger.info(f"Anomaly detection model trained for {well_id}")
            except Exception as e:
                error_msg = f"Anomaly detection training failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=e)

            # Train predictive maintenance
            try:
                predictive_result = self.predictive_service.train_model(
                    well_id=well_id,
                    days=days
                )
                results["predictive_maintenance"] = {
                    "success": True,
                    "models": list(predictive_result.get("models_trained", {}).keys()),
                    "training_duration": predictive_result.get("training_duration_seconds"),
                }
                logger.info(f"Predictive maintenance models trained for {well_id}")
            except Exception as e:
                error_msg = f"Predictive maintenance training failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=e)

            # Check if at least one model trained successfully
            if results["anomaly_detection"] or results["predictive_maintenance"]:
                results["success"] = True

            results["completed_at"] = datetime.utcnow().isoformat()

            return results

        except Exception as e:
            error_msg = f"Training failed for well {well_id}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=e)
            results["completed_at"] = datetime.utcnow().isoformat()
            return results

    def train_all_wells(
        self,
        days: int = 30,
        contamination: float = 0.1,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Train models for all active wells.

        Args:
            days: Days of training data
            contamination: Expected anomaly rate
            dry_run: If True, only list wells without training

        Returns:
            Dictionary with overall training results
        """
        start_time = datetime.utcnow()

        # Get active wells
        wells = self.get_active_wells()

        if not wells:
            logger.warning("No active wells found for training")
            return {
                "success": False,
                "message": "No active wells found",
                "wells_count": 0,
            }

        logger.info(f"Found {len(wells)} wells to train")

        if dry_run:
            logger.info(f"DRY RUN: Would train {len(wells)} wells: {wells}")
            return {
                "success": True,
                "dry_run": True,
                "wells_count": len(wells),
                "wells": wells,
            }

        # Train each well
        training_results = []
        successful_wells = []
        failed_wells = []

        for well_id in wells:
            result = self.train_well(well_id, days, contamination)
            training_results.append(result)

            if result["success"]:
                successful_wells.append(well_id)
            else:
                failed_wells.append(well_id)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "success": len(successful_wells) > 0,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "wells_count": len(wells),
            "successful_count": len(successful_wells),
            "failed_count": len(failed_wells),
            "successful_wells": successful_wells,
            "failed_wells": failed_wells,
            "training_results": training_results,
        }

        logger.info(
            f"Training complete: {len(successful_wells)}/{len(wells)} wells successful",
            extra={"extra_fields": summary}
        )

        return summary


def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description="ML Training Scheduler for ESP IoT Platform"
    )
    parser.add_argument(
        "--well-id",
        type=str,
        help="Train specific well only"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of training data (default: 30)"
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.1,
        help="Expected anomaly rate for Isolation Forest (default: 0.1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List wells without training"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    try:
        scheduler = MLTrainingScheduler()

        if args.well_id:
            # Train specific well
            print(f"Training models for well: {args.well_id}")
            result = scheduler.train_well(
                well_id=args.well_id,
                days=args.days,
                contamination=args.contamination
            )

            if result["success"]:
                print(f"SUCCESS: Models trained for {args.well_id}")
                if args.verbose:
                    print(f"  Anomaly detection: {result['anomaly_detection']}")
                    print(f"  Predictive maintenance: {result['predictive_maintenance']}")
                sys.exit(0)
            else:
                print(f"FAILED: Training failed for {args.well_id}")
                for error in result["errors"]:
                    print(f"  Error: {error}")
                sys.exit(1)

        else:
            # Train all wells
            print(f"Training models for all active wells...")
            if args.dry_run:
                print("DRY RUN MODE - No training will be performed")

            summary = scheduler.train_all_wells(
                days=args.days,
                contamination=args.contamination,
                dry_run=args.dry_run
            )

            if args.dry_run:
                print(f"\nFound {summary['wells_count']} active wells:")
                for well in summary.get("wells", []):
                    print(f"  - {well}")
                sys.exit(0)

            print(f"\nTraining Summary:")
            print(f"  Total wells: {summary['wells_count']}")
            print(f"  Successful: {summary['successful_count']}")
            print(f"  Failed: {summary['failed_count']}")
            print(f"  Duration: {summary['duration_seconds']:.1f} seconds")

            if summary["successful_wells"]:
                print(f"\nSuccessful wells:")
                for well in summary["successful_wells"]:
                    print(f"  - {well}")

            if summary["failed_wells"]:
                print(f"\nFailed wells:")
                for well in summary["failed_wells"]:
                    print(f"  - {well}")

            sys.exit(0 if summary["success"] else 1)

    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
