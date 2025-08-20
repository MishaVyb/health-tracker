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
HEMOGLOBIN_CONCEPT = schemas.CodeableConcept(
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
