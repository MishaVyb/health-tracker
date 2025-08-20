from uuid import UUID

from fastapi import APIRouter
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
) -> schemas.GetObservationsResponse:
    return schemas.GetObservationsResponse(items=await service.get_observations())


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
