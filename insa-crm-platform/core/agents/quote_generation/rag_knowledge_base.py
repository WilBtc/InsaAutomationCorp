"""
RAG Knowledge Base for Quote Generation
Stores and retrieves past projects for similarity matching
"""

import chromadb
from chromadb.config import Settings
import json
import os
from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path
from datetime import datetime

from .config import config

logger = structlog.get_logger()


class RAGKnowledgeBase:
    """
    Vector database for storing and retrieving past projects
    Uses ChromaDB for efficient similarity search
    """

    def __init__(self):
        """Initialize ChromaDB client and collection"""
        # Create storage directory if it doesn't exist
        os.makedirs(config.chromadb_path, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=config.chromadb_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=config.chromadb_collection
            )
            logger.info("Connected to existing ChromaDB collection",
                       collection=config.chromadb_collection)
        except:
            self.collection = self.client.create_collection(
                name=config.chromadb_collection,
                metadata={"description": "INSA Automation Corp past projects for quote generation"}
            )
            logger.info("Created new ChromaDB collection",
                       collection=config.chromadb_collection)

    def index_project(
        self,
        project_code: str,
        project_data: Dict[str, Any],
        document_text: str
    ) -> None:
        """
        Index a project into the knowledge base

        Args:
            project_code: Unique project identifier (e.g., INSAGTEC-6598)
            project_data: Project metadata (dict)
            document_text: Full text description of the project
        """
        try:
            # Create metadata for filtering
            metadata = {
                "project_code": project_code,
                "project_name": project_data.get("project_name", ""),
                "customer": project_data.get("customer", ""),
                "project_type": project_data.get("project_type", ""),
                "status": project_data.get("status", ""),
                "indexed_date": datetime.utcnow().isoformat(),
                # Technical details
                "plc_vendor": project_data.get("plc_vendor", ""),
                "hmi_vendor": project_data.get("hmi_vendor", ""),
                "industry": project_data.get("industry", ""),
                # Financial (if available)
                "total_value": project_data.get("total_value", 0),
                "labor_hours": project_data.get("labor_hours", 0),
            }

            # Add to collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[project_code]
            )

            logger.info("Project indexed successfully",
                       project_code=project_code,
                       metadata_keys=list(metadata.keys()))

        except Exception as e:
            logger.error("Failed to index project",
                        project_code=project_code,
                        error=str(e))
            raise

    def find_similar_projects(
        self,
        requirement_text: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar past projects based on requirement text

        Args:
            requirement_text: Customer requirements/RFP text
            n_results: Number of similar projects to return
            filters: Optional metadata filters (e.g., {"industry": "Oil & Gas"})

        Returns:
            List of similar projects with metadata and similarity scores
        """
        try:
            # Build where clause for filtering
            where = filters if filters else None

            # Query the collection
            results = self.collection.query(
                query_texts=[requirement_text],
                n_results=n_results,
                where=where
            )

            # Format results
            similar_projects = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, project_id in enumerate(results['ids'][0]):
                    similar_projects.append({
                        "project_code": project_id,
                        "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "metadata": results['metadatas'][0][i],
                        "document": results['documents'][0][i]
                    })

            logger.info("Found similar projects",
                       count=len(similar_projects),
                       top_match=similar_projects[0]['project_code'] if similar_projects else None)

            return similar_projects

        except Exception as e:
            logger.error("Failed to find similar projects", error=str(e))
            return []

    def get_project(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific project by code

        Args:
            project_code: Project identifier

        Returns:
            Project data or None if not found
        """
        try:
            result = self.collection.get(ids=[project_code])

            if result and result['ids'] and len(result['ids']) > 0:
                return {
                    "project_code": result['ids'][0],
                    "metadata": result['metadatas'][0],
                    "document": result['documents'][0]
                }
            return None

        except Exception as e:
            logger.error("Failed to get project",
                        project_code=project_code,
                        error=str(e))
            return None

    def index_all_reference_projects(self) -> int:
        """
        Index all projects from the reference projects directory

        Returns:
            Number of projects indexed
        """
        indexed_count = 0
        projects_path = Path(config.reference_projects_path)

        if not projects_path.exists():
            logger.warning("Reference projects path does not exist",
                          path=config.reference_projects_path)
            return 0

        # Scan for project directories
        for project_dir in projects_path.iterdir():
            if not project_dir.is_dir():
                continue

            metadata_file = project_dir / "project_metadata.json"
            if not metadata_file.exists():
                logger.debug("No metadata file found", project=project_dir.name)
                continue

            try:
                # Load project metadata
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                project_code = metadata.get('project_info', {}).get('project_code', project_dir.name)

                # Build document text from metadata
                document_text = self._build_project_document(metadata)

                # Extract key fields for metadata
                project_data = {
                    "project_name": metadata.get('project_info', {}).get('project_name', ''),
                    "customer": metadata.get('project_info', {}).get('customer', ''),
                    "project_type": metadata.get('project_info', {}).get('project_type', ''),
                    "status": metadata.get('project_info', {}).get('status', ''),
                    "plc_vendor": metadata.get('technical_details', {}).get('control_system', {}).get('plc', ''),
                    "hmi_vendor": metadata.get('technical_details', {}).get('control_system', {}).get('hmi', ''),
                    "industry": "Oil & Gas" if "oil" in metadata.get('project_info', {}).get('project_type', '').lower() else "Industrial",
                }

                # Index the project
                self.index_project(project_code, project_data, document_text)
                indexed_count += 1

            except Exception as e:
                logger.error("Failed to index project",
                            project=project_dir.name,
                            error=str(e))

        logger.info("Finished indexing reference projects", count=indexed_count)
        return indexed_count

    def _build_project_document(self, metadata: Dict[str, Any]) -> str:
        """
        Build searchable document text from project metadata

        Args:
            metadata: Project metadata dictionary

        Returns:
            Formatted text document for RAG indexing
        """
        doc_parts = []

        # Project info
        project_info = metadata.get('project_info', {})
        doc_parts.append(f"Project: {project_info.get('project_name', '')}")
        doc_parts.append(f"Customer: {project_info.get('customer', '')}")
        doc_parts.append(f"Type: {project_info.get('project_type', '')}")

        # Technical details
        tech_details = metadata.get('technical_details', {})
        if 'control_system' in tech_details:
            cs = tech_details['control_system']
            doc_parts.append(f"PLC: {cs.get('plc', '')}")
            doc_parts.append(f"HMI: {cs.get('hmi', '')}")
            doc_parts.append(f"Communication: {cs.get('communication', '')}")
            doc_parts.append(f"I/O: {', '.join(cs.get('io_modules', []))}")

        if 'instrumentation' in tech_details:
            inst = tech_details['instrumentation']
            doc_parts.append(f"Instrumentation: {', '.join(inst.values())}")

        # Compliance standards
        standards = metadata.get('compliance_standards', {})
        if standards:
            doc_parts.append(f"Standards: {', '.join(f'{k}: {v}' for k, v in standards.items())}")

        # Project phases
        phases = metadata.get('project_phases', [])
        if phases:
            deliverables = []
            for phase in phases:
                deliverables.extend(phase.get('deliverables', []))
            doc_parts.append(f"Deliverables: {', '.join(deliverables)}")

        return "\n".join(doc_parts)

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            count = self.collection.count()
            return {
                "total_projects": count,
                "collection_name": config.chromadb_collection,
                "storage_path": config.chromadb_path
            }
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return {"error": str(e)}
