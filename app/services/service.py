import uuid
from typing import Annotated

from fastapi import Depends

from app.dependencies.exceptions import HTTPBadRequestError
from app.repository.repositories import DatabaseRepositoriesDepends
from app.schemas import schemas
from app.schemas.base import EMPTY_PAYLOAD


class HealthTrackerService:
    def __init__(self, db: DatabaseRepositoriesDepends) -> None:
        self.db = db

    ########################################################################################

    async def create_patient(
        self, patient: schemas.PatientCreate
    ) -> schemas.PatientRead:
        return await self.db.patients.create(patient)

    async def get_patient(self, pk: uuid.UUID) -> schemas.PatientRead:
        return await self.db.patients.get(pk)

    async def get_patients(self) -> list[schemas.PatientRead]:
        return await self.db.patients.get_all()

    async def update_patient(
        self, pk: uuid.UUID, payload: schemas.PatientUpdate
    ) -> schemas.PatientRead:
        return await self.db.patients.update(pk, payload)

    async def delete_patient(self, pk: uuid.UUID) -> None:
        return await self.db.patients.delete(pk)

    ########################################################################################

    async def create_codeable_concept(
        self, payload: schemas.CodeableConceptCreate
    ) -> schemas.CodeableConceptRead:
        instance = await self.db.concepts.create(payload)

        # handle many-to-many relationships:
        for code in payload.coding:
            code_instance = await self.db.codes.create_if_not_exists(code)
            await self.db.concept_to_code.pending_create(
                EMPTY_PAYLOAD,
                codeable_concept_id=instance.id,
                coding_id=code_instance.id,
            )

        # refresh instance:
        return await self.db.concepts.get(instance.id, cached=False)

    async def get_codeable_concept(self, pk: uuid.UUID) -> schemas.CodeableConceptRead:
        return await self.db.concepts.get(pk)

    async def get_codeable_concepts(self) -> list[schemas.CodeableConceptRead]:
        return await self.db.concepts.get_all()

    async def update_codeable_concept(
        self, pk: uuid.UUID, payload: schemas.CodeableConceptUpdate
    ) -> schemas.CodeableConceptRead:
        instance = await self.db.concepts.update(pk, payload)

        # handle many-to-many relationships:
        if "coding" in payload.model_fields_set:
            raise HTTPBadRequestError(
                detail="Update nested coding is not currently supported."
            )

        # refresh instance:
        return await self.db.concepts.get(instance.id, cached=False)

    async def delete_codeable_concept(self, pk: uuid.UUID) -> None:
        return await self.db.concepts.delete(pk)

    ########################################################################################

    async def create_observation(
        self, observation: schemas.ObservationCreate
    ) -> schemas.ObservationRead:
        instance = await self.db.observations.create(observation, refresh=True)

        # handle many-to-many relationships:
        for category in observation.category_ids:
            category_instance = await self.db.concepts.get(category)
            await self.db.observation_to_concept.pending_create(
                EMPTY_PAYLOAD,
                observation_id=instance.id,
                codeable_concept_id=category_instance.id,
            )

        # refresh instance:
        return await self.db.observations.get(instance.id, cached=False)

    async def get_observation(self, pk: uuid.UUID) -> schemas.ObservationRead:
        return await self.db.observations.get(pk)

    async def get_observations(self) -> list[schemas.ObservationRead]:
        return await self.db.observations.get_all()

    async def update_observation(
        self, pk: uuid.UUID, payload: schemas.ObservationUpdate
    ) -> schemas.ObservationRead:
        instance = await self.db.observations.update(pk, payload)

        # handle many-to-many relationships:
        if "category_ids" in payload.model_fields_set:
            # delete existing relationships:
            await self.db.observation_to_concept.delete_where(
                observation_id=instance.id,
            )

            # create new relationships:
            for category in payload.category_ids or []:
                category_instance = await self.db.concepts.get(category)
                await self.db.observation_to_concept.pending_create(
                    EMPTY_PAYLOAD,
                    observation_id=instance.id,
                    codeable_concept_id=category_instance.id,
                )

        # refresh instance:
        return await self.db.observations.get(instance.id, cached=False)

    async def delete_observation(self, pk: uuid.UUID) -> None:
        return await self.db.observations.delete(pk)


HealthTrackerServiceDepends = Annotated[HealthTrackerService, Depends()]
