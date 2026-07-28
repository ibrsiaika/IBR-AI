"""
API Server — REST API for the IBR Platform (PRD Section 20).

Uses FastAPI (FREE, open source) for the REST API server.
Exposes: health, research, memory, training, models, knowledge graph endpoints.

All FREE — no paid API gateway, no paid authentication service.

References:
    - PRD Section 20 (APIs & Dashboard)
    - PRD Section 63 (Streaming — SSE)
    - PRD Section 62 (Structured Outputs)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ibr_platform.platform.architecture import list_layers
from ibr_platform.platform.memory import MemoryManager, MemoryTier
from ibr_platform.platform.orchestrator import TaskOrchestrator

# ============================================
# Request/Response Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ResearchRequest(BaseModel):
    """Research API request."""
    query: str = Field(..., description="Research query")
    user_id: str = Field(default="anonymous", description="User ID")
    max_results: int = Field(default=10, description="Max results per source")


class ResearchResponse(BaseModel):
    """Research API response."""
    request_id: str
    status: str = "pending"
    query: str


class MemoryWriteRequest(BaseModel):
    """Memory write API request."""
    content: str
    tier: str = "long_term"
    scope: str = "project"
    scope_id: str = "default"
    confidence: float = 0.0


class MemoryWriteResponse(BaseModel):
    """Memory write API response."""
    memory_id: str
    success: bool = True


class MemorySearchRequest(BaseModel):
    """Memory search API request."""
    query: str
    scope: str | None = None
    scope_id: str | None = None
    top_k: int = 10


class MemoryEntryResponse(BaseModel):
    """Memory entry API response."""
    id: str
    content: str
    tier: str
    scope: str
    scope_id: str
    confidence: float
    access_count: int


class ArchitectureResponse(BaseModel):
    """Architecture info API response."""
    layers: list[dict[str, Any]]


# ============================================
# API Server Factory
# ============================================

def create_app() -> FastAPI:
    """Create the FastAPI application.

    Returns:
        Configured FastAPI instance with all routes.
    """
    app = FastAPI(
        title="IBR Platform API",
        description="Autonomous Agentic AI Research & Self-Improving Foundation Model Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS (allow all for development; restrict in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize platform components
    orchestrator = TaskOrchestrator()
    memory_manager = MemoryManager()

    # ============================================
    # Routes
    # ============================================

    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse()

    @app.get("/api/v1/architecture", response_model=ArchitectureResponse)
    async def get_architecture() -> ArchitectureResponse:
        """Get the platform's layered architecture."""
        layers = []
        for layer in list_layers():
            from ibr_platform.platform.architecture import get_architecture_info
            info = get_architecture_info(layer)
            layers.append({
                "id": layer.value,
                "name": layer.name,
                **info,
            })
        return ArchitectureResponse(layers=layers)

    @app.post("/api/v1/research", response_model=ResearchResponse)
    async def submit_research(request: ResearchRequest) -> ResearchResponse:
        """Submit a research request.

        Creates a new request in the TaskOrchestrator and returns the
        request ID for polling.
        """
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        request_id = await orchestrator.submit_request(
            query=request.query,
            user_id=request.user_id,
            metadata={"max_results": request.max_results},
        )
        return ResearchResponse(
            request_id=request_id,
            query=request.query,
        )

    @app.get("/api/v1/research/{request_id}")
    async def get_research_result(request_id: str) -> dict[str, Any]:
        """Get the status and result of a research request."""
        request = await orchestrator.get_result(request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="Request not found")
        return {
            "request_id": request.id,
            "status": request.status.value,
            "query": request.query,
            "result": request.result,
            "error": request.error,
            "created_at": request.created_at.isoformat(),
            "updated_at": request.updated_at.isoformat(),
        }

    @app.get("/api/v1/research")
    async def list_research_requests(
        user_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List research requests with optional filters."""
        from ibr_platform.platform.orchestrator import RequestStatus
        status_enum = RequestStatus(status) if status else None
        requests = await orchestrator.list_requests(user_id=user_id, status=status_enum)
        return [
            {
                "request_id": r.id,
                "status": r.status.value,
                "query": r.query,
                "user_id": r.user_id,
            }
            for r in requests
        ]

    @app.post("/api/v1/memory/write", response_model=MemoryWriteResponse)
    async def write_memory(request: MemoryWriteRequest) -> MemoryWriteResponse:
        """Write to the memory system."""
        tier = MemoryTier(request.tier)
        entry_id = await memory_manager.write(
            content=request.content,
            tier=tier,
            scope=request.scope,
            scope_id=request.scope_id,
            confidence=request.confidence,
        )
        return MemoryWriteResponse(memory_id=entry_id)

    @app.post("/api/v1/memory/search")
    async def search_memory(request: MemorySearchRequest) -> list[dict[str, Any]]:
        """Search the memory system."""
        results = await memory_manager.search(
            query=request.query,
            scope=request.scope,
            scope_id=request.scope_id,
            top_k=request.top_k,
        )
        return [
            {
                "id": e.id,
                "content": e.content,
                "tier": e.tier.value,
                "scope": e.scope,
                "scope_id": e.scope_id,
                "confidence": e.confidence,
                "access_count": e.access_count,
            }
            for e in results
        ]

    @app.get("/api/v1/memory/stats")
    async def memory_stats() -> dict[str, int]:
        """Get memory statistics (per-tier counts)."""
        stats = memory_manager.get_stats()
        return {tier.value: count for tier, count in stats.items()}

    @app.get("/api/v1/memory/{entry_id}")
    async def read_memory(entry_id: str) -> dict[str, Any]:
        """Read a specific memory entry by ID."""
        entry = await memory_manager.read(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Memory entry not found")
        return {
            "id": entry.id,
            "content": entry.content,
            "tier": entry.tier.value,
            "scope": entry.scope,
            "scope_id": entry.scope_id,
            "version": entry.version,
            "confidence": entry.confidence,
            "access_count": entry.access_count,
            "created_at": entry.created_at.isoformat(),
        }

    @app.delete("/api/v1/memory/{entry_id}")
    async def delete_memory(entry_id: str) -> dict[str, bool]:
        """Delete a memory entry."""
        deleted = await memory_manager.delete(entry_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Memory entry not found")
        return {"deleted": True}

    @app.get("/api/v1/orchestrator/health")
    async def orchestrator_health() -> dict[str, Any]:
        """Get orchestrator health."""
        health = await orchestrator.health_check()
        return {
            "status": health.status,
            "active_requests": health.active_requests,
            "total_requests": health.total_requests,
            "uptime_seconds": health.uptime_seconds,
        }

    return app


# Create the default app instance
app = create_app()
