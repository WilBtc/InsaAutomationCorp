"""
Machine Learning services for the Alkhorayef ESP IoT Platform.

This package provides ML/AI analytics capabilities including:
- Anomaly detection using Isolation Forest
- Predictive maintenance with time-series forecasting
- Performance optimization recommendations
- Model storage and versioning
"""

from .model_storage import ModelStorage
from .anomaly_detection import AnomalyDetectionService
from .predictive_maintenance import PredictiveMaintenanceService
from .performance_optimizer import PerformanceOptimizerService

__all__ = [
    "ModelStorage",
    "AnomalyDetectionService",
    "PredictiveMaintenanceService",
    "PerformanceOptimizerService",
]

__version__ = "1.0.0"
