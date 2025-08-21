from http import HTTPMethod
from pathlib import Path
from typing import Type, TypeVar

import httpx
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from pydantic import BaseModel

from app.adapter.base import HTTPAdapterBase, QueryParamTypes

_T = TypeVar("_T")


class ExternalFHIRSourceJSONFiles(BaseModel):
    """External FHIR resources as stored JSON files."""

    patients: Path
    observations: Path


class ExternalFHIRAdapter(HTTPAdapterBase):
    """
    Adapter for the third party FHIR server.
    Resolve FHIR resources from HTTPX client or JSON files.
    """

    _api_prefix = "/fhir"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        source: ExternalFHIRSourceJSONFiles | None = None,
    ) -> None:
        if not client and not source:
            raise ValueError("Either client or source must be provided")
        if client and source:
            raise ValueError("Either client or source must be provided, not both")

        self._client = client
        self._source = source

    async def get_patients(self) -> list[Patient]:
        return await self._call_service(
            HTTPMethod.GET, "/patients", response_schema=list[Patient]
        )

    async def get_observations(self) -> list[Observation]:
        return await self._call_service(
            HTTPMethod.GET, "/observations", response_schema=list[Observation]
        )

    async def _call_service(
        self,
        method: HTTPMethod,
        url: httpx.URL | str,
        *,
        params: BaseModel | QueryParamTypes | None = None,
        payload: BaseModel | None = None,
        response_schema: Type[_T],
        **other_request_kwargs,
    ) -> _T:
        if self._client:
            return await super()._call_service(
                method,
                url,
                params=params,
                payload=payload,
                response_schema=response_schema,
                **other_request_kwargs,
            )

        source = getattr(self._source, str(url).lstrip("/"), None)
        if not source:
            raise ValueError(f"No source file for {url}")

        with open(source, "r") as f:
            return await self._validate_content(response_schema, f.read())
