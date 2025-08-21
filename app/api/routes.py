from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query
from pydantic import AwareDatetime
from starlette import status

from app.repository.repositories import DatabaseRepositoriesDepends
from app.schemas import constants, schemas
from app.services.service import HealthTrackerServiceDepends

########################################################################################
# Patients
########################################################################################


patients = APIRouter(prefix="/patients", tags=["Patients"])

PatientIdPathParam = Annotated[
    UUID,
    Path(json_schema_extra=dict(example="30b37fe1-cef8-5f27-8203-5089c18cef47")),
]
SubjectIdsQueryParam = Annotated[
    list[UUID] | None,
    Query(
        description="List of patient IDs to filter observations by",
        example=["30b37fe1-cef8-5f27-8203-5089c18cef47"],
    ),
]
ObservationIdPathParam = Annotated[
    UUID,
    Path(json_schema_extra=dict(example="5e7580e2-cf8f-594e-9207-62e91997ac3b")),
]
CodeableConceptIdPathParam = Annotated[
    UUID,
    Path(json_schema_extra=dict(example="5e7580e2-cf8f-594e-9207-62e91997ac3b")),
]
DatetimeQueryParam = Annotated[
    AwareDatetime | None,
    Query(json_schema_extra=dict(example="2025-01-01 10:00Z")),
]


@patients.get("")
async def get_patients(db: DatabaseRepositoriesDepends) -> schemas.GetPatientsResponse:
    return schemas.GetPatientsResponse(items=await db.patients.get_all())


@patients.get("/{pk}")
async def get_patient(
    db: DatabaseRepositoriesDepends, *, pk: PatientIdPathParam
) -> schemas.PatientRead:
    return await db.patients.get(pk)


@patients.post("", status_code=status.HTTP_201_CREATED)
async def create_patient(
    db: DatabaseRepositoriesDepends, *, payload: schemas.PatientCreate
) -> schemas.PatientRead:
    return await db.patients.create(payload)


@patients.patch("/{pk}", status_code=status.HTTP_200_OK)
async def update_patient(
    db: DatabaseRepositoriesDepends,
    *,
    pk: PatientIdPathParam,
    payload: schemas.PatientUpdate,
) -> schemas.PatientRead:
    return await db.patients.update(pk, payload, flush=True)


@patients.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    db: DatabaseRepositoriesDepends, *, pk: PatientIdPathParam
) -> None:
    await db.patients.delete(pk)


########################################################################################
# Observations
########################################################################################

observations = APIRouter(prefix="/observations", tags=["Observations"])


@observations.get("")
async def get_observations(
    service: HealthTrackerServiceDepends,
    *,
    subject_ids: SubjectIdsQueryParam = None,
    kinds: Annotated[
        list[schemas.CodeKind] | None,
        Query(description="List of observation kinds to filter observations by"),
    ] = None,
    codes: Annotated[
        list[schemas.CodeType] | None,
        Query(description="List of codes to filter observations by"),
    ] = None,
    start: DatetimeQueryParam = None,
    end: DatetimeQueryParam = None,
) -> schemas.GetObservationsResponse:
    if kinds:
        codes = codes or []
        for kind in kinds:
            for concept in constants.get_codeable_concepts(kind):
                codes.extend(concept.codes())

    filters = schemas.ObservationFilters(
        subject_ids=subject_ids or [],
        codes=codes,
        start=start,
        end=end,
    )
    return schemas.GetObservationsResponse(
        items=await service.get_observations(filters)
    )


@observations.get("/{pk}")
async def get_observation(
    service: HealthTrackerServiceDepends, *, pk: ObservationIdPathParam
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
    pk: ObservationIdPathParam,
    payload: schemas.ObservationUpdate,
) -> schemas.ObservationRead:
    return await service.update_observation(pk, payload)


@observations.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(
    service: HealthTrackerServiceDepends, *, pk: ObservationIdPathParam
) -> None:
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
    service: HealthTrackerServiceDepends, *, pk: CodeableConceptIdPathParam
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
    pk: CodeableConceptIdPathParam,
    payload: schemas.CodeableConceptUpdate,
) -> schemas.CodeableConceptRead:
    return await service.update_codeable_concept(pk, payload)


@concepts.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_codeable_concept(
    service: HealthTrackerServiceDepends, *, pk: CodeableConceptIdPathParam
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
    patient_id: PatientIdPathParam,
    start: DatetimeQueryParam = None,
    end: DatetimeQueryParam = None,
) -> schemas.DiagnosticReport:
    """Calculate and return a health score in FHIR-compliant DiagnosticReport."""
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
