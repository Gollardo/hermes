from fastapi import APIRouter, Depends

from app.api.routes.health import router as health_router
from app.modules.auth.dependencies import require_authenticated_session, require_csrf_session
from app.modules.auth.router import protected_router as protected_auth_router
from app.modules.auth.router import public_router as public_auth_router
from app.modules.settings.router import read_router as settings_read_router
from app.modules.settings.router import write_router as settings_write_router


def create_api_router() -> APIRouter:
    """Compose the public HTTP API from module-owned routers."""
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(public_auth_router)

    protected = APIRouter(dependencies=[Depends(require_authenticated_session)])
    protected.include_router(protected_auth_router)
    protected.include_router(settings_read_router)
    protected.include_router(
        settings_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    router.include_router(protected)
    return router
