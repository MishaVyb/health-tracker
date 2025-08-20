from dataclasses import dataclass, fields
from typing import Annotated, Never
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from . import models, schemas
from .base import SQLAlchemyRepositoryBase


class PatientRepo(
    SQLAlchemyRepositoryBase[
        models.Patient,
        UUID,
        schemas.PatientRead,
        schemas.PatientCreate,
        schemas.PatientUpdate,
    ]
):
    _model = models.Patient
    _schema = schemas.PatientRead


class CodingRepo(
    SQLAlchemyRepositoryBase[
        models.Coding,
        UUID,
        schemas.CodingRead,  # read
        schemas.Coding,  # create
        Never,  # update
    ]
):
    _model = models.Coding
    _schema = schemas.CodingRead

    async def create_if_not_exists(self, payload: schemas.Coding) -> schemas.CodingRead:
        if instance := await self.get_one_or_none(code=payload.code):
            return instance
        return await self.create(payload)


class CodeableConceptRepo(
    SQLAlchemyRepositoryBase[
        models.CodeableConcept,
        UUID,
        schemas.CodeableConceptRead,
        schemas.CodeableConceptCreate,
        schemas.CodeableConceptUpdate,
    ]
):
    _model = models.CodeableConcept
    _schema = schemas.CodeableConceptRead

    @dataclass(kw_only=True)
    class SelectContext(SQLAlchemyRepositoryBase.SelectContext):
        loading_options: tuple[ORMOption, ...] = (
            selectinload(models.CodeableConcept.coding),
        )


class ObservationRepo(
    SQLAlchemyRepositoryBase[
        models.Observation,
        UUID,
        schemas.ObservationRead,
        schemas.ObservationCreate,
        schemas.ObservationUpdate,
    ]
):
    _model = models.Observation
    _schema = schemas.ObservationRead

    @dataclass(kw_only=True)
    class SelectContext(SQLAlchemyRepositoryBase.SelectContext):
        loading_options: tuple[ORMOption, ...] = (
            selectinload(models.Observation.subject),
            selectinload(models.Observation.code).selectinload(
                models.CodeableConcept.coding
            ),
            selectinload(models.Observation.category).selectinload(
                models.CodeableConcept.coding
            ),
        )


class CodeableConceptToCodeRepo(
    SQLAlchemyRepositoryBase[
        models.CodeableConceptToCoding,
        UUID,
        Never,
        Never,
        Never,
    ]
):
    _model = models.CodeableConceptToCoding
    _schema = ...


class ObservationToCodeableConceptRepo(
    SQLAlchemyRepositoryBase[
        models.CodeableConceptToObservation,
        UUID,
        Never,
        Never,
        Never,
    ]
):
    _model = models.CodeableConceptToObservation
    _schema = ...


@dataclass(kw_only=True)
class DatabaseRepositories:
    patients: Annotated[PatientRepo, Depends()]
    codes: Annotated[CodingRepo, Depends()]
    concepts: Annotated[CodeableConceptRepo, Depends()]
    observations: Annotated[ObservationRepo, Depends()]

    concept_to_code: Annotated[CodeableConceptToCodeRepo, Depends()]
    observation_to_concept: Annotated[ObservationToCodeableConceptRepo, Depends()]

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
    #         users=UserRepo(session=session),
    #     )

    @property
    def repositories(self) -> list[SQLAlchemyRepositoryBase]:
        return [getattr(self, field.name) for field in fields(self)]


DatabaseRepositoriesDepends = Annotated[DatabaseRepositories, Depends()]
