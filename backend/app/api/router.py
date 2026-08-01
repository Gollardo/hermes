from fastapi import APIRouter

from app.api.routes.health import router as health_router


def create_api_router() -> APIRouter:
    """Compose the public HTTP API from module-owned routers."""
    router = APIRouter()
    router.include_router(health_router)
    return router
