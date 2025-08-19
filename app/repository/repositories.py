from dataclasses import dataclass, fields
from typing import Annotated, Never
from uuid import UUID

from fastapi import Depends

from . import models, schemas
from .base import SQLAlchemyRepositoryBase


class PatientRepository(
    SQLAlchemyRepositoryBase[
        models.Patient,
        UUID,
        schemas.Patient,
        schemas.PatientCreate,
        schemas.PatientUpdate,
    ]
):
    model = models.Patient
    schema = schemas.Patient


class ObservationRepository(
    SQLAlchemyRepositoryBase[
        models.Observation,
        UUID,
        schemas.Observation,
        schemas.ObservationCreate,
        schemas.ObservationUpdate,
    ]
):
    model = models.Observation
    schema = schemas.Observation


class CodeableConceptRepository(
    SQLAlchemyRepositoryBase[
        models.CodeableConcept,
        UUID,
        schemas.CodeableConcept,
        schemas.CodeableConceptCreate,
        schemas.CodeableConceptUpdate,
    ]
):
    model = models.CodeableConcept
    schema = schemas.CodeableConcept


class ObservationToCodeableConceptRepository(
    SQLAlchemyRepositoryBase[
        models.CodeableConceptToObservation,
        UUID,
        Never,
        Never,
        Never,
    ]
):
    model = models.CodeableConceptToObservation
    schema = ...


@dataclass(kw_only=True)
class DatabaseRepositories:
    patients: Annotated[PatientRepository, Depends()]
    observations: Annotated[ObservationRepository, Depends()]
    codeable_concepts: Annotated[CodeableConceptRepository, Depends()]

    # def __post_init__(self) -> None:
    #     for repo in self.repositories:
    #         repo.db = self

    # @classmethod
    # def construct(
    #     cls,
    #     request: ObjectiveRequest,
    #     session: AsyncSession,
    #     app: ObjectiveAPP,
    #     settings: AppSettings,
    #     logger: Logger,
    # ) -> Self:
    #     # storage shared between all repositories for single session
    #     storage = StrongInstanceIdentityMap(session)
    #     return cls(
    #         # SQLAlchemyRepositories:
    #         **{
    #             field.name: field.type(
    #                 request=request,
    #                 session=session,
    #                 storage=storage,
    #                 logger=logger,
    #                 app=app,
    #                 settings=settings,
    #             )
    #             for field in fields(cls)
    #             if field.name != "users"
    #         },
    #         # other:
    #         users=UserRepository(session=session),
    #     )

    @property
    def repositories(self) -> list[SQLAlchemyRepositoryBase]:
        return [getattr(self, field.name) for field in fields(self)]


DatabaseRepositoriesDepends = Annotated[DatabaseRepositories, Depends()]
