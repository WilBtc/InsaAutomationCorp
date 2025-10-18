#!/usr/bin/env python3
"""
INSA CRM Platform - Historical Project Ingestion
Ingests historical INSA projects into the RAG knowledge base

Usage:
    python3 ingest_historical_projects.py /var/lib/insa-crm/historical_projects/

Expected project structure:
    project_folder/
    ├── metadata.json       # Customer, industry, timeline, project type
    ├── requirements.txt    # Or .pdf - customer requirements
    ├── quote.json          # Pricing, BOM, labor hours, margin
    ├── bom.csv             # Parts list with quantities
    └── outcome.json        # Won/lost, actual vs estimated, lessons learned

Author: INSA Automation Corp
Date: October 18, 2025
"""

import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from agents.quote_generation.rag_knowledge_base import RAGKnowledgeBase


class ProjectIngester:
    """Ingests historical INSA projects into RAG knowledge base"""

    def __init__(self):
        self.rag = RAGKnowledgeBase()
        self.stats = {
            'total_projects': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

    def ingest_project(self, project_folder: Path) -> bool:
        """
        Ingest a single historical project

        Args:
            project_folder: Path to project folder

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n{'='*80}")
            print(f"Ingesting: {project_folder.name}")
            print(f"{'='*80}")

            # Load metadata
            metadata_path = project_folder / 'metadata.json'
            if not metadata_path.exists():
                raise FileNotFoundError(f"Missing metadata.json in {project_folder.name}")

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            print(f"✓ Customer: {metadata.get('customer_name', 'N/A')}")
            print(f"✓ Industry: {metadata.get('industry', 'N/A')}")
            print(f"✓ Date: {metadata.get('completion_date', 'N/A')}")

            # Load requirements
            requirements = self._load_requirements(project_folder)
            if requirements:
                print(f"✓ Requirements loaded ({len(requirements)} chars)")

            # Load quote
            quote_data = self._load_quote(project_folder)
            if quote_data:
                print(f"✓ Quote loaded (${quote_data.get('total_price', 0):,.2f})")

            # Load BOM
            bom = self._load_bom(project_folder)
            if bom:
                print(f"✓ BOM loaded ({len(bom)} parts)")

            # Load outcome
            outcome = self._load_outcome(project_folder)
            if outcome:
                status = outcome.get('status', 'unknown')
                print(f"✓ Outcome: {status}")

            # Create project document for RAG
            project_doc = self._create_project_document(
                metadata, requirements, quote_data, bom, outcome
            )

            # Index in RAG
            project_id = metadata.get('project_id', project_folder.name)
            self.rag.index_project(project_id, project_doc, metadata)

            print(f"\n✅ Successfully ingested: {project_id}")
            self.stats['successful'] += 1
            return True

        except Exception as e:
            print(f"\n❌ Failed to ingest {project_folder.name}: {str(e)}")
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'project': project_folder.name,
                'error': str(e)
            })
            return False

    def _load_requirements(self, project_folder: Path) -> str:
        """Load customer requirements from .txt or .pdf"""
        req_txt = project_folder / 'requirements.txt'
        if req_txt.exists():
            return req_txt.read_text()

        # TODO: Add PDF parsing if needed
        req_pdf = project_folder / 'requirements.pdf'
        if req_pdf.exists():
            return f"[PDF requirements file: {req_pdf.name}]"

        return ""

    def _load_quote(self, project_folder: Path) -> Dict[str, Any]:
        """Load quote data"""
        quote_path = project_folder / 'quote.json'
        if quote_path.exists():
            with open(quote_path, 'r') as f:
                return json.load(f)
        return {}

    def _load_bom(self, project_folder: Path) -> List[Dict[str, Any]]:
        """Load BOM from CSV"""
        bom_path = project_folder / 'bom.csv'
        if not bom_path.exists():
            return []

        bom = []
        with open(bom_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bom.append(dict(row))

        return bom

    def _load_outcome(self, project_folder: Path) -> Dict[str, Any]:
        """Load project outcome data"""
        outcome_path = project_folder / 'outcome.json'
        if outcome_path.exists():
            with open(outcome_path, 'r') as f:
                return json.load(f)
        return {}

    def _create_project_document(
        self,
        metadata: Dict[str, Any],
        requirements: str,
        quote: Dict[str, Any],
        bom: List[Dict[str, Any]],
        outcome: Dict[str, Any]
    ) -> str:
        """
        Create searchable project document for RAG

        This document will be embedded and used for similarity search
        when generating new quotes.
        """
        doc_parts = []

        # Project overview
        doc_parts.append(f"Project: {metadata.get('project_name', 'N/A')}")
        doc_parts.append(f"Customer: {metadata.get('customer_name', 'N/A')}")
        doc_parts.append(f"Industry: {metadata.get('industry', 'N/A')}")
        doc_parts.append(f"Type: {metadata.get('project_type', 'N/A')}")
        doc_parts.append("")

        # Requirements
        if requirements:
            doc_parts.append("REQUIREMENTS:")
            doc_parts.append(requirements)
            doc_parts.append("")

        # Solution summary
        if quote:
            doc_parts.append("SOLUTION:")
            doc_parts.append(f"Total Price: ${quote.get('total_price', 0):,.2f}")
            doc_parts.append(f"Labor Hours: {quote.get('labor_hours', 0)}")
            doc_parts.append(f"Margin: {quote.get('margin_percent', 0)}%")
            doc_parts.append("")

        # BOM
        if bom:
            doc_parts.append("BILL OF MATERIALS:")
            for item in bom:
                part = item.get('part_number', 'N/A')
                desc = item.get('description', 'N/A')
                qty = item.get('quantity', 1)
                doc_parts.append(f"  - {qty}x {part}: {desc}")
            doc_parts.append("")

        # Outcome & lessons learned
        if outcome:
            doc_parts.append("OUTCOME:")
            doc_parts.append(f"Status: {outcome.get('status', 'N/A')}")

            if outcome.get('lessons_learned'):
                doc_parts.append("Lessons Learned:")
                doc_parts.append(outcome['lessons_learned'])

            if outcome.get('actual_vs_estimated'):
                doc_parts.append("Actual vs Estimated:")
                doc_parts.append(json.dumps(outcome['actual_vs_estimated'], indent=2))

        return "\n".join(doc_parts)

    def ingest_all(self, projects_dir: Path) -> Dict[str, Any]:
        """
        Ingest all projects from directory

        Args:
            projects_dir: Path to directory containing project folders

        Returns:
            Statistics dictionary
        """
        if not projects_dir.exists():
            print(f"❌ Projects directory does not exist: {projects_dir}")
            return self.stats

        # Find all project folders
        project_folders = [d for d in projects_dir.iterdir() if d.is_dir()]

        if not project_folders:
            print(f"⚠️  No project folders found in {projects_dir}")
            return self.stats

        print(f"\n{'='*80}")
        print(f"INSA Historical Project Ingestion")
        print(f"{'='*80}")
        print(f"Found {len(project_folders)} project folders")
        print("")

        # Ingest each project
        for project_folder in project_folders:
            self.stats['total_projects'] += 1
            self.ingest_project(project_folder)

        # Print summary
        print(f"\n{'='*80}")
        print(f"INGESTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Projects: {self.stats['total_projects']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")

        if self.stats['errors']:
            print(f"\nErrors:")
            for error in self.stats['errors']:
                print(f"  - {error['project']}: {error['error']}")

        # Show RAG statistics
        rag_stats = self.rag.get_statistics()
        print(f"\n{'='*80}")
        print(f"RAG KNOWLEDGE BASE STATUS")
        print(f"{'='*80}")
        print(f"Total Projects Indexed: {rag_stats.get('total_projects', 0)}")
        print(f"Total Documents: {rag_stats.get('total_documents', 0)}")

        return self.stats


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 ingest_historical_projects.py <projects_directory>")
        print("")
        print("Example:")
        print("  python3 ingest_historical_projects.py /var/lib/insa-crm/historical_projects/")
        sys.exit(1)

    projects_dir = Path(sys.argv[1])

    ingester = ProjectIngester()
    stats = ingester.ingest_all(projects_dir)

    # Exit with error if any failed
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
