#!/usr/bin/env python3
"""
INSA Project Sizing Agent - FastAPI REST API
Provides HTTP endpoints for autonomous project sizing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
from pathlib import Path
import json
from datetime import datetime

from sizing_orchestrator import SizingOrchestrator

app = FastAPI(
    title="INSA Project Sizing API",
    description="Autonomous AI-powered project dimensioning for industrial automation",
    version="1.0.0"
)

# CORS middleware for web UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = SizingOrchestrator()

# Request/Response Models
class ProjectSizingRequest(BaseModel):
    """Request model for project sizing"""
    project_description: str = Field(..., description="Natural language project description")
    customer_name: str = Field(..., description="Customer name")
    country: str = Field(default="colombia", description="Country: colombia, ecuador, usa")
    project_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameters (io_count, etc)")
    customer_requirements: Optional[List[str]] = Field(default=None, description="Optional customer requirements")
    save_results: bool = Field(default=True, description="Save results to disk")

class ProjectSizingResponse(BaseModel):
    """Response model for project sizing"""
    sizing_id: str
    timestamp: str
    generation_time_seconds: float
    classification: Dict[str, Any]
    estimation: Dict[str, Any]
    documents: Dict[str, Any]
    assessment: Dict[str, Any]
    recommended_actions: List[str]

class SizingListItem(BaseModel):
    """List item for sizing history"""
    sizing_id: str
    timestamp: str
    customer_name: str
    project_type: str
    complexity: str
    total_hours: float
    total_cost: float
    confidence: float
    ready_for_quotation: bool

# API Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "INSA Project Sizing API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "/size": "POST - Size a new project",
            "/sizings": "GET - List recent sizings",
            "/sizings/{sizing_id}": "GET - Get sizing details",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from config import SIZING_RESULTS_DIR
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator": "initialized",
        "storage": str(SIZING_RESULTS_DIR)
    }

@app.post("/size", response_model=ProjectSizingResponse)
async def size_project(request: ProjectSizingRequest):
    """
    Size a project based on description and parameters

    Returns complete project sizing with:
    - Classification (type, complexity, disciplines)
    - Effort estimation (hours, cost, duration)
    - Document requirements
    - Risk assessment
    - Recommended actions
    """
    try:
        # Size the project
        sizing = orchestrator.size_project(
            project_description=request.project_description,
            customer_name=request.customer_name,
            country=request.country,
            project_parameters=request.project_parameters or {},
            customer_requirements=request.customer_requirements or [],
            save_results=request.save_results
        )

        return ProjectSizingResponse(**sizing)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sizing failed: {str(e)}")

@app.get("/sizings", response_model=List[SizingListItem])
async def list_sizings(limit: int = 20):
    """
    List recent project sizings

    Parameters:
    - limit: Maximum number of results (default 20)
    """
    try:
        from config import SIZING_RESULTS_DIR
        # Get all sizing files
        sizing_files = sorted(
            SIZING_RESULTS_DIR.glob("SZ-*_project_sizing.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        # Parse each sizing
        sizings = []
        for file in sizing_files:
            with open(file, 'r') as f:
                data = json.load(f)

                sizings.append(SizingListItem(
                    sizing_id=data['sizing_id'],
                    timestamp=data['timestamp'],
                    customer_name=data['input']['customer_name'],
                    project_type=data['classification']['project_type'],
                    complexity=data['classification']['complexity'],
                    total_hours=data['estimation']['total_hours'],
                    total_cost=data['estimation']['total_cost'],
                    confidence=data['assessment']['overall_confidence'],
                    ready_for_quotation=data['assessment']['ready_for_quotation']
                ))

        return sizings

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sizings: {str(e)}")

@app.get("/sizings/{sizing_id}")
async def get_sizing(sizing_id: str):
    """
    Get detailed sizing results by ID

    Parameters:
    - sizing_id: Sizing ID (e.g., SZ-20251019203904)
    """
    try:
        from config import SIZING_RESULTS_DIR
        # Find sizing file
        sizing_file = SIZING_RESULTS_DIR / f"{sizing_id}_project_sizing.json"

        if not sizing_file.exists():
            raise HTTPException(status_code=404, detail=f"Sizing {sizing_id} not found")

        # Load and return
        with open(sizing_file, 'r') as f:
            sizing = json.load(f)

        return sizing

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sizing: {str(e)}")

@app.delete("/sizings/{sizing_id}")
async def delete_sizing(sizing_id: str):
    """
    Delete a sizing by ID

    Parameters:
    - sizing_id: Sizing ID (e.g., SZ-20251019203904)
    """
    try:
        from config import SIZING_RESULTS_DIR
        # Find and delete files
        json_file = SIZING_RESULTS_DIR / f"{sizing_id}_project_sizing.json"
        summary_file = SIZING_RESULTS_DIR / f"{sizing_id}_summary.txt"

        deleted = []
        if json_file.exists():
            json_file.unlink()
            deleted.append("json")
        if summary_file.exists():
            summary_file.unlink()
            deleted.append("summary")

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Sizing {sizing_id} not found")

        return {
            "status": "deleted",
            "sizing_id": sizing_id,
            "files_deleted": deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete sizing: {str(e)}")

# Example usage documentation
@app.get("/examples")
async def get_examples():
    """Get API usage examples"""
    # Get API base URL from environment or use localhost
    api_url = os.getenv("SIZING_API_URL", "http://localhost:8008")

    return {
        "curl_examples": {
            "simple_sizing": {
                "description": "Size a simple project",
                "command": f"""curl -X POST {api_url}/size \\
  -H "Content-Type: application/json" \\
  -d '{{
    "project_description": "Three-phase separator with PLC control and HMI",
    "customer_name": "Deilim Colombia",
    "country": "colombia"
  }}'"""
            },
            "detailed_sizing": {
                "description": "Size with parameters",
                "command": f"""curl -X POST {api_url}/size \\
  -H "Content-Type: application/json" \\
  -d '{{
    "project_description": "Separator trifásico con control PLC Allen-Bradley",
    "customer_name": "Petroecuador",
    "country": "ecuador",
    "project_parameters": {{
      "io_count": 85,
      "instrument_count": 25,
      "panel_count": 2,
      "scada_screens": 12,
      "tank_count": 1
    }},
    "customer_requirements": [
      "RETIE compliance",
      "Spanish documentation"
    ]
  }}'"""
            },
            "list_sizings": {
                "description": "List recent sizings",
                "command": f"curl {api_url}/sizings?limit=10"
            },
            "get_sizing": {
                "description": "Get sizing details",
                "command": f"curl {api_url}/sizings/SZ-20251019203904"
            }
        },
        "python_example": {
            "description": "Python client example",
            "code": f"""import requests

# Size a project
response = requests.post('{api_url}/size', json={{
    'project_description': 'Three-phase separator with PLC',
    'customer_name': 'Deilim',
    'country': 'colombia',
    'project_parameters': {{
        'io_count': 64,
        'instrument_count': 20
    }}
}})

sizing = response.json()
print(f"Total Hours: {{sizing['estimation']['total_hours']}}")
print(f"Total Cost: ${{sizing['estimation']['total_cost']:,.2f}}")
print(f"Ready for Quote: {{sizing['assessment']['ready_for_quotation']}}")"""
        }
    }

if __name__ == "__main__":
    api_url = os.getenv("SIZING_API_URL", "http://localhost:8008")
    print("🚀 Starting INSA Project Sizing API...")
    print(f"📍 Server: {api_url}")
    print(f"📖 API Docs: {api_url}/docs")
    print(f"🔧 Examples: {api_url}/examples")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        log_level="info"
    )
