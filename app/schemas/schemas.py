from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, Field

from .base import (
    BaseSchema,
    CreateSchemaBase,
    ItemsResponseBase,
    ReadSchemaBase,
    UpdateSchemaBase,
)

########################################################################################
# Patient Schemas
########################################################################################


class HumanNameUse(StrEnum):
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    NICKNAME = "nickname"
    ANONYMOUS = "anonymous"
    OLD = "old"
    MAIDEN = "maiden"


class HumanName(BaseSchema):
    use: HumanNameUse | None = None
    family: str | None = None
    given: list[str] | None = None


class HumanGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class Patient(BaseSchema):
    name: list[HumanName] = []
    gender: HumanGender | None = None


class PatientRead(ReadSchemaBase, Patient):
    pass


class GetPatientsResponse(ItemsResponseBase[PatientRead]):
    pass


class PatientCreate(CreateSchemaBase, Patient):
    pass


class PatientUpdate(UpdateSchemaBase, Patient):
    pass


########################################################################################
# CodeableConcept Schemas
########################################################################################

CodeType = Annotated[
    str,
    Field(min_length=1, max_length=100, description="Unique code."),
]


class Coding(BaseSchema):
    code: CodeType
    system: str
    display: str | None = None


class CodingRead(ReadSchemaBase, Coding):
    pass


class CodeableConcept(BaseSchema):
    text: str
    coding: list[Coding] = []


class CodeableConceptRead(ReadSchemaBase, CodeableConcept):
    coding: list[CodingRead] = []


class GetCodeableConceptsResponse(ItemsResponseBase[CodeableConceptRead]):
    pass


class CodeableConceptCreate(CreateSchemaBase, CodeableConcept):
    pass


class CodeableConceptUpdate(UpdateSchemaBase, CodeableConcept):
    text: str | None = None


########################################################################################
# Observation Schemas
########################################################################################


class Status(StrEnum):
    FINAL = "final"
    PRELIMINARY = "preliminary"
    AMENDED = "amended"


class Observation(BaseSchema):
    status: Status

    effective_datetime_start: AwareDatetime
    effective_datetime_end: AwareDatetime
    issued: AwareDatetime | None = None

    value_quantity: float
    value_quantity_unit: str | None = None


class ObservationRead(ReadSchemaBase, Observation):
    category: list[CodeableConceptRead] = []
    code: CodeableConceptRead
    subject: PatientRead


class GetObservationsResponse(ItemsResponseBase[ObservationRead]):
    pass


class ObservationCreate(CreateSchemaBase, Observation):
    subject_id: uuid.UUID
    """Foreign key reference to the Patient id."""
    code_id: uuid.UUID
    """Foreign key reference to the CodeableConcept id."""
    category_ids: list[uuid.UUID] = []
    """Foreign key references to the CodeableConcept ids."""


class ObservationUpdate(UpdateSchemaBase, Observation):
    status: Status | None = None

    effective_datetime_start: AwareDatetime | None = None
    effective_datetime_end: AwareDatetime | None = None
    value_quantity: float | None = None

    code_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    category_ids: list[uuid.UUID] | None = None


class ObservationFilters(BaseSchema):
    subject_ids: list[uuid.UUID] = []
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None


########################################################################################
# Health Score Schemas
########################################################################################


class PopulationStatistics(BaseSchema):
    code: CodeType
    mean: float
    std: float
    min: float
    max: float
    count: int


PopulationStatisticsMap = dict[CodeType, PopulationStatistics]


class ValueScore(BaseSchema):
    """Score for a specific observation type."""

    code: str
    patient_avg: float
    population_avg: float
    score: float


class PatientMetrics(BaseSchema):
    observation_count: int
    observation_codes: list[CodeType]
    value_scores: list[ValueScore]
    consistency_score: float
