from http import HTTPMethod
from uuid import UUID

from pydantic import AwareDatetime

from app.adapter.base import HTTPAdapterBase
from app.schemas import schemas


class HealthTrackerAdapter(HTTPAdapterBase):
    _api_prefix = "/api"

    ########################################################################################
    # Patients
    ########################################################################################

    async def get_patients(self) -> schemas.GetPatientsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            "/patients",
            response_schema=schemas.GetPatientsResponse,
        )

    async def get_patient(self, id: UUID) -> schemas.PatientRead:
        return await self._call_service(
            HTTPMethod.GET,
            f"/patients/{id}",
            response_schema=schemas.PatientRead,
        )

    async def create_patient(
        self, payload: schemas.PatientCreate
    ) -> schemas.PatientRead:
        return await self._call_service(
            HTTPMethod.POST,
            "/patients",
            payload=payload,
            response_schema=schemas.PatientRead,
        )

    async def update_patient(
        self,
        id: UUID,
        payload: schemas.PatientUpdate,
    ) -> schemas.PatientRead:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/patients/{id}",
            payload=payload,
            response_schema=schemas.PatientRead,
        )

    async def delete_patient(self, id: UUID) -> None:
        return await self._call_service(
            HTTPMethod.DELETE,
            f"/patients/{id}",
        )

    ########################################################################################
    # Observations
    ########################################################################################

    async def get_observations(
        self,
        *,
        kinds: list[schemas.CodeKind] | None = None,
        codes: list[schemas.CodeType] | None = None,
        subject_ids: list[UUID] | None = None,
        start: AwareDatetime | None = None,
        end: AwareDatetime | None = None,
    ) -> schemas.GetObservationsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            "/observations",
            params=schemas.ObservationFilters(
                kinds=kinds,
                codes=codes,
                subject_ids=subject_ids,
                start=start,
                end=end,
            ),
            response_schema=schemas.GetObservationsResponse,
        )

    async def get_observation(self, id: UUID) -> schemas.ObservationRead:
        return await self._call_service(
            HTTPMethod.GET,
            f"/observations/{id}",
            response_schema=schemas.ObservationRead,
        )

    async def create_observation(
        self, payload: schemas.ObservationCreate
    ) -> schemas.ObservationRead:
        return await self._call_service(
            HTTPMethod.POST,
            "/observations",
            payload=payload,
            response_schema=schemas.ObservationRead,
        )

    async def update_observation(
        self,
        id: UUID,
        payload: schemas.ObservationUpdate,
    ) -> schemas.ObservationRead:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/observations/{id}",
            payload=payload,
            response_schema=schemas.ObservationRead,
        )

    async def delete_observation(self, id: UUID) -> None:
        return await self._call_service(
            HTTPMethod.DELETE,
            f"/observations/{id}",
        )

    ########################################################################################
    # CodeableConcepts
    ########################################################################################

    async def get_codeable_concepts(
        self,
    ) -> schemas.GetCodeableConceptsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            "/codeable-concepts",
            response_schema=schemas.GetCodeableConceptsResponse,
        )

    async def get_codeable_concept(self, id: UUID) -> schemas.CodeableConceptRead:
        return await self._call_service(
            HTTPMethod.GET,
            f"/codeable-concepts/{id}",
            response_schema=schemas.CodeableConceptRead,
        )

    async def create_codeable_concept(
        self, payload: schemas.CodeableConcept | schemas.CodeableConceptCreate
    ) -> schemas.CodeableConceptRead:
        return await self._call_service(
            HTTPMethod.POST,
            "/codeable-concepts",
            payload=payload,
            response_schema=schemas.CodeableConceptRead,
        )

    async def update_codeable_concept(
        self,
        id: UUID,
        payload: schemas.CodeableConceptUpdate,
    ) -> schemas.CodeableConceptRead:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/codeable-concepts/{id}",
            payload=payload,
            response_schema=schemas.CodeableConceptRead,
        )

    async def delete_codeable_concept(self, id: UUID) -> None:
        return await self._call_service(HTTPMethod.DELETE, f"/codeable-concepts/{id}")

    ########################################################################################
    # Health Score
    ########################################################################################

    async def get_health_score(
        self, patient_id: UUID, start: AwareDatetime, end: AwareDatetime
    ) -> schemas.DiagnosticReport:
        return await self._call_service(
            HTTPMethod.GET,
            f"/health-score/{patient_id}",
            params=schemas.ObservationFilters(start=start, end=end),
            response_schema=schemas.DiagnosticReport,
        )
