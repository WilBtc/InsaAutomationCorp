"""
Performance optimization service for ESP wells.

This module provides well performance scoring, efficiency optimization
recommendations, and comparative analysis against peer wells.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from app.core import get_logger, ValidationError, DatabaseError
from app.db import get_db_pool


logger = get_logger(__name__)


class PerformanceOptimizerService:
    """Service for optimizing ESP well performance."""

    def __init__(self):
        """Initialize performance optimizer service."""
        self._db_pool = None

        # Optimal operating ranges
        self.optimal_ranges = {
            "flow_rate": {"min": 2000, "max": 3500, "target": 2750},
            "pip": {"min": 200, "max": 300, "target": 250},
            "motor_current": {"min": 35, "max": 50, "target": 42.5},
            "motor_temp": {"min": 70, "max": 85, "target": 77.5},
            "vibration": {"min": 1.5, "max": 3.0, "target": 2.25},
            "vsd_frequency": {"min": 50, "max": 65, "target": 57.5},
            "gor": {"min": 100, "max": 200, "target": 150},
        }

        # Performance weights for scoring
        self.weights = {
            "flow_rate": 0.25,
            "efficiency": 0.20,
            "motor_health": 0.20,
            "vibration": 0.15,
            "stability": 0.10,
            "gor": 0.10,
        }

        logger.info("Performance optimizer service initialized")

    @property
    def db_pool(self):
        """Lazy-load database connection pool."""
        if self._db_pool is None:
            self._db_pool = get_db_pool()
        return self._db_pool

    def _fetch_well_data(
        self,
        well_id: str,
        hours: int = 24
    ) -> pd.DataFrame:
        """
        Fetch recent telemetry data for a well.

        Args:
            well_id: Well identifier
            hours: Number of hours of history

        Returns:
            DataFrame with telemetry data

        Raises:
            ValidationError: If insufficient data
            DatabaseError: If query fails
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            query = """
                SELECT
                    timestamp,
                    flow_rate,
                    pip,
                    motor_current,
                    motor_temp,
                    vibration,
                    vsd_frequency,
                    flow_variance,
                    torque,
                    gor
                FROM esp_telemetry
                WHERE well_id = %s
                AND timestamp >= %s
                ORDER BY timestamp ASC
            """

            result = self.db_pool.execute_query(
                query,
                params=(well_id, start_time),
                fetch=True,
                return_dict=True
            )

            if not result or len(result) < 10:
                raise ValidationError(
                    message=f"Insufficient data for analysis. Need at least 10 records, got {len(result) if result else 0}",
                    field="data",
                    details={"well_id": well_id, "hours": hours}
                )

            df = pd.DataFrame(result)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            logger.info(
                f"Fetched {len(df)} records for performance analysis",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "hours": hours,
                        "records": len(df),
                    }
                }
            )

            return df

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch well data",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Failed to fetch well data",
                operation="SELECT",
                details={"well_id": well_id}
            ) from e

    def _fetch_peer_wells(
        self,
        hours: int = 24
    ) -> List[str]:
        """
        Fetch list of peer wells for comparison.

        Args:
            hours: Number of hours to look back

        Returns:
            List of well IDs
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            query = """
                SELECT DISTINCT well_id
                FROM esp_telemetry
                WHERE timestamp >= %s
                ORDER BY well_id
            """

            result = self.db_pool.execute_query(
                query,
                params=(start_time,),
                fetch=True,
                return_dict=True
            )

            return [row["well_id"] for row in result] if result else []

        except Exception as e:
            logger.warning(
                "Failed to fetch peer wells",
                exc_info=e
            )
            return []

    def _calculate_well_score(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance score for a well.

        Args:
            df: DataFrame with telemetry data

        Returns:
            Dictionary with scores and sub-scores
        """
        try:
            # Calculate sub-scores (0-100 scale)
            flow_score = self._score_flow_performance(df)
            efficiency_score = self._score_efficiency(df)
            motor_health_score = self._score_motor_health(df)
            vibration_score = self._score_vibration(df)
            stability_score = self._score_stability(df)
            gor_score = self._score_gor(df)

            # Calculate weighted total score
            total_score = (
                flow_score * self.weights["flow_rate"] +
                efficiency_score * self.weights["efficiency"] +
                motor_health_score * self.weights["motor_health"] +
                vibration_score * self.weights["vibration"] +
                stability_score * self.weights["stability"] +
                gor_score * self.weights["gor"]
            )

            return {
                "total_score": round(total_score, 2),
                "sub_scores": {
                    "flow_performance": round(flow_score, 2),
                    "efficiency": round(efficiency_score, 2),
                    "motor_health": round(motor_health_score, 2),
                    "vibration": round(vibration_score, 2),
                    "stability": round(stability_score, 2),
                    "gor": round(gor_score, 2),
                },
                "grade": self._get_performance_grade(total_score),
            }

        except Exception as e:
            logger.error("Score calculation failed", exc_info=e)
            raise ValidationError(
                message="Failed to calculate performance score",
                details={"error": str(e)}
            ) from e

    def _score_flow_performance(self, df: pd.DataFrame) -> float:
        """Score flow rate performance (0-100)."""
        avg_flow = df["flow_rate"].mean()
        optimal = self.optimal_ranges["flow_rate"]

        if optimal["min"] <= avg_flow <= optimal["max"]:
            # Within optimal range - score based on proximity to target
            deviation = abs(avg_flow - optimal["target"]) / (optimal["max"] - optimal["min"])
            return 100 - (deviation * 20)  # Max 20 points penalty for deviation
        else:
            # Outside optimal range
            if avg_flow < optimal["min"]:
                ratio = avg_flow / optimal["min"]
            else:
                ratio = optimal["max"] / avg_flow
            return max(0, ratio * 70)  # Max 70 points when outside range

    def _score_efficiency(self, df: pd.DataFrame) -> float:
        """Score electrical efficiency (0-100)."""
        # Efficiency metric: flow rate per unit of motor current
        df["efficiency"] = df["flow_rate"] / (df["motor_current"] + 1e-6)
        avg_efficiency = df["efficiency"].mean()

        # Higher efficiency is better (typical range 50-70)
        normalized = (avg_efficiency - 50) / 20  # Normalize to 0-1
        return max(0, min(100, normalized * 100))

    def _score_motor_health(self, df: pd.DataFrame) -> float:
        """Score motor health based on temperature and current (0-100)."""
        avg_temp = df["motor_temp"].mean()
        avg_current = df["motor_current"].mean()

        # Temperature score
        temp_optimal = self.optimal_ranges["motor_temp"]
        if temp_optimal["min"] <= avg_temp <= temp_optimal["max"]:
            temp_score = 100 - abs(avg_temp - temp_optimal["target"]) / (temp_optimal["max"] - temp_optimal["min"]) * 20
        else:
            if avg_temp < temp_optimal["min"]:
                temp_score = 80
            else:
                temp_score = max(0, 100 - ((avg_temp - temp_optimal["max"]) / 10) * 20)

        # Current score
        current_optimal = self.optimal_ranges["motor_current"]
        if current_optimal["min"] <= avg_current <= current_optimal["max"]:
            current_score = 100 - abs(avg_current - current_optimal["target"]) / (current_optimal["max"] - current_optimal["min"]) * 20
        else:
            if avg_current < current_optimal["min"]:
                current_score = 80
            else:
                current_score = max(0, 100 - ((avg_current - current_optimal["max"]) / 10) * 20)

        return (temp_score + current_score) / 2

    def _score_vibration(self, df: pd.DataFrame) -> float:
        """Score vibration levels (0-100)."""
        avg_vibration = df["vibration"].mean()
        optimal = self.optimal_ranges["vibration"]

        if avg_vibration <= optimal["target"]:
            return 100
        elif avg_vibration <= optimal["max"]:
            excess = (avg_vibration - optimal["target"]) / (optimal["max"] - optimal["target"])
            return 100 - (excess * 30)
        else:
            excess = (avg_vibration - optimal["max"]) / optimal["max"]
            return max(0, 70 - (excess * 70))

    def _score_stability(self, df: pd.DataFrame) -> float:
        """Score operational stability based on variance (0-100)."""
        # Lower variance = higher stability
        flow_cv = df["flow_rate"].std() / (df["flow_rate"].mean() + 1e-6)
        temp_cv = df["motor_temp"].std() / (df["motor_temp"].mean() + 1e-6)
        vib_cv = df["vibration"].std() / (df["vibration"].mean() + 1e-6)

        avg_cv = (flow_cv + temp_cv + vib_cv) / 3

        # Typical CV range 0-0.2 (lower is better)
        stability = max(0, 100 - (avg_cv * 500))
        return min(100, stability)

    def _score_gor(self, df: pd.DataFrame) -> float:
        """Score gas-oil ratio (0-100)."""
        avg_gor = df["gor"].mean()
        optimal = self.optimal_ranges["gor"]

        if optimal["min"] <= avg_gor <= optimal["max"]:
            deviation = abs(avg_gor - optimal["target"]) / (optimal["max"] - optimal["min"])
            return 100 - (deviation * 20)
        else:
            if avg_gor < optimal["min"]:
                ratio = avg_gor / optimal["min"]
            else:
                ratio = optimal["max"] / avg_gor
            return max(0, ratio * 70)

    def _get_performance_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_optimization_recommendations(
        self,
        df: pd.DataFrame,
        scores: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations based on performance analysis.

        Args:
            df: DataFrame with telemetry data
            scores: Performance scores

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Analyze flow rate
        avg_flow = df["flow_rate"].mean()
        optimal_flow = self.optimal_ranges["flow_rate"]
        if avg_flow < optimal_flow["min"]:
            recommendations.append({
                "category": "flow_optimization",
                "priority": "high",
                "title": "Increase Flow Rate",
                "description": f"Flow rate ({avg_flow:.0f} bpd) is below optimal range ({optimal_flow['min']}-{optimal_flow['max']} bpd)",
                "action": f"Increase VSD frequency to target {optimal_flow['target']:.0f} bpd",
                "estimated_impact": "15-20% production increase",
            })
        elif avg_flow > optimal_flow["max"]:
            recommendations.append({
                "category": "flow_optimization",
                "priority": "medium",
                "title": "Reduce Flow Rate",
                "description": f"Flow rate ({avg_flow:.0f} bpd) exceeds optimal range, risking equipment wear",
                "action": f"Decrease VSD frequency to target {optimal_flow['target']:.0f} bpd",
                "estimated_impact": "Improved equipment longevity",
            })

        # Analyze motor temperature
        avg_temp = df["motor_temp"].mean()
        optimal_temp = self.optimal_ranges["motor_temp"]
        if avg_temp > optimal_temp["max"]:
            recommendations.append({
                "category": "motor_health",
                "priority": "high",
                "title": "Reduce Motor Temperature",
                "description": f"Motor temperature ({avg_temp:.1f}°C) exceeds safe limit ({optimal_temp['max']}°C)",
                "action": "Reduce motor load or improve cooling",
                "estimated_impact": "Prevent motor failure",
            })

        # Analyze vibration
        avg_vibration = df["vibration"].mean()
        optimal_vibration = self.optimal_ranges["vibration"]
        if avg_vibration > optimal_vibration["max"]:
            recommendations.append({
                "category": "vibration",
                "priority": "high",
                "title": "Address High Vibration",
                "description": f"Vibration ({avg_vibration:.2f} mm/s) exceeds safe limit ({optimal_vibration['max']} mm/s)",
                "action": "Inspect pump for wear, check alignment, or adjust frequency",
                "estimated_impact": "Prevent equipment damage",
            })

        # Analyze efficiency
        if scores["sub_scores"]["efficiency"] < 70:
            recommendations.append({
                "category": "efficiency",
                "priority": "medium",
                "title": "Improve Electrical Efficiency",
                "description": "Well is operating below optimal efficiency",
                "action": "Optimize VSD frequency and check for pump wear",
                "estimated_impact": "5-10% energy cost reduction",
            })

        # Analyze stability
        if scores["sub_scores"]["stability"] < 70:
            recommendations.append({
                "category": "stability",
                "priority": "medium",
                "title": "Improve Operational Stability",
                "description": "High variability in operating parameters detected",
                "action": "Check for gas slugging, inspect valves, or adjust control settings",
                "estimated_impact": "More consistent production",
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])

        return recommendations

    def _find_optimal_operating_point(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Find optimal operating point based on historical data.

        Args:
            df: DataFrame with telemetry data

        Returns:
            Dictionary with optimal operating parameters
        """
        try:
            # Calculate efficiency for each data point
            df["efficiency"] = df["flow_rate"] / (df["motor_current"] + 1e-6)

            # Find top 10% most efficient operating points
            top_efficiency_threshold = df["efficiency"].quantile(0.9)
            top_efficient = df[df["efficiency"] >= top_efficiency_threshold]

            # Calculate optimal setpoints as median of top efficient points
            optimal_point = {
                "vsd_frequency": float(top_efficient["vsd_frequency"].median()),
                "expected_flow_rate": float(top_efficient["flow_rate"].median()),
                "expected_motor_current": float(top_efficient["motor_current"].median()),
                "expected_motor_temp": float(top_efficient["motor_temp"].median()),
                "expected_efficiency": float(top_efficient["efficiency"].median()),
            }

            return optimal_point

        except Exception as e:
            logger.warning("Failed to find optimal operating point", exc_info=e)
            # Return default optimal point
            return {
                "vsd_frequency": self.optimal_ranges["vsd_frequency"]["target"],
                "expected_flow_rate": self.optimal_ranges["flow_rate"]["target"],
                "expected_motor_current": self.optimal_ranges["motor_current"]["target"],
                "expected_motor_temp": self.optimal_ranges["motor_temp"]["target"],
                "expected_efficiency": 60.0,
            }

    def analyze_well_performance(
        self,
        well_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Perform comprehensive performance analysis for a well.

        Args:
            well_id: Well identifier
            hours: Number of hours of data to analyze

        Returns:
            Dictionary with performance analysis results

        Raises:
            ValidationError: If insufficient data
            DatabaseError: If analysis fails
        """
        try:
            logger.info(
                f"Starting performance analysis for well {well_id}",
                extra={"extra_fields": {"well_id": well_id, "hours": hours}}
            )

            # Fetch well data
            df = self._fetch_well_data(well_id, hours)

            # Calculate performance scores
            scores = self._calculate_well_score(df)

            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(df, scores)

            # Find optimal operating point
            optimal_point = self._find_optimal_operating_point(df)

            # Calculate current averages
            current_averages = {
                "flow_rate": float(df["flow_rate"].mean()),
                "pip": float(df["pip"].mean()),
                "motor_current": float(df["motor_current"].mean()),
                "motor_temp": float(df["motor_temp"].mean()),
                "vibration": float(df["vibration"].mean()),
                "vsd_frequency": float(df["vsd_frequency"].mean()),
                "gor": float(df["gor"].mean()),
            }

            # Determine trend
            if len(df) >= 10:
                first_half_score = self._calculate_well_score(df.iloc[:len(df)//2])["total_score"]
                second_half_score = self._calculate_well_score(df.iloc[len(df)//2:])["total_score"]
                score_change = second_half_score - first_half_score

                if score_change > 5:
                    trend = "improving"
                elif score_change < -5:
                    trend = "degrading"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            result = {
                "well_id": well_id,
                "analysis_period_hours": hours,
                "data_points_analyzed": len(df),
                "performance_score": scores["total_score"],
                "performance_grade": scores["grade"],
                "sub_scores": scores["sub_scores"],
                "trend": trend,
                "current_operating_point": current_averages,
                "optimal_operating_point": optimal_point,
                "optimization_recommendations": recommendations,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Performance analysis complete for well {well_id}",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "score": scores["total_score"],
                        "grade": scores["grade"],
                        "recommendations": len(recommendations),
                    }
                }
            )

            return result

        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(
                "Performance analysis failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Performance analysis failed",
                operation="ANALYZE",
                details={"well_id": well_id}
            ) from e

    def compare_to_peers(
        self,
        well_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Compare well performance to peer wells.

        Args:
            well_id: Well identifier
            hours: Number of hours of data

        Returns:
            Dictionary with peer comparison results
        """
        try:
            # Analyze target well
            target_analysis = self.analyze_well_performance(well_id, hours)
            target_score = target_analysis["performance_score"]

            # Get peer wells
            peer_wells = self._fetch_peer_wells(hours)
            peer_wells = [w for w in peer_wells if w != well_id]

            if not peer_wells:
                return {
                    "well_id": well_id,
                    "peer_comparison": "No peer wells available for comparison",
                    "target_score": target_score,
                }

            # Analyze peer wells
            peer_scores = []
            for peer_id in peer_wells:
                try:
                    peer_analysis = self.analyze_well_performance(peer_id, hours)
                    peer_scores.append({
                        "well_id": peer_id,
                        "score": peer_analysis["performance_score"],
                    })
                except Exception as e:
                    logger.warning(f"Failed to analyze peer well {peer_id}", exc_info=e)
                    continue

            if not peer_scores:
                return {
                    "well_id": well_id,
                    "peer_comparison": "Failed to analyze peer wells",
                    "target_score": target_score,
                }

            # Calculate statistics
            peer_score_values = [p["score"] for p in peer_scores]
            peer_avg = np.mean(peer_score_values)
            peer_std = np.std(peer_score_values)
            peer_median = np.median(peer_score_values)

            # Calculate percentile
            percentile = stats.percentileofscore(peer_score_values, target_score)

            # Determine performance category
            if target_score >= peer_avg + peer_std:
                category = "top_performer"
            elif target_score >= peer_avg:
                category = "above_average"
            elif target_score >= peer_avg - peer_std:
                category = "average"
            else:
                category = "below_average"

            result = {
                "well_id": well_id,
                "target_score": target_score,
                "peer_statistics": {
                    "peer_count": len(peer_scores),
                    "average_score": round(peer_avg, 2),
                    "median_score": round(peer_median, 2),
                    "std_deviation": round(peer_std, 2),
                    "min_score": round(min(peer_score_values), 2),
                    "max_score": round(max(peer_score_values), 2),
                },
                "comparison": {
                    "percentile": round(percentile, 1),
                    "performance_category": category,
                    "score_vs_average": round(target_score - peer_avg, 2),
                },
                "peer_wells": peer_scores,
            }

            logger.info(
                f"Peer comparison complete for well {well_id}",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "percentile": percentile,
                        "category": category,
                    }
                }
            )

            return result

        except Exception as e:
            logger.error(
                "Peer comparison failed",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            raise DatabaseError(
                message="Peer comparison failed",
                operation="COMPARE",
                details={"well_id": well_id}
            ) from e
