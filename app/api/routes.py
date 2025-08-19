from uuid import UUID

from fastapi import APIRouter
from starlette import status

from app.repository.repositories import DatabaseRepositoriesDepends
from app.schemas import schemas

########################################################################################
# Patients
########################################################################################


patients = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@patients.get("")
async def get_patients(db: DatabaseRepositoriesDepends) -> schemas.GetPatientsResponse:
    return schemas.GetPatientsResponse(items=await db.patients.get_all())


@patients.get("/{id}")
async def get_patient(db: DatabaseRepositoriesDepends, *, id: UUID) -> schemas.Patient:
    return await db.patients.get(id)


@patients.post("", status_code=status.HTTP_201_CREATED)
async def create_patient(
    db: DatabaseRepositoriesDepends, *, payload: schemas.PatientCreate
) -> schemas.Patient:
    return await db.patients.create(payload)


@patients.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_patient(
    db: DatabaseRepositoriesDepends, *, id: UUID, payload: schemas.PatientUpdate
) -> schemas.Patient:
    return await db.patients.update(id, payload, flush=True)


@patients.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(db: DatabaseRepositoriesDepends, *, id: UUID) -> None:
    await db.patients.delete(id)


########################################################################################
# Observations
########################################################################################

observations = APIRouter(prefix="/observations", tags=["Observations"])


@observations.get("")
async def get_observations(
    db: DatabaseRepositoriesDepends,
) -> schemas.GetObservationsResponse:
    return schemas.GetObservationsResponse(items=await db.observations.get_all())


@observations.get("/{id}")
async def get_observation(
    db: DatabaseRepositoriesDepends, *, id: UUID
) -> schemas.Observation:
    return await db.observations.get(id)


@observations.post("", status_code=status.HTTP_201_CREATED)
async def create_observation(
    db: DatabaseRepositoriesDepends, *, payload: schemas.ObservationCreate
) -> schemas.Observation:
    return await db.observations.create(payload, refresh=True)


@observations.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_observation(
    db: DatabaseRepositoriesDepends, *, id: UUID, payload: schemas.ObservationUpdate
) -> schemas.Observation:
    return await db.observations.update(id, payload, refresh=True)


@observations.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(db: DatabaseRepositoriesDepends, *, id: UUID) -> None:
    await db.observations.delete(id)


########################################################################################
# CodeableConcepts
########################################################################################

concepts = APIRouter(prefix="/codeable-concepts", tags=["CodeableConcepts"])


@concepts.get("")
async def get_codeable_concepts(
    db: DatabaseRepositoriesDepends,
) -> schemas.GetCodeableConceptsResponse:
    return schemas.GetCodeableConceptsResponse(
        items=await db.codeable_concepts.get_all()
    )


@concepts.get("/{id}")
async def get_codeable_concept(
    db: DatabaseRepositoriesDepends, *, id: UUID
) -> schemas.CodeableConcept:
    return await db.codeable_concepts.get(id)


@concepts.post("", status_code=status.HTTP_201_CREATED)
async def create_codeable_concept(
    db: DatabaseRepositoriesDepends, *, payload: schemas.CodeableConceptCreate
) -> schemas.CodeableConcept:
    return await db.codeable_concepts.create(payload, refresh=True)


@concepts.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_codeable_concept(
    db: DatabaseRepositoriesDepends, *, id: UUID, payload: schemas.CodeableConceptUpdate
) -> schemas.CodeableConcept:
    return await db.codeable_concepts.update(id, payload, refresh=True)


@concepts.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_codeable_concept(db: DatabaseRepositoriesDepends, *, id: UUID) -> None:
    await db.codeable_concepts.delete(id)
