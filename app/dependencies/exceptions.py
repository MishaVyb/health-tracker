import fastapi
from fastapi import params, status
from sqlalchemy.exc import NoResultFound


class HTTPException(fastapi.HTTPException):
    status_code: int

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=self.status_code, detail=detail)


class HTTPBadRequestError(HTTPException):
    status_code: int = status.HTTP_400_BAD_REQUEST


class HTTPNotFoundError(HTTPException):
    status_code: int = status.HTTP_404_NOT_FOUND


class HTTPTimeoutError(HTTPException):
    status_code: int = status.HTTP_504_GATEWAY_TIMEOUT


class ServiceExceptionDepends(params.Depends):
    """
    Translate custom service exception into HTTP errors.

    Depends implementation in order to be called before middleware exist stack,
    where FastAPI/Starlette has its own exception handler implementation.
    """

    def __init__(self, *, use_cache: bool = True):
        super().__init__(dependency=self, use_cache=use_cache)

    async def __call__(self):
        try:
            yield
        except NoResultFound as e:
            raise HTTPNotFoundError(detail=str(e))
