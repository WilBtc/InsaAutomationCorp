"""
INSA CRM System - FastAPI Main Application
Multi-agent CRM orchestrator for industrial automation company

Handles:
- Lead qualification
- Quote generation
- Security assessments
- Proposal writing
- Compliance tracking
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import structlog
from prometheus_client import make_asgi_app
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import engine, init_db
from .api.v1 import api_router
from .core.rate_limit import limiter, rate_limit_exceeded_handler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("insa_crm_starting", version="0.1.0")
    await init_db()
    logger.info("database_initialized")

    # Load MCP servers
    from .core.mcp_manager import mcp_manager
    await mcp_manager.initialize()
    logger.info("mcp_servers_initialized", count=len(mcp_manager.servers))

    yield

    # Shutdown
    logger.info("insa_crm_shutting_down")
    await mcp_manager.shutdown()
    await engine.dispose()


# Initialize FastAPI app
app = FastAPI(
    title="INSA CRM System",
    description="AI-Powered CRM for Industrial Automation Engineering",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Include authentication routers
from .routers import auth_simple, admin
app.include_router(auth_simple.router)
app.include_router(admin.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "insa-crm-system",
        "version": "0.1.0"
    }


@app.get("/chat")
async def chat_ui():
    """Serve the CRM chat interface"""
    chat_file = Path(__file__).parent.parent / "static" / "chat.html"
    if chat_file.exists():
        return FileResponse(chat_file)
    else:
        raise HTTPException(status_code=404, detail="Chat UI not found")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "INSA CRM System",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/health",
        "chat": "/chat"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("unhandled_exception", exception=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
