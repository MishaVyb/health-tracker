import fastapi
from fastapi import status


class HTTPException(fastapi.HTTPException):
    status_code: int

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=self.status_code, detail=detail)


class HTTPTimeoutError(HTTPException):
    status_code: int = status.HTTP_504_GATEWAY_TIMEOUT
