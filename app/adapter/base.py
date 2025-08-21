import asyncio
from http import HTTPMethod
from typing import Any, Type, TypeVar, overload

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, TypeAdapter

from app.dependencies.exceptions import (
    HTTPBadRequestError,
    HTTPNotFoundError,
    HTTPTimeoutError,
)

_T = TypeVar("_T")
_TSchema = TypeVar("_TSchema", bound=BaseModel)
_TYPE_ADAPTERS: dict[type, TypeAdapter[Any]] = {}

PrimitiveData = str | int | float | bool | None
QueryParamTypes = (
    dict[str, PrimitiveData | list[PrimitiveData]] | list[tuple[str, PrimitiveData]]
)


class HTTPContentError(ValueError):
    pass


class HTTPAdapterBase:
    """Pydantic oriented adapter on top of HTTPX client."""

    # class level configuration
    _base_url: httpx.URL | str | None = None
    _api_prefix: httpx.URL | str | None = None

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    def _use_url(self, url: httpx.URL | str) -> httpx.URL:
        if isinstance(url, str):
            url = httpx.URL(url)
        if self._api_prefix:
            url = url.copy_with(path=str(self._api_prefix) + str(url.path))
        if self._base_url and not self._client.base_url:
            url = self._base_url.join(url)
        return url

    def _use_params(
        self, params: QueryParamTypes | BaseModel | None = None
    ) -> QueryParamTypes | None:
        """Build request Params."""
        if isinstance(params, BaseModel):
            return params.model_dump(
                exclude_unset=True, exclude_none=True, by_alias=True, mode="json"
            )
        return params

    def _use_json(self, payload: BaseModel | None = None) -> str | None:
        """Build and serialize request payload."""
        if not payload:
            return None

        return payload.model_dump_json(exclude_unset=True, by_alias=True)

    @overload
    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: Type[_TSchema],  # overload reason
        **other_request_kwargs,
    ) -> _TSchema:
        """Normalize request options. Parse response."""

    @overload
    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: Type[_T],  # overload reason
        **other_request_kwargs,
    ) -> _T:
        """Normalize request options. Parse response."""

    @overload
    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: TypeAdapter[_T],  # overload reason
        **other_request_kwargs,
    ) -> _T:
        """Normalize request options. Parse response."""

    @overload
    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: None = None,  # overload reason
        **other_request_kwargs,
    ) -> None:
        """Normalize request options. No content response."""

    # NOTE
    # This overload is for unsupported special forms (such as Annotated, Union, etc.)
    # Currently there is no way to type this correctly
    # See https://github.com/python/typing/pull/1618
    @overload
    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: Any,  # overload reason
        **other_request_kwargs,
    ) -> Any:
        """Normalize request options. No content response."""

    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: Any | None = None,
        validation_context: dict[str, Any] | None = None,
        **other_request_kwargs,
    ) -> _TSchema | _T | None:
        response_with_content = True if response_schema else False

        url = self._use_url(url)
        json = self._use_json(payload)
        params = self._use_params(params)

        try:
            content = await self._process_request(
                method,
                url,
                response_with_content=response_with_content,
                params=params,
                data=json,
                **other_request_kwargs,
            )

        # request timeout:
        except asyncio.TimeoutError:
            raise HTTPTimeoutError(f"HTTP Request timed out: {method} {url}")

        # reraise http error with original status code:
        except httpx.HTTPStatusError as e:
            detail = (
                f"HTTP Request failed: bad status code received. {method} {url} {e}"
            )
            if e.response.status_code == HTTPNotFoundError.status_code:
                raise HTTPNotFoundError(detail)
            if e.response.status_code == HTTPBadRequestError.status_code:
                raise HTTPBadRequestError(detail)

            raise HTTPException(status_code=e.response.status_code, detail=detail)

        if response_with_content:
            return await self._validate_content(
                response_schema, content, validation_context
            )

        return None

    async def _process_request(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        response_with_content: bool,
        params: QueryParamTypes | None = None,
        data: str | bytes | None = None,
        **request_kwargs,
    ) -> bytes | None:
        req = self._client.build_request(
            method,
            url,
            params=params,
            content=data,
            files=request_kwargs.get("files", None),
            headers=request_kwargs.get("headers", None),
            cookies=request_kwargs.get("cookies", None),
            timeout=request_kwargs.get("timeout", httpx.USE_CLIENT_DEFAULT),
            extensions=request_kwargs.get("extensions", None),
        )

        response: httpx.Response = await self._client.send(
            req,
            stream=request_kwargs.get("stream", False),
            auth=request_kwargs.get("auth", httpx.USE_CLIENT_DEFAULT),
            follow_redirects=request_kwargs.get(
                "follow_redirects", httpx.USE_CLIENT_DEFAULT
            ),
        )
        response.raise_for_status()

        if response_with_content:
            if not response.content:
                raise HTTPContentError(
                    f"HTTP Request failed: no content received. {method} {url}"
                )
            return response.content
        return None

    async def _validate_content(
        self,
        response_schema: Any,
        content: bytes | str | None,
        validation_context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Validate raw content and build appropriate response schema.
        Async method in order to support heavy validation in thread pool, etc.
        """
        adapter: TypeAdapter[Any] | None
        if isinstance(response_schema, TypeAdapter):
            adapter = response_schema
        elif not (adapter := _TYPE_ADAPTERS.get(response_schema)):
            adapter = _TYPE_ADAPTERS[response_schema] = TypeAdapter(response_schema)

        return adapter.validate_json(content or b"", context=validation_context)
