from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class AngularStaticFiles(StaticFiles):
    """Serve Angular assets and fall back to index.html for client-side routes."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as error:
            if error.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


def mount_frontend(app: FastAPI, static_dir: Path | None) -> None:
    if static_dir is None:
        return
    index = static_dir / "index.html"
    if not index.is_file():
        raise RuntimeError(f"Angular build not found: {index}")
    app.mount("/", AngularStaticFiles(directory=static_dir, html=True), name="frontend")
