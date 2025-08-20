import uuid
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Annotated

from fastapi import Depends
from fhir.resources.attachment import Attachment
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.reference import Reference

from app.dependencies.dependencies import AppSettingsDepends
from app.dependencies.exceptions import HTTPBadRequestError
from app.dependencies.logging import LoggerDepends
from app.repository.models import models
from app.repository.repositories import DatabaseRepositoriesDepends
from app.schemas import schemas
from app.schemas.base import EMPTY_PAYLOAD
from app.schemas.constants import (
    HEALTH_ASSESSMENT_CODING,
    HEALTH_SCORE_PANEL_CODING,
    LABORATORY_CATEGORY_CODING,
)


class HealthTrackerService:
    def __init__(
        self,
        db: DatabaseRepositoriesDepends,
        logger: LoggerDepends,
        settings: AppSettingsDepends,
    ) -> None:
        self.db = db
        self.logger = logger
        self.settings = settings

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

    async def get_observations(
        self, filters: schemas.ObservationFilters
    ) -> list[schemas.ObservationRead]:
        return await self.db.observations.get_where(filters)

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

    ########################################################################################
    # Health Score Calculation
    ########################################################################################

    async def get_health_score(
        self, filters: schemas.ObservationFilters
    ) -> DiagnosticReport:
        patient = await self.get_patient(filters.subject_ids[0])
        patient_observations = await self.get_observations(filters)
        if not patient_observations:
            raise HTTPBadRequestError(
                detail=f"No observations found for patient {filters.subject_ids}"
            )

        other_observations = await self.db.observations.get_where(
            clauses=(
                (models.Observation.id.notin_(o.id for o in patient_observations)),
            )
        )

        self.logger.info(
            "Calculating health score depending on %s observations. "
            "Considering %s other observations as population statistics.",
            len(patient_observations),
            len(other_observations),
        )

        stats = self._calculate_statistics(patient_observations + other_observations)
        patient_metrics = self._calculate_metrics(patient_observations, stats)
        patient_score = self._calculate_score(patient_metrics)

        # Create FHIR DiagnosticReport structure
        diagnostic_report = self._construct_report(
            filters, patient, patient_score, patient_metrics, patient_observations
        )

        return diagnostic_report

    def _prepare_observations_values(
        self, observations: list[schemas.ObservationRead]
    ) -> dict[schemas.CodeType, list[float]]:
        res: dict[schemas.CodeType, list[float]] = defaultdict(list)
        for obs in observations:
            for coding in obs.code.coding:
                res[coding.code].append(obs.value_quantity)
        return res

    def _calculate_statistics(
        self, observations: list[schemas.ObservationRead]
    ) -> schemas.PopulationStatisticsMap:
        """Calculate population statistics for a list of observations."""

        res: schemas.PopulationStatisticsMap = {}
        observations_per_code = self._prepare_observations_values(observations)
        for code, values in observations_per_code.items():
            if len(values) > 1:
                res[code] = schemas.PopulationStatistics(
                    code=code,
                    mean=mean(values),
                    std=stdev(values),
                    min=min(values),
                    max=max(values),
                    count=len(values),
                )

        return res

    def _calculate_metrics(
        self,
        observations: list[schemas.ObservationRead],
        stats: schemas.PopulationStatisticsMap,
    ) -> schemas.PatientMetrics:
        """Calculate metrics for a patient depending on their observations and population statistics."""

        # Calculate value scores for each observation type
        value_scores: dict[schemas.CodeType, schemas.ValueScore] = {}
        observations_per_code = self._prepare_observations_values(observations)
        for code, values in observations_per_code.items():
            if pop_stats := stats.get(code):
                avg_value = pop_stats.mean

                # Calculate z-score (how many standard deviations from mean)
                z_score = abs((avg_value - pop_stats.mean) / pop_stats.std)
                # Convert to a 0-100 score (lower z-score = better score)
                value_score = max(0, 100 - (z_score * 20))

                value_scores[code] = schemas.ValueScore(
                    code=code,
                    patient_avg=avg_value,
                    population_avg=pop_stats.mean,
                    score=value_score,
                )

        # Calculate consistency score (how consistent the patient's values are)
        values = [obs.value_quantity for obs in observations]

        # Lower coefficient of variation = more consistent
        cv = stdev(values) / mean(values)  # ??? zero division
        consistency_score = max(0, 100 - (cv * 50))

        return schemas.PatientMetrics(
            observation_count=len(observations),
            observation_codes=list(observations_per_code.keys()),
            value_scores=list(value_scores.values()),
            consistency_score=consistency_score,
        )

    def _calculate_score(self, metrics: schemas.PatientMetrics) -> float:
        """
        Calculate overall health score from individual metrics. Considering:
        - observation coverage
        - value quality
        - consistency
        """
        res = 0

        # Observation coverage score (0-100)
        score = min(100, len(metrics.observation_codes) * 20)
        res += score * self.settings.SERVICE_SCORE_WEIGHT_OBSERVATION_COVERAGE

        # Value quality score (average of individual value scores)
        if metrics.value_scores:
            score = mean(score.score for score in metrics.value_scores)
            res += score * self.settings.SERVICE_SCORE_WEIGHT_VALUE_QUALITY

        # Consistency score (already 0-100)
        res += metrics.consistency_score * self.settings.SERVICE_SCORE_WEIGHT_CONS

        return round(res, 2)

    def _compose_conclusion(
        self,
        filters: schemas.ObservationFilters,
        patient: schemas.PatientRead,
        health_score: float,
        metrics: schemas.PatientMetrics,
    ) -> str:
        """Compose human-readable conclusion."""

        assignments_map = {
            4: "Excellent health data quality and consistency.",  # 80-100
            3: "Good health data with room for improvement.",  # 60-79
            2: "Moderate health data quality, consider additional monitoring.",  # 40-59
            1: "Limited health data quality, recommend increase activity.",  # 20-39
            0: "Inappropriate health score, instant actions are required.",  # 0-19
        }
        overall_assessment = assignments_map[int(health_score // 20)]

        return f"""
            Patient: {patient}
            Period: {filters.start} - {filters.end}

            Patient has {metrics.observation_count} total observations across {len(metrics.observation_codes)} different health metrics.
            Health Score: {health_score}/100
            Value scores: {metrics.value_scores}
            Consistency score: {metrics.consistency_score}/100

            Overall Assessment: {overall_assessment}
        """

    def _construct_report(
        self,
        filters: schemas.ObservationFilters,
        patient: schemas.PatientRead,
        health_score: float,
        metrics: schemas.PatientMetrics,
        observations: list[schemas.ObservationRead],
    ) -> DiagnosticReport:
        """Create a FHIR-compliant DiagnosticReport structure."""
        conclusion = self._compose_conclusion(filters, patient, health_score, metrics)

        diagnostic_report = DiagnosticReport(
            id=f"health-score-{filters.subject_ids[0]}",
            status=schemas.Status.FINAL,
            code=schemas.CodeableConcept(
                coding=[HEALTH_SCORE_PANEL_CODING],
                text="Comprehensive Health Score Assessment",
            ).model_dump(),
            subject=Reference(
                reference=f"Patient/{filters.subject_ids[0]}", type="Patient"
            ),
            issued=datetime.now(timezone.utc),
            result=[
                Reference(reference=f"Observation/{obs.id}", type="Observation")
                for obs in observations
            ],
            conclusion=conclusion,
            conclusionCode=[
                schemas.CodeableConcept(
                    coding=[HEALTH_ASSESSMENT_CODING],
                    text="Health Score Assessment",
                ).model_dump(),
            ],
            category=[
                schemas.CodeableConcept(
                    coding=[LABORATORY_CATEGORY_CODING],
                    text="Health Assessment",
                ).model_dump(),
            ],
            presentedForm=[
                Attachment(
                    contentType="text/plain",
                    data=conclusion.encode(),
                    title="Health Score Report",
                )
            ],
        )

        return diagnostic_report


HealthTrackerServiceDepends = Annotated[HealthTrackerService, Depends()]
