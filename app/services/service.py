import uuid
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Annotated

from fastapi import Depends

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
from app.schemas.schemas import Attachment, DiagnosticReport, Reference


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
        patient_obs = await self.get_observations(filters)
        if not patient_obs:
            raise HTTPBadRequestError(
                detail=f"No observations found for patient {filters.subject_ids}"
            )

        other_obs = await self.db.observations.get_where(
            clauses=((models.Observation.id.notin_(o.id for o in patient_obs)),)
        )

        self.logger.info(
            "Calculating health score depending on %s observations. "
            "Considering %s other observations as population statistics.",
            len(patient_obs),
            len(other_obs),
        )

        patient_stats = self._calculate_statistics_per_coding(patient_obs)
        all_stats = self._calculate_statistics_per_coding(patient_obs + other_obs)

        patient_metrics = self._calculate_metrics_per_coding(
            patient_obs, patient_stats, all_stats
        )
        patient_score = self._calculate_total_score(patient_metrics)

        diagnostic_report = self._construct_report(
            filters, patient, patient_metrics, patient_obs, patient_score
        )

        return diagnostic_report

    def _prepare_observations_per_coding(
        self, observations: list[schemas.ObservationRead]
    ) -> dict[schemas.Coding, list[float]]:
        res: dict[schemas.Coding, list[float]] = defaultdict(list)
        for obs in observations:
            for coding in obs.code.coding:
                res[coding].append(obs.value_quantity)
        return res

    def _calculate_statistics_per_coding(
        self, observations: list[schemas.ObservationRead]
    ) -> schemas.ObservationQuantityStatMap:
        """Calculate statistics for a list of observations."""

        res: schemas.ObservationQuantityStatMap = {}
        observations_per_code = self._prepare_observations_per_coding(observations)
        for code, values in observations_per_code.items():
            if len(values) > 1:
                res[code] = schemas.ObservationQuantityStat(
                    mean=round(mean(values), 4),  # average value
                    stdev=round(stdev(values), 4),  # standard deviation
                    min=round(min(values), 4),
                    max=round(max(values), 4),
                    count=len(values),
                )

            else:
                self.logger.warning(
                    "Not enough observations to calculate statistics for %s", code
                )

        return res

    def _calculate_metrics_per_coding(
        self,
        observations: list[schemas.ObservationRead],
        patient_stats: schemas.ObservationQuantityStatMap,
        population_stats: schemas.ObservationQuantityStatMap,
    ) -> schemas.PatientMetrics:
        """
        Calculate patient metrics depending on their observations and population
        statistics for each observation type separately.
        """

        scores: dict[schemas.Coding, schemas.PatientScoreStat] = {}
        for coding, population_stat in population_stats.items():
            if not (patient_stat := patient_stats.get(coding)):
                self.logger.warning("No patient statistics found for coding %s", coding)
                continue

            # calculate z-score (how many standard deviations from population mean)
            z_score = abs(
                (patient_stat.mean - population_stat.mean) / population_stat.stdev
            )
            # convert to a 0-100 score (lower z-score = better score)
            patient_score = max(
                0, 100 - (z_score * self.settings.SERVICE_SCORE_Z_SCALING_FACTOR)
            )

            scores[coding] = schemas.PatientScoreStat(
                coding=coding,
                patient_stats=patient_stat,
                population_stats=population_stat,
                patient_score=patient_score,
            )

        return schemas.PatientMetrics(
            observation_count=len(observations),
            observation_codes=list(scores.keys()),
            observation_scores=list(scores.values()),
        )

    def _calculate_total_score(self, metrics: schemas.PatientMetrics) -> float:
        """Calculate overall health score from individual metrics."""
        res = mean(score.patient_score for score in metrics.observation_scores)
        return round(res, 4)

    def _compose_conclusion(
        self,
        filters: schemas.ObservationFilters,
        patient: schemas.PatientRead,
        metrics: schemas.PatientMetrics,
        total_score: float,
    ) -> str:
        """Compose human-readable conclusion."""

        assignments_map = {
            4: "Excellent health data quality and consistency.",  # 80-100
            3: "Good health data with room for improvement.",  # 60-79
            2: "Moderate health data quality, consider additional monitoring.",  # 40-59
            1: "Limited health data quality, recommend increase activity.",  # 20-39
            0: "Inappropriate health score, instant actions are required.",  # 0-19
        }
        assessment = assignments_map[int((total_score - 1) // 20)]
        scores = "\n".join(map(str, metrics.observation_scores[:10]))
        return (
            f"Patient: {patient}\n"
            f"Period: {filters.start} - {filters.end}\n"
            f"Patient has {metrics.observation_count} total observations across {len(metrics.observation_codes)} different health metrics.\n"
            f"Health Score: {total_score}/100\n"
            f"Value scores per observation code (first 10): \n{scores}\n"
            f"Overall Assessment: {assessment}"
        )

    def _construct_report(
        self,
        filters: schemas.ObservationFilters,
        patient: schemas.PatientRead,
        metrics: schemas.PatientMetrics,
        observations: list[schemas.ObservationRead],
        total_score: float,
    ) -> DiagnosticReport:
        """Create a FHIR-compliant DiagnosticReport structure."""
        conclusion = self._compose_conclusion(filters, patient, metrics, total_score)

        diagnostic_report = DiagnosticReport(
            id=f"health-score-{filters.subject_ids[0]}",
            status=schemas.Status.FINAL,
            code=schemas.CodeableConcept(
                coding=[HEALTH_SCORE_PANEL_CODING],
                text="Comprehensive Health Score Assessment",
            ),
            subject=Reference(reference=str(filters.subject_ids[0]), type="Patient"),
            effective_period=schemas.Period(start=filters.start, end=filters.end),
            issued=datetime.now(timezone.utc),
            result=[
                Reference(reference=str(obs.id), type="Observation")
                for obs in observations
            ],
            conclusion=conclusion,
            conclusion_code=[
                schemas.CodeableConcept(
                    coding=[HEALTH_ASSESSMENT_CODING],
                    text="Health Score Assessment",
                ),
            ],
            category=[
                schemas.CodeableConcept(
                    coding=[LABORATORY_CATEGORY_CODING],
                    text="Health Assessment",
                ),
            ],
            presented_form=[
                Attachment(
                    contentType="text/plain",
                    data=conclusion.encode(),
                    title="Health Score Report",
                )
            ],
        )

        return diagnostic_report


HealthTrackerServiceDepends = Annotated[HealthTrackerService, Depends()]
