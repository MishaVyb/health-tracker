from http import HTTPMethod
from uuid import UUID

from app.client.base import HTTPAdapterBase
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

    async def get_patient(self, id: UUID) -> schemas.Patient:
        return await self._call_service(
            HTTPMethod.GET,
            f"/patients/{id}",
            response_schema=schemas.Patient,
        )

    async def create_patient(self, payload: schemas.PatientCreate) -> schemas.Patient:
        return await self._call_service(
            HTTPMethod.POST,
            "/patients",
            payload=payload,
            response_schema=schemas.Patient,
        )

    async def update_patient(
        self,
        id: UUID,
        payload: schemas.PatientUpdate,
    ) -> schemas.Patient:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/patients/{id}",
            payload=payload,
            response_schema=schemas.Patient,
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
    ) -> schemas.GetObservationsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            "/observations",
            response_schema=schemas.GetObservationsResponse,
        )

    async def get_observation(self, id: UUID) -> schemas.Observation:
        return await self._call_service(
            HTTPMethod.GET,
            f"/observations/{id}",
            response_schema=schemas.Observation,
        )

    async def create_observation(
        self, payload: schemas.ObservationCreate
    ) -> schemas.Observation:
        return await self._call_service(
            HTTPMethod.POST,
            "/observations",
            payload=payload,
            response_schema=schemas.Observation,
        )

    async def update_observation(
        self,
        id: UUID,
        payload: schemas.ObservationUpdate,
    ) -> schemas.Observation:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/observations/{id}",
            payload=payload,
            response_schema=schemas.Observation,
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

    async def get_concept(self, id: UUID) -> schemas.CodeableConcept:
        return await self._call_service(
            HTTPMethod.GET,
            f"/codeable-concepts/{id}",
            response_schema=schemas.CodeableConcept,
        )

    async def create_codeable_concept(
        self, payload: schemas.CodeableConceptCreate
    ) -> schemas.CodeableConcept:
        return await self._call_service(
            HTTPMethod.POST,
            "/codeable-concepts",
            payload=payload,
            response_schema=schemas.CodeableConcept,
        )

    async def update_codeable_concept(
        self,
        id: UUID,
        payload: schemas.CodeableConceptUpdate,
    ) -> schemas.Observation:
        return await self._call_service(
            HTTPMethod.PATCH,
            f"/codeable-concepts/{id}",
            payload=payload,
            response_schema=schemas.CodeableConcept,
        )

    async def delete_codeable_concept(self, id: UUID) -> None:
        return await self._call_service(HTTPMethod.DELETE, f"/codeable-concepts/{id}")
