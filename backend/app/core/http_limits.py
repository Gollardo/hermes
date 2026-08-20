from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.routing import APIRoute
from starlette.responses import Response
from starlette.types import Message

MAX_BACKUP_BYTES = 72 * 1024 * 1024


class BackupBodyLimitRoute(APIRoute):
    """Reject oversized backup bodies before FastAPI buffers and parses JSON."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_handler = super().get_route_handler()

        async def limited_handler(request: Request) -> Response:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    declared_size = int(content_length)
                except ValueError:
                    declared_size = MAX_BACKUP_BYTES + 1
                if declared_size > MAX_BACKUP_BYTES:
                    raise backup_too_large()

            received = 0
            original_receive = request.receive

            async def limited_receive() -> Message:
                nonlocal received
                message = await original_receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > MAX_BACKUP_BYTES:
                        raise backup_too_large()
                return message

            return await original_handler(Request(request.scope, limited_receive))

        return limited_handler


def backup_too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        detail={
            "code": "backup_too_large",
            "message": "Backup exceeds the 72 MiB request limit",
        },
    )


__all__ = ["BackupBodyLimitRoute", "MAX_BACKUP_BYTES", "backup_too_large"]
