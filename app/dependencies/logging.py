import logging
import uuid
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    MutableMapping,
    NotRequired,
    TypedDict,
)

from fastapi import Request
from fastapi.params import Depends
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.responses import Response
from starlette.types import ASGIApp

from app.dependencies.request import Request

logger = logging.getLogger(__name__)


class RequestLoggerContext(TypedDict):
    request_id: NotRequired[str]


class RequestLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    logger: logging.Logger
    extra: RequestLoggerContext | None

    def __init__(
        self,
        logger: logging.Logger,
        extra: RequestLoggerContext | None = None,
    ) -> None:
        super().__init__(logger, extra)

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        if self.extra and (request_id := self.extra.get("request_id")):
            return f"[{request_id}] {msg}", kwargs
        return msg, kwargs

    @property
    def level(self) -> int:
        return self.logger.level


class LoggerMiddleware(BaseHTTPMiddleware):
    """Populates request state with corelation logger."""

    def __init__(
        self,
        app: ASGIApp,
        dispatch: DispatchFunction | None = None,
        *,
        name: str = __name__,
    ) -> None:
        self.name = name
        super().__init__(app, dispatch)

    def build_request_id(self, request: Request) -> str:
        return uuid.uuid4().hex

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            req_id = request.state.request_id
        except AttributeError:
            req_id = request.state.request_id = self.build_request_id(request)

        request.state.logger = RequestLoggerAdapter(
            logger,
            RequestLoggerContext(request_id=req_id),
        )
        return await call_next(request)


def get_logger(request: Request) -> logging.Logger:
    try:
        return request.state.logger
    except AttributeError:
        raise RuntimeError(f"{LoggerMiddleware} must be applied. ")


LoggerDepends = Annotated[logging.Logger, Depends(get_logger)]
"""Dependency annotation to get logger attached to current request. """
