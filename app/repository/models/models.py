from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Patient(Base):
    """Patient model for health tracking"""

    name: Mapped[list[dict]]
    gender: Mapped[str | None]


class CodeableConcept(Base):
    """CodeableConcept model for health tracking"""

    code: Mapped[list[dict]]
    text: Mapped[str]


class Observation(Base):
    """Observation model for health tracking"""

    status: Mapped[str]
    effective_datetime_start: Mapped[datetime]
    effective_datetime_end: Mapped[datetime]
    issued: Mapped[datetime | None]

    # relations:
    category: Mapped[list[CodeableConcept]] = relationship()  # many-to-many

    code: Mapped[CodeableConcept] = relationship()
    code_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(CodeableConcept.id), index=True
    )

    subject: Mapped[Patient] = relationship()
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Patient.id), index=True)

    # TODO
    # value_quantity: Mapped[Quantity] = relationship()
    # reference_range: Mapped[list[ObservationReferenceRange]] = relationship()


class CodeableConceptToObservation(Base):
    """CodeableConcept to Observation model"""

    codeable_concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(CodeableConcept.id), index=True
    )
    observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Observation.id), index=True
    )
