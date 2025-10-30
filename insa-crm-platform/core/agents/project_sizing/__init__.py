"""
INSA Project Sizing Agent - Phase 11
AI-powered project dimensioning system for industrial automation

Automatically estimates:
- Hours by discipline (13 INSA disciplines)
- Personnel requirements (Junior/Senior/Specialist)
- Documents to generate (by phase and discipline)
- Timeline estimation (weeks per phase)
- Resource allocation
- Risk identification

Author: INSA Automation Corp
Date: October 19, 2025
"""

__version__ = "1.0.0"
__author__ = "INSA Automation Corp"

from project_classifier import ProjectClassifier
from discipline_estimator import DisciplineEstimator
from document_predictor import DocumentPredictor
from sizing_orchestrator import SizingOrchestrator

__all__ = [
    "ProjectClassifier",
    "DisciplineEstimator",
    "DocumentPredictor",
    "SizingOrchestrator"
]
