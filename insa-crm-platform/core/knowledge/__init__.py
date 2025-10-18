"""
Industrial Instrumentation RAG System
Knowledge-augmented CRM agents for industrial automation

Provides AI agents with access to 794 pages of industrial instrumentation
knowledge from "Instrumentación Industrial" by Antonio Creus Solé.

Author: INSA Automation Corp
Date: October 18, 2025
"""

from .instrumentation_rag import (
    InstrumentationRAG,
    DocumentChunk,
    instrumentation_rag,
    get_sensor_recommendation,
    get_control_strategy,
    get_calibration_procedure
)

__all__ = [
    'InstrumentationRAG',
    'DocumentChunk',
    'instrumentation_rag',
    'get_sensor_recommendation',
    'get_control_strategy',
    'get_calibration_procedure'
]

__version__ = '1.0.0'
__author__ = 'INSA Automation Corp'
