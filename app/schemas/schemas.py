from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from .base import (
    BaseSchema,
    CreateSchemaBase,
    ItemsResponseBase,
    ReadSchemaBase,
    UpdateSchemaBase,
)


class ObservationStatus(StrEnum):
    FINAL = "final"
    PRELIMINARY = "preliminary"
    AMENDED = "amended"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


########################################################################################
# Patient Schemas
########################################################################################


class PatientBase(BaseSchema):
    name: list[dict] = []
    gender: Gender | None = None


class Patient(ReadSchemaBase, PatientBase):
    pass


class GetPatientsResponse(ItemsResponseBase[Patient]):
    pass


class PatientCreate(CreateSchemaBase, PatientBase):
    pass


class PatientUpdate(UpdateSchemaBase, PatientBase):
    pass


########################################################################################
# CodeableConcept Schemas
########################################################################################


class CodeableConceptBase(BaseSchema):
    text: str
    code: list[dict] = []


class CodeableConcept(ReadSchemaBase, CodeableConceptBase):
    pass


class GetCodeableConceptsResponse(ItemsResponseBase[CodeableConcept]):
    pass


class CodeableConceptCreate(CreateSchemaBase, CodeableConceptBase):
    pass


class CodeableConceptUpdate(UpdateSchemaBase, CodeableConceptBase):
    text: str | None = None


########################################################################################
# Observation Schemas
########################################################################################


class ObservationBase(BaseSchema):
    status: ObservationStatus
    effective_datetime_start: datetime
    effective_datetime_end: datetime
    issued: datetime | None = None


class Observation(ReadSchemaBase, ObservationBase):
    category: list[CodeableConcept] = []
    code: CodeableConcept
    subject: Patient


class GetObservationsResponse(ItemsResponseBase[Observation]):
    pass


class ObservationCreate(CreateSchemaBase, ObservationBase):
    # foreign key references for creation:
    code_id: uuid.UUID
    subject_id: uuid.UUID
    category_ids: list[uuid.UUID] = []


class ObservationUpdate(UpdateSchemaBase, ObservationBase):
    status: ObservationStatus | None = None
    effective_datetime_start: datetime | None = None
    effective_datetime_end: datetime | None = None
    issued: datetime | None = None
    code_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    category_ids: list[uuid.UUID] | None = None
