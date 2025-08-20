from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fhir.resources.diagnosticreport import DiagnosticReport
from pydantic import AwareDatetime
from starlette import status

from app.repository.repositories import DatabaseRepositoriesDepends
from app.schemas import schemas
from app.services.service import HealthTrackerServiceDepends

########################################################################################
# Patients
########################################################################################


patients = APIRouter(prefix="/patients", tags=["Patients"])


@patients.get("")
async def get_patients(db: DatabaseRepositoriesDepends) -> schemas.GetPatientsResponse:
    return schemas.GetPatientsResponse(items=await db.patients.get_all())


@patients.get("/{pk}")
async def get_patient(
    db: DatabaseRepositoriesDepends, *, pk: UUID
) -> schemas.PatientRead:
    return await db.patients.get(pk)


@patients.post("", status_code=status.HTTP_201_CREATED)
async def create_patient(
    db: DatabaseRepositoriesDepends, *, payload: schemas.PatientCreate
) -> schemas.PatientRead:
    return await db.patients.create(payload)


@patients.patch("/{pk}", status_code=status.HTTP_200_OK)
async def update_patient(
    db: DatabaseRepositoriesDepends, *, pk: UUID, payload: schemas.PatientUpdate
) -> schemas.PatientRead:
    return await db.patients.update(pk, payload, flush=True)


@patients.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(db: DatabaseRepositoriesDepends, *, pk: UUID) -> None:
    await db.patients.delete(pk)


########################################################################################
# Observations
########################################################################################

observations = APIRouter(prefix="/observations", tags=["Observations"])


@observations.get("")
async def get_observations(
    service: HealthTrackerServiceDepends,
    *,
    kinds: Annotated[  # TODO
        list[schemas.CodeKind] | None,
        Query(description="List of observation kinds to filter observations by"),
    ] = None,
    code_ids: Annotated[  # TODO
        list[UUID] | None,
        Query(description="List of code IDs to filter observations by"),
    ] = None,
    subject_ids: Annotated[
        list[UUID] | None,
        Query(description="List of patient IDs to filter observations by"),
    ] = None,
    start: Annotated[
        AwareDatetime | None,
        Query(description="Start date of the observation period"),
    ] = None,
    end: Annotated[
        AwareDatetime | None,
        Query(description="End date of the observation period"),
    ] = None,
) -> schemas.GetObservationsResponse:
    filters = schemas.ObservationFilters(
        subject_ids=subject_ids or [],
        start=start,
        end=end,
    )
    return schemas.GetObservationsResponse(
        items=await service.get_observations(filters)
    )


@observations.get("/{pk}")
async def get_observation(
    service: HealthTrackerServiceDepends, *, pk: UUID
) -> schemas.ObservationRead:
    return await service.get_observation(pk)


@observations.post("", status_code=status.HTTP_201_CREATED)
async def create_observation(
    service: HealthTrackerServiceDepends, *, payload: schemas.ObservationCreate
) -> schemas.ObservationRead:
    return await service.create_observation(payload)


@observations.patch("/{pk}", status_code=status.HTTP_200_OK)
async def update_observation(
    service: HealthTrackerServiceDepends,
    *,
    pk: UUID,
    payload: schemas.ObservationUpdate,
) -> schemas.ObservationRead:
    return await service.update_observation(pk, payload)


@observations.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(service: HealthTrackerServiceDepends, *, pk: UUID) -> None:
    await service.delete_observation(pk)


########################################################################################
# CodeableConcepts
########################################################################################

concepts = APIRouter(prefix="/codeable-concepts", tags=["CodeableConcepts"])


@concepts.get("")
async def get_codeable_concepts(
    service: HealthTrackerServiceDepends,
) -> schemas.GetCodeableConceptsResponse:
    return schemas.GetCodeableConceptsResponse(
        items=await service.get_codeable_concepts()
    )


@concepts.get("/{pk}")
async def get_codeable_concept(
    service: HealthTrackerServiceDepends, *, pk: UUID
) -> schemas.CodeableConceptRead:
    return await service.get_codeable_concept(pk)


@concepts.post("", status_code=status.HTTP_201_CREATED)
async def create_codeable_concept(
    service: HealthTrackerServiceDepends, *, payload: schemas.CodeableConceptCreate
) -> schemas.CodeableConceptRead:
    return await service.create_codeable_concept(payload)


@concepts.patch("/{pk}", status_code=status.HTTP_200_OK)
async def update_codeable_concept(
    service: HealthTrackerServiceDepends,
    *,
    pk: UUID,
    payload: schemas.CodeableConceptUpdate,
) -> schemas.CodeableConceptRead:
    return await service.update_codeable_concept(pk, payload)


@concepts.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_codeable_concept(
    service: HealthTrackerServiceDepends, *, pk: UUID
) -> None:
    await service.delete_codeable_concept(pk)


########################################################################################
# Health Score
########################################################################################

score = APIRouter(prefix="/health-score", tags=["Health Score"])


@score.get("/{patient_id}")
async def get_health_score(
    service: HealthTrackerServiceDepends,
    *,
    patient_id: UUID,
    start: Annotated[
        AwareDatetime, Query(description="Start date of the observation period")
    ],
    end: Annotated[
        AwareDatetime, Query(description="End date of the observation period")
    ],
) -> DiagnosticReport:
    """
    Calculate and return a health score for a patient.

    The health score is calculated based on:
    - Number and variety of health observations
    - Comparison to population averages
    - Data consistency

    Returns a FHIR-compliant DiagnosticReport.
    """
    return await service.get_health_score(
        schemas.ObservationFilters(
            subject_ids=[patient_id],
            start=start,
            end=end,
        )
    )


########################################################################################
# Other
########################################################################################

monitoring = APIRouter(prefix="", tags=["Monitoring"])


@monitoring.get("/health")
async def health() -> None:
    return None
