from logging import Logger
from typing import Any
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from app.adapter.adapter import HealthTrackerAdapter
from app.adapter.external import ExternalFHIRAdapter
from app.dependencies.exceptions import HTTPException
from app.schemas import external, schemas

IdAdapter = TypeAdapter(UUID)
"""
Health Tracker uses UUIDs for patient and observation IDs.
It might be changed to strings in the future in order to have full FHIR compatibility.
"""


class HealthTrackerIntegration:
    """
    Integrate HealthTracker with external FHIR server.

    - Create patients in HealthTracker if they don't exist.
    - Update patients in HealthTracker if they exist.
    - Create codeable concepts in HealthTracker if they don't exist.
    - Create observations in HealthTracker if they don't exist.
    """

    def __init__(
        self,
        client: HealthTrackerAdapter,
        external: ExternalFHIRAdapter,
        *,
        logger: Logger,
        strict: bool = False,
    ) -> None:
        self.client = client
        self.external = external
        self.logger = logger
        self.strict = strict

    async def integrate(self) -> None:
        patients = await self.client.get_patients()
        patients_map = {p.id: p for p in patients.items}

        concepts = await self.client.get_codeable_concepts()
        concepts_map = {c.codes(): c for c in concepts.items}

        observations = await self.client.get_observations()
        observations_map = {o.id: o for o in observations.items}

        external_patients = await self.external.get_patients()
        external_observations = await self.external.get_observations()

        for ext in external_patients:
            try:
                await self.integrate_patient(patients_map, ext)
            except (HTTPException, ValidationError) as e:
                if self.strict:
                    raise
                self.logger.exception(f"Integration failed: {ext.id}. {e}")

        for ext in external_observations:
            try:
                await self.integrate_observation(
                    patients_map, observations_map, concepts_map, ext
                )
            except (HTTPException, ValidationError) as e:
                if self.strict:
                    raise
                self.logger.exception(f"Integration failed: {ext.id}. {e}")

    async def integrate_patient(
        self,
        patients_map: dict[UUID, schemas.PatientRead],
        external_patient: external.Patient,
    ) -> None:
        pk = IdAdapter.validate_python(external_patient.id)

        if pk in patients_map:
            self.logger.info(f"Updating patient {pk}")
            payload = schemas.PatientUpdate.model_validate(
                external_patient.model_dump()
            )
            await self.client.update_patient(pk, payload)
            patients_map[pk] = payload

        else:
            self.logger.info(f"Creating patient {pk}")
            payload = schemas.PatientCreate.model_validate(
                external_patient.model_dump()
            )
            await self.client.create_patient(payload)
            patients_map[pk] = payload

    async def integrate_observation(
        self,
        patients_map: dict[UUID, schemas.PatientRead],
        observations: dict[UUID, schemas.ObservationRead],
        concepts: dict[tuple[schemas.CodeType, ...], schemas.CodeableConceptRead],
        external_observation: external.Observation,
    ) -> None:
        pk = IdAdapter.validate_python(external_observation.id)
        if pk in observations:
            self.logger.warning(f"Observation exists: {pk}. Updating is not supported.")
            return

        code: external.CodeableConcept = external_observation.code
        if not code.coding:
            self.logger.warning(f"Observation {pk} has no coding. Skipping.")
            return

        concept_codes = tuple(c.code for c in code.coding)  # type: ignore[attr-defined]
        if not (concept := concepts.get(concept_codes)):
            self.logger.info(f"Creating codeable concept: {code.text}")
            payload = schemas.CodeableConceptCreate.model_validate(code.model_dump())
            concept = await self.client.create_codeable_concept(payload)
            concepts[concept_codes] = concept

        self.logger.info(f"Processing observation {pk}")
        data = self.integrate_observation_data(
            external_observation, concept, patients_map
        )
        if data is None:
            return

        self.logger.info(f"Creating observation {pk}")
        payload = schemas.ObservationCreate.model_validate(data)
        await self.client.create_observation(payload)

    def integrate_observation_data(
        self,
        source: external.Observation,
        concept: schemas.CodeableConceptRead,
        patients_map: dict[UUID, schemas.PatientRead],
    ) -> dict[str, Any] | None:
        # build payload with relationships as foreign keys:
        data = source.model_dump(exclude={"subject", "code", "category"})
        data["code_id"] = concept.id

        subject: external.Reference = source.subject
        subject_id = IdAdapter.validate_python(subject.reference)
        data["subject_id"] = subject_id

        if subject_id not in patients_map:
            self.logger.warning(
                f"Observation {source.id} has unknown subject {subject_id}. Skipping."
            )
            return None

        # map FHIR fields to internal schema
        # handle effective datetime
        if source.effectiveDateTime:
            effective_dt = source.effectiveDateTime
            data["effectiveDatetimeStart"] = effective_dt
            data["effectiveDatetimeEnd"] = effective_dt
        elif source.effectivePeriod:
            data["effectiveDatetimeStart"] = source.effectivePeriod.start
            data["effectiveDatetimeEnd"] = source.effectivePeriod.end
        else:
            # use issued time as fallback
            data["effectiveDatetimeStart"] = source.issued
            data["effectiveDatetimeEnd"] = source.issued

        # handle value quantity
        if source.valueQuantity:
            data["valueQuantity"] = source.valueQuantity.value
            data["valueQuantityUnit"] = source.valueQuantity.unit
        elif source.component:
            # for composite observations like blood pressure, use first component
            first_component: external.ObservationComponent = source.component[0]
            if first_component.valueQuantity:
                data["valueQuantity"] = first_component.valueQuantity.value
                data["valueQuantityUnit"] = first_component.valueQuantity.unit
        else:
            self.logger.warning(
                f"Observation {source.id} has no value quantity. Skipping."
            )
            return None

        return data
