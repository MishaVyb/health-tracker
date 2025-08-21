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


class CodeKind(StrEnum):
    """Verbose name for a code identifier."""

    SLEEP_ACTIVITY = "sleep_activity"
    PHYSICAL_ACTIVITY = "physical_activity"
    BLOOD_TEST = "blood_test"


CodeType = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        description="Unique code.",
        examples=["4596-3", "29463-7"],
    ),
]


class Coding(BaseSchema):
    code: CodeType
    system: str
    display: str | None = None

    def __str__(self) -> str:
        return f"{self.code} ({self.display})"

    def __hash__(self) -> int:
        return hash(self.code)


class CodingRead(ReadSchemaBase, Coding):
    pass


class CodeableConcept(BaseSchema):
    text: str
    coding: list[Coding] = []

    def codes(self) -> tuple[CodeType, ...]:
        return tuple(c.code for c in self.coding)


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

    # relationships:
    subject_id: uuid.UUID | None = None
    """Foreign key reference to the Patient id."""
    code_id: uuid.UUID | None = None
    """Foreign key reference to the CodeableConcept id."""
    category_ids: list[uuid.UUID] | None = None
    """Foreign key references to the CodeableConcept ids."""


class ObservationFilters(BaseSchema):
    kinds: list[CodeKind] | None = None
    subject_ids: list[uuid.UUID] | None = None
    codes: list[CodeType] | None = None
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None


########################################################################################
# Diagnostic Report Schemas
########################################################################################


class ObservationQuantityStat(BaseSchema):
    """Statistics for an specific observation type."""

    mean: float
    """Average value for the observation type."""
    stdev: float
    """Standard deviation of the observation type."""
    min: float
    """Minimum value for the observation type."""
    max: float
    """Maximum value for the observation type."""
    count: int
    """Number of observations for the observation type."""


class PatientScoreStat(BaseSchema):
    coding: Coding

    population_stats: ObservationQuantityStat
    patient_stats: ObservationQuantityStat
    patient_score: Annotated[float, Field(ge=0, le=100)]
    """Patient score for this observation type."""

    def __str__(self) -> str:
        return f"{self.coding}: {self.patient_score} ({self.patient_stats} / {self.population_stats})"


ObservationQuantityStatMap = dict[Coding, ObservationQuantityStat]


class PatientMetrics(BaseSchema):
    observation_count: int
    observation_codes: list[Coding]
    observation_scores: list[PatientScoreStat]


class Reference(BaseSchema):
    reference: str
    type: str | None = None
    display: str | None = None


class Attachment(BaseSchema):
    contentType: str | None = None
    language: str | None = None
    data: bytes | None = None
    url: str | None = None
    size: int | None = None
    hash: bytes | None = None
    title: str | None = None
    creation: AwareDatetime | None = None


class Period(BaseSchema):
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None


class DiagnosticReport(BaseSchema):
    id: str | None = None
    status: Status
    code: CodeableConcept
    subject: Reference | None = None
    issued: AwareDatetime | None = None
    result: list[Reference] = []
    conclusion: str | None = None
    conclusion_code: list[CodeableConcept] = []
    category: list[CodeableConcept] = []
    presented_form: list[Attachment] = []
    effective_period: Period | None = None
