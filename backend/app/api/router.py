from fastapi import APIRouter, Depends

from app.api.routes.accounts import read_router as accounts_read_router
from app.api.routes.accounts import write_router as accounts_write_router
from app.api.routes.health import router as health_router
from app.modules.auth.dependencies import require_authenticated_session, require_csrf_session
from app.modules.auth.router import protected_router as protected_auth_router
from app.modules.auth.router import public_router as public_auth_router
from app.modules.categories.router import read_router as categories_read_router
from app.modules.categories.router import write_router as categories_write_router
from app.modules.funds.router import read_router as funds_read_router
from app.modules.funds.router import write_router as funds_write_router
from app.modules.operations.router import read_router as operations_read_router
from app.modules.operations.router import write_router as operations_write_router
from app.modules.settings.router import read_router as settings_read_router
from app.modules.settings.router import write_router as settings_write_router


def create_api_router() -> APIRouter:
    """Compose the public HTTP API from module-owned routers."""
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(public_auth_router)

    protected = APIRouter(dependencies=[Depends(require_authenticated_session)])
    protected.include_router(protected_auth_router)
    protected.include_router(accounts_read_router)
    protected.include_router(categories_read_router)
    protected.include_router(settings_read_router)
    protected.include_router(operations_read_router)
    protected.include_router(funds_read_router)
    protected.include_router(
        settings_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    protected.include_router(
        accounts_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    protected.include_router(
        categories_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    protected.include_router(
        operations_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    protected.include_router(
        funds_write_router,
        dependencies=[Depends(require_csrf_session)],
    )
    router.include_router(protected)
    return router
