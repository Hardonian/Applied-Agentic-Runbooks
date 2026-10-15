"""
Enhanced health check endpoints with circuit breaker status.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from agent_factory.security.circuit_breaker import _breakers

router = APIRouter()


@router.get("/circuit-breakers")
async def circuit_breaker_status():
    """
    Get status of all circuit breakers.
    
    Returns:
        Dictionary with circuit breaker statuses
    """
    statuses = {}
    for name, breaker in _breakers.items():
        statuses[name] = breaker.get_stats()
    
    return JSONResponse(content={"circuit_breakers": statuses})
