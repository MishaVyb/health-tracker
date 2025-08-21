from app.schemas import schemas

BLOOD_PRESSURE_CONCEPT = schemas.CodeableConcept(
    text="Blood Pressure",
    coding=[
        schemas.Coding(
            system="http://loinc.org",
            code="85354-9",
            display="Blood Pressure",
        )
    ],
)
BLOOD_HEMOGLOBIN_CONCEPT = schemas.CodeableConcept(
    text="Hemoglobin",
    coding=[
        schemas.Coding(
            system="http://loinc.org",
            code="718-7",
            display="Hemoglobin",
        )
    ],
)
BLOOD_GLUCOSE_CONCEPT = schemas.CodeableConcept(
    text="Blood Glucose",
    coding=[
        schemas.Coding(
            system="http://loinc.org",
            code="2339-0",
            display="Blood Glucose",
        )
    ],
)

PHYSICAL_ACTIVITY_CONCEPT = schemas.CodeableConcept(
    text="Physical Activity",
    coding=[
        schemas.Coding(
            system="http://loinc.org",
            code="55423-8",
            display="Physical Activity",
        ),
    ],
)

SLEEP_ACTIVITY_CONCEPT = schemas.CodeableConcept(
    text="Sleep Activity",
    coding=[
        schemas.Coding(
            system="http://loinc.org",
            code="93832-4",
            display="Sleep duration",
        ),
    ],
)

HEALTH_SCORE_PANEL_CODING = schemas.Coding(
    system="http://loinc.org",
    code="LP29693-3",
    display="Health score panel",
)

HEALTH_ASSESSMENT_CODING = schemas.Coding(
    system="http://snomed.info/sct",
    code="386725007",
    display="Health assessment",
)

LABORATORY_CATEGORY_CODING = schemas.Coding(
    system="http://terminology.hl7.org/CodeSystem/v2-0074",
    code="LAB",
    display="Laboratory",
)


def get_codeable_concepts(kind: schemas.CodeKind) -> list[schemas.CodeableConcept]:
    if kind == schemas.CodeKind.BLOOD_TEST:
        return [BLOOD_GLUCOSE_CONCEPT, BLOOD_HEMOGLOBIN_CONCEPT]
    elif kind == schemas.CodeKind.PHYSICAL_ACTIVITY:
        return [PHYSICAL_ACTIVITY_CONCEPT]
    elif kind == schemas.CodeKind.SLEEP_ACTIVITY:
        return [SLEEP_ACTIVITY_CONCEPT]
    else:
        raise ValueError(f"Unknown code kind: {kind}")
