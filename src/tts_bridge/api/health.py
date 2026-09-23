"""`/health` route."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..backends.base import Backend
from .deps import get_backend
from .schemas import HealthResponse

router = APIRouter()


@router.get("/health")
async def health(backend: Backend = Depends(get_backend)) -> HealthResponse:
    ok = await backend.health()
    return HealthResponse(status="ok" if ok else "degraded", backend=backend.name, backend_healthy=ok)
