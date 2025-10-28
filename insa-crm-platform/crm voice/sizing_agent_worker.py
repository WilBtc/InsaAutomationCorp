#!/usr/bin/env python3
"""
Sizing Agent Worker - Phase 11 Week 2 + Phase 12 Week 2 Metrics
Processes equipment dimensioning tasks via message bus

Capabilities:
- Dimensions separators, pumps, tanks, valves, etc.
- Accepts handoffs from orchestrator or other agents
- Hands off to CRM for quote generation
- Participates in consensus (multiple sizing estimates)
- Prometheus metrics collection (Phase 12 Week 2)
"""
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from agent_worker import AgentWorker

# Phase 12 Week 2: Prometheus metrics
from prometheus_metrics import (
    metrics,
    track_request_metrics,
    track_message_processing
)

# Add sizing agent path
sys.path.insert(0, str(Path.home() / "insa-crm-platform/core/agents/project_sizing"))

logger = logging.getLogger(__name__)


class SizingAgentWorker(AgentWorker):
    """
    Sizing Agent Worker - Equipment Dimensioning Expert

    Listens to message bus for sizing tasks and processes them
    using the existing sizing orchestrator logic.
    """

    def __init__(self):
        """Initialize Sizing Agent Worker"""
        super().__init__(
            agent_id='sizing_agent',
            agent_type='sizing'
        )

        # Load sizing orchestrator
        try:
            from sizing_orchestrator import SizingOrchestrator
            self.sizing_orchestrator = SizingOrchestrator()
            logger.info("✅ Sizing orchestrator loaded")
        except ImportError as e:
            logger.error(f"❌ Failed to load sizing orchestrator: {e}")
            self.sizing_orchestrator = None

        # Phase 12 Week 2: Initialize worker health metrics
        metrics.update_worker_health('sizing_agent', 'sizing', True)
        metrics.update_active_requests('sizing_agent', 0)
        metrics.update_worker_queue('sizing_agent', 0)

        logger.info("SizingAgentWorker initialized")

    def get_additional_topics(self) -> list:
        """Subscribe to additional topics"""
        return [
            'equipment_request',  # Direct equipment dimensioning requests
            'sizing_update',      # Updates to sizing parameters
            'bom_request'         # Bill of materials requests
        ]

    @track_request_metrics('sizing_agent')
    def process_task(self, task: str, session_id: str,
                    dependencies_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sizing task from orchestrator

        Args:
            task: Task description (e.g., "Dimension 3-phase separator for 10,000 BPD")
            session_id: Session identifier
            dependencies_results: Results from dependent agents (usually empty for sizing)

        Returns:
            Dictionary with sizing results
        """
        logger.info(f"🔧 Sizing agent processing: {task[:80]}...")

        # Phase 12 Week 2: Track active request
        metrics.update_active_requests('sizing_agent', 1)

        if not self.sizing_orchestrator:
            metrics.update_active_requests('sizing_agent', 0)
            return {
                'error': 'Sizing orchestrator not available',
                'status': 'failed'
            }

        try:
            # Extract parameters from task description
            params = self._parse_task(task, dependencies_results)

            # Call sizing orchestrator
            result = self._dimension_equipment(params)

            # Check if we should auto-handoff to CRM
            if self._should_handoff_to_crm(task, result):
                self._handoff_to_crm(result, session_id)

            return {
                'status': 'success',
                'equipment_type': result.get('equipment_type'),
                'specifications': result.get('specifications'),
                'dimensions': result.get('dimensions'),
                'bom': result.get('bom', []),
                'estimated_cost': result.get('estimated_cost'),
                'notes': result.get('notes'),
                'session_id': session_id
            }

        except Exception as e:
            logger.error(f"❌ Sizing task failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'status': 'failed',
                'session_id': session_id
            }
        finally:
            # Phase 12 Week 2: Clear active request
            metrics.update_active_requests('sizing_agent', 0)

    def _parse_task(self, task: str, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse task description to extract sizing parameters

        Args:
            task: Natural language task description
            dependencies: Results from other agents (may contain parameters)

        Returns:
            Dictionary of sizing parameters
        """
        params = {
            'task_description': task,
            'dependencies': dependencies
        }

        task_lower = task.lower()

        # Extract equipment type
        equipment_keywords = {
            'separator': ['separador', 'separator', 'separación'],
            'pump': ['bomba', 'pump', 'bombeo'],
            'tank': ['tanque', 'tank', 'almacenamiento'],
            'valve': ['válvula', 'valve', 'control valve'],
            'compressor': ['compresor', 'compressor']
        }

        for equipment, keywords in equipment_keywords.items():
            if any(kw in task_lower for kw in keywords):
                params['equipment_type'] = equipment
                break

        # Extract capacity (BPD, m³/h, etc.)
        import re

        # Match patterns like "10000 BPD", "10,000 bpd", "100 m³/h"
        capacity_patterns = [
            r'(\d+[\d,]*)\s*(bpd|barril|barrel)',
            r'(\d+[\d,]*)\s*m[³3]',
            r'(\d+[\d,]*)\s*(gpm|gallon)',
            r'(\d+[\d,]*)\s*litro'
        ]

        for pattern in capacity_patterns:
            match = re.search(pattern, task_lower)
            if match:
                capacity_str = match.group(1).replace(',', '')
                params['capacity'] = float(capacity_str)
                params['capacity_unit'] = match.group(2) if match.lastindex > 1 else 'bpd'
                break

        # Extract pressure
        pressure_patterns = [
            r'(\d+)\s*(psi|bar|kpa|psig)',
        ]

        for pattern in pressure_patterns:
            match = re.search(pattern, task_lower)
            if match:
                params['pressure'] = float(match.group(1))
                params['pressure_unit'] = match.group(2)
                break

        # Extract temperature
        temp_patterns = [
            r'(\d+)\s*°?\s*([fc])',
            r'temperatura[:\s]+(\d+)',
        ]

        for pattern in temp_patterns:
            match = re.search(pattern, task_lower)
            if match:
                params['temperature'] = float(match.group(1))
                params['temperature_unit'] = match.group(2).upper() if match.lastindex > 1 else 'F'
                break

        # Check dependencies for additional parameters
        if dependencies:
            # CRM agent might have provided customer requirements
            if 'customer_requirements' in dependencies:
                params.update(dependencies['customer_requirements'])

            # Platform agent might have provided site conditions
            if 'site_conditions' in dependencies:
                params.update(dependencies['site_conditions'])

        logger.debug(f"Parsed parameters: {params}")
        return params

    def _dimension_equipment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dimension equipment using sizing orchestrator

        Args:
            params: Sizing parameters

        Returns:
            Sizing results with specifications
        """
        equipment_type = params.get('equipment_type', 'separator')

        # Build query for sizing orchestrator
        query_parts = []

        if equipment_type:
            query_parts.append(f"Dimensionar {equipment_type}")

        if params.get('capacity'):
            unit = params.get('capacity_unit', 'BPD')
            query_parts.append(f"{params['capacity']} {unit}")

        if params.get('pressure'):
            unit = params.get('pressure_unit', 'PSI')
            query_parts.append(f"{params['pressure']} {unit}")

        if params.get('temperature'):
            unit = params.get('temperature_unit', 'F')
            query_parts.append(f"{params['temperature']}°{unit}")

        query = " ".join(query_parts) if query_parts else params.get('task_description', '')

        logger.info(f"Sizing query: {query}")

        # Call sizing orchestrator
        # Note: This is a simplified version - real implementation would handle
        # full conversational flow from sizing_orchestrator
        result = {
            'equipment_type': equipment_type,
            'query': query,
            'specifications': {
                'capacity': params.get('capacity'),
                'pressure': params.get('pressure'),
                'temperature': params.get('temperature')
            },
            'dimensions': self._calculate_dimensions(equipment_type, params),
            'bom': self._generate_bom(equipment_type, params),
            'estimated_cost': self._estimate_cost(equipment_type, params),
            'notes': f"Dimensioned {equipment_type} based on provided parameters"
        }

        return result

    def _calculate_dimensions(self, equipment_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate equipment dimensions

        This is a simplified implementation - real version would use
        proper engineering calculations from sizing_orchestrator.
        """
        capacity = params.get('capacity', 10000)  # BPD
        pressure = params.get('pressure', 500)    # PSI

        if equipment_type == 'separator':
            # Simplified separator sizing
            # Real calculation considers: L/D ratio, retention time, gas capacity, etc.
            if pressure < 250:
                diameter = 54  # inches
                length = 20    # feet
            elif pressure < 750:
                diameter = 60
                length = 22
            else:
                diameter = 66
                length = 24

            return {
                'type': 'horizontal',
                'diameter': diameter,
                'diameter_unit': 'inches',
                'length': length,
                'length_unit': 'feet',
                'thickness': 0.75,
                'thickness_unit': 'inches',
                'volume': (3.14159 * (diameter/24)**2 * length) / 4,
                'volume_unit': 'ft³'
            }

        elif equipment_type == 'pump':
            # Simplified pump sizing
            flow = capacity / 24  # Convert BPD to GPH
            head = pressure * 2.31  # Convert PSI to feet of head

            return {
                'type': 'centrifugal',
                'flow': flow,
                'flow_unit': 'GPH',
                'head': head,
                'head_unit': 'feet',
                'power': (flow * head) / 3960,  # HP
                'power_unit': 'HP'
            }

        elif equipment_type == 'tank':
            # Simplified tank sizing
            volume = capacity * 1.2  # 120% of daily capacity
            diameter = (volume / 10) ** 0.5 * 12  # Rough estimate

            return {
                'type': 'vertical',
                'diameter': diameter,
                'diameter_unit': 'feet',
                'height': 20,
                'height_unit': 'feet',
                'volume': volume,
                'volume_unit': 'barrels'
            }

        return {}

    def _generate_bom(self, equipment_type: str, params: Dict[str, Any]) -> list:
        """
        Generate Bill of Materials

        Returns list of required components.
        """
        bom = []

        if equipment_type == 'separator':
            bom = [
                {'item': '3-Phase Separator Vessel', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Level Control Valve', 'quantity': 2, 'unit': 'EA'},
                {'item': 'Pressure Safety Valve', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Level Transmitter', 'quantity': 3, 'unit': 'EA'},
                {'item': 'Pressure Transmitter', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Temperature Transmitter', 'quantity': 1, 'unit': 'EA'},
            ]

        elif equipment_type == 'pump':
            bom = [
                {'item': 'Centrifugal Pump', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Electric Motor', 'quantity': 1, 'unit': 'EA'},
                {'item': 'VFD (Variable Frequency Drive)', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Pressure Transmitter', 'quantity': 2, 'unit': 'EA'},
                {'item': 'Flow Transmitter', 'quantity': 1, 'unit': 'EA'},
            ]

        elif equipment_type == 'tank':
            bom = [
                {'item': 'Storage Tank', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Level Transmitter', 'quantity': 1, 'unit': 'EA'},
                {'item': 'High Level Alarm', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Inlet Nozzle', 'quantity': 1, 'unit': 'EA'},
                {'item': 'Outlet Nozzle', 'quantity': 1, 'unit': 'EA'},
            ]

        return bom

    def _estimate_cost(self, equipment_type: str, params: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate equipment cost

        This is a rough estimate - real pricing comes from CRM agent
        using vendor catalogs.
        """
        capacity = params.get('capacity', 10000)
        pressure = params.get('pressure', 500)

        if equipment_type == 'separator':
            base_cost = 50000  # USD
            capacity_factor = (capacity / 10000) ** 0.6
            pressure_factor = 1 + (pressure - 150) / 1000
            equipment_cost = base_cost * capacity_factor * pressure_factor
            installation = equipment_cost * 0.3
            instrumentation = 25000

        elif equipment_type == 'pump':
            base_cost = 15000
            capacity_factor = (capacity / 10000) ** 0.6
            equipment_cost = base_cost * capacity_factor
            installation = equipment_cost * 0.2
            instrumentation = 5000

        elif equipment_type == 'tank':
            base_cost = 30000
            capacity_factor = (capacity / 10000) ** 0.6
            equipment_cost = base_cost * capacity_factor
            installation = equipment_cost * 0.25
            instrumentation = 8000

        else:
            return {'total': 0}

        return {
            'equipment': round(equipment_cost, 2),
            'installation': round(installation, 2),
            'instrumentation': round(instrumentation, 2),
            'total': round(equipment_cost + installation + instrumentation, 2),
            'currency': 'USD'
        }

    def _should_handoff_to_crm(self, task: str, result: Dict[str, Any]) -> bool:
        """
        Determine if we should auto-handoff to CRM for quoting

        Returns True if task mentions quote/pricing and sizing succeeded
        """
        task_lower = task.lower()
        quote_keywords = ['cotiza', 'quote', 'precio', 'price', 'costo', 'cost']

        has_quote_keyword = any(kw in task_lower for kw in quote_keywords)
        sizing_successful = result.get('status') == 'success'

        return has_quote_keyword and sizing_successful

    def _handoff_to_crm(self, sizing_result: Dict[str, Any], session_id: str):
        """
        Handoff to CRM agent for quote generation

        Args:
            sizing_result: Complete sizing specifications
            session_id: Session identifier
        """
        logger.info("🤝 Auto-handing off to CRM agent for quote generation")

        self.handoff_to_agent(
            to_agent='crm_agent',
            task='Generate quote for dimensioned equipment',
            context={
                'equipment_type': sizing_result.get('equipment_type'),
                'specifications': sizing_result.get('specifications'),
                'dimensions': sizing_result.get('dimensions'),
                'bom': sizing_result.get('bom'),
                'estimated_cost': sizing_result.get('estimated_cost'),
                'session_id': session_id
            },
            reason='Sizing complete, customer requested quote'
        )

    def process_handoff(self, task: str, context: Dict[str, Any], from_agent: str) -> Dict[str, Any]:
        """
        Handle handoff from another agent

        Args:
            task: Task description
            context: Context from previous agent
            from_agent: Agent that sent handoff

        Returns:
            Sizing results
        """
        logger.info(f"🤝 Processing handoff from {from_agent}")

        # Extract parameters from context
        params = context.copy()
        params['task_description'] = task

        # Dimension equipment
        result = self._dimension_equipment(params)

        # Check if we should handoff to CRM
        session_id = context.get('session_id', 'default')
        if self._should_handoff_to_crm(task, result):
            self._handoff_to_crm(result, session_id)

        return result

    def can_handle_handoff(self, task: str, context: Dict[str, Any]) -> bool:
        """
        Check if we can handle this handoff

        Accept if task involves dimensioning/sizing
        """
        task_lower = task.lower()
        sizing_keywords = [
            'dimensiona', 'dimension', 'size', 'sizing',
            'calcula', 'calculate', 'estima', 'estimate',
            'diseña', 'design'
        ]

        return any(kw in task_lower for kw in sizing_keywords)

    def process_consensus(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Participate in consensus - provide sizing estimate

        Args:
            task: Consensus task
            context: Context

        Returns:
            Our sizing estimate
        """
        logger.info("🗳️ Participating in consensus")

        result = self.process_task(task, context.get('session_id', 'default'), {})

        # Return just the estimated cost for consensus
        return {
            'estimate': result.get('estimated_cost', {}).get('total', 0),
            'confidence': 0.8  # 80% confidence in rough estimate
        }


# Global instance
_sizing_worker = None


def get_sizing_worker() -> SizingAgentWorker:
    """Get or create global sizing worker instance"""
    global _sizing_worker
    if _sizing_worker is None:
        _sizing_worker = SizingAgentWorker()
    return _sizing_worker


if __name__ == '__main__':
    # Test sizing worker
    logging.basicConfig(level=logging.INFO)

    worker = get_sizing_worker()
    worker.start()

    print(f"\n=== Sizing Agent Worker Started ===")
    print(f"Agent ID: {worker.agent_id}")
    print(f"Status: {worker.get_status()}")
    print(f"\nListening to message bus...")
    print(f"Try sending a task via orchestrator!")

    # Keep running
    try:
        import time
        while True:
            time.sleep(10)
            status = worker.get_status()
            print(f"\rTasks processed: {status['tasks_processed']}, Failed: {status['tasks_failed']}", end='')
    except KeyboardInterrupt:
        print(f"\n\nStopping worker...")
        worker.stop()
        print(f"Final status: {worker.get_status()}")
