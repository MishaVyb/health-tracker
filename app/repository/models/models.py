from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Patient(Base):
    """
    Patient model.

    Simplified version of FHIR Patient resource.
    https://www.hl7.org/fhir/patient.html
    """

    name: Mapped[list[dict]]
    gender: Mapped[str | None]


class Coding(Base):
    """
    Coding model.

    Simplified version of FHIR Coding data type.
    https://www.hl7.org/fhir/datatypes-definitions.html#CodeableConcept.coding
    """

    system: Mapped[str]
    code: Mapped[str] = mapped_column(unique=True)
    display: Mapped[str | None]


class CodeableConcept(Base):
    """
    CodeableConcept model.

    Simplified version of FHIR CodeableConcept data type.
    https://www.hl7.org/fhir/datatypes.html#CodeableConcept
    """

    coding: Mapped[list[Coding]] = relationship(  # many-to-many
        secondary=lambda: CodeableConceptToCoding.__table__,
        viewonly=True,
        order_by=(Coding.system, Coding.code),
    )
    text: Mapped[str]


class Observation(Base):
    """
    Observation model.

    Simplified version of FHIR Observation resource.
    https://www.hl7.org/fhir/observation.html
    """

    status: Mapped[str]
    effective_datetime_start: Mapped[datetime]
    effective_datetime_end: Mapped[datetime]
    issued: Mapped[datetime | None]

    # relations:
    subject: Mapped[Patient] = relationship()
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Patient.id, ondelete="CASCADE"),
        index=True,
    )

    # NOTE: one-to-many and many-to-many relationships with CodeableConcept
    category: Mapped[list[CodeableConcept]] = relationship(
        secondary=lambda: CodeableConceptToObservation.__table__,
        viewonly=True,
        order_by=(CodeableConcept.text, CodeableConcept.id),
    )
    code: Mapped[CodeableConcept] = relationship()
    code_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(CodeableConcept.id, ondelete="CASCADE"),
        index=True,
    )

    value_quantity: Mapped[float]
    value_quantity_unit: Mapped[str | None]


class CodeableConceptToCoding(Base):
    """Association table for CodeableConcept to Coding relationship"""

    codeable_concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(CodeableConcept.id, ondelete="CASCADE"), index=True
    )
    coding_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Coding.id, ondelete="CASCADE"), index=True
    )
    __table_args__ = (UniqueConstraint(codeable_concept_id, coding_id),)


class CodeableConceptToObservation(Base):
    """Association table for CodeableConcept to Observation relationship"""

    codeable_concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(CodeableConcept.id, ondelete="CASCADE"), index=True
    )
    observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Observation.id, ondelete="CASCADE"), index=True
    )
    __table_args__ = (UniqueConstraint(codeable_concept_id, observation_id),)
