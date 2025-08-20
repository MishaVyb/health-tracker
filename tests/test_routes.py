import uuid

import pytest

from app.client.client import HealthTrackerAdapter
from app.dependencies.exceptions import HTTPBadRequestError, HTTPNotFoundError
from app.schemas import schemas
from tests.conftest import TEST_DT


async def test_patient_crud(client: HealthTrackerAdapter) -> None:
    create_payload = schemas.PatientCreate(
        name=[schemas.HumanName(family="INITIAL_FAMILY", given=["INITIAL_GIVEN"])],
        gender=schemas.HumanGender.MALE,
    )

    result = await client.create_patient(create_payload)
    assert result.id
    assert result.name == create_payload.name
    assert result.gender == create_payload.gender

    assert result == await client.get_patient(result.id)
    assert result == (await client.get_patients()).items[0]

    update_payload = schemas.PatientUpdate(
        name=[schemas.HumanName(family="NEW_FAMILY", given=["NEW_GIVEN"])]
    )

    result = await client.update_patient(result.id, update_payload)
    assert result.name == update_payload.name
    assert result.gender == create_payload.gender  # left unchanged

    assert result == await client.get_patient(result.id)
    assert result == (await client.get_patients()).items[0]

    await client.delete_patient(result.id)
    with pytest.raises(HTTPNotFoundError):
        assert await client.get_patient(result.id)
    assert (await client.get_patients()).items == []


async def test_codeable_concept_crud(client: HealthTrackerAdapter) -> None:
    create_payload = schemas.CodeableConceptCreate(
        text="TEST_CONCEPT_1",
        coding=[schemas.Coding(system="TEST_SYSTEM", code="1")],
    )

    result = await client.create_codeable_concept(create_payload)
    assert result.id
    assert result.text == create_payload.text
    assert result.coding[0].code == create_payload.coding[0].code

    update_payload = schemas.CodeableConceptUpdate(
        text="NEW_TEXT",
    )
    result = await client.update_codeable_concept(result.id, update_payload)
    assert result.text == update_payload.text
    assert result.coding[0].code == create_payload.coding[0].code  # left unchanged

    assert result == await client.get_codeable_concept(result.id)
    assert result == (await client.get_codeable_concepts()).items[0]

    # 4xx errors:
    with pytest.raises(HTTPNotFoundError):
        await client.get_codeable_concept(uuid.uuid4())
    with pytest.raises(HTTPNotFoundError):
        await client.update_codeable_concept(uuid.uuid4(), update_payload)

    # nested relationship update currently is not supported:
    with pytest.raises(HTTPBadRequestError):
        await client.update_codeable_concept(
            result.id,
            schemas.CodeableConceptUpdate(
                coding=[schemas.Coding(system="TEST_SYSTEM", code="2")]
            ),
        )

    # delete:
    await client.delete_codeable_concept(result.id)
    with pytest.raises(HTTPNotFoundError):
        assert await client.get_codeable_concept(result.id)
    assert (await client.get_codeable_concepts()).items == []


@pytest.mark.usefixtures("init_concepts")
async def test_observation_crud(
    client: HealthTrackerAdapter, patient: schemas.PatientRead
) -> None:
    codeable_concepts = (await client.get_codeable_concepts()).items
    code = codeable_concepts[0]
    categories = codeable_concepts[1:]
    create_payload = schemas.ObservationCreate(
        status=schemas.ObservationStatus.PRELIMINARY,
        effective_datetime_start=TEST_DT,
        effective_datetime_end=TEST_DT,
        issued=TEST_DT,
        value_quantity=100,
        value_quantity_unit="mg/dL",
        # relations:
        subject_id=patient.id,
        code_id=code.id,
        category_ids=[c.id for c in categories],
    )

    result = await client.create_observation(create_payload)
    assert result.id
    assert result.status == create_payload.status
    assert result.effective_datetime_start == create_payload.effective_datetime_start
    assert result.effective_datetime_end == create_payload.effective_datetime_end
    assert result.issued == create_payload.issued
    assert result.value_quantity == create_payload.value_quantity
    assert result.value_quantity_unit == create_payload.value_quantity_unit
    assert result.subject == patient
    assert result.code == code
    assert result.category == categories

    assert result == await client.get_observation(result.id)
    assert result == (await client.get_observations()).items[0]

    code = codeable_concepts[1]  # update codeable concept relationship
    categories = codeable_concepts[2:]  # update codeable concept relationship
    update_payload = schemas.ObservationUpdate(
        status=schemas.ObservationStatus.FINAL,
        value_quantity=200,
        code_id=code.id,
        category_ids=[c.id for c in categories],
    )

    result = await client.update_observation(result.id, update_payload)
    assert result.status == update_payload.status
    assert result.value_quantity == update_payload.value_quantity
    assert result.code == code
    assert result.category == categories
    assert result.issued == create_payload.issued  # left unchanged
    assert result.subject == patient  # left unchanged

    assert result == await client.get_observation(result.id)
    assert result == (await client.get_observations()).items[0]

    # 4xx errors:
    with pytest.raises(HTTPNotFoundError):
        await client.get_observation(uuid.uuid4())
    with pytest.raises(HTTPNotFoundError):
        await client.update_observation(uuid.uuid4(), update_payload)
    with pytest.raises(HTTPNotFoundError):
        await client.update_observation(
            result.id,
            schemas.ObservationUpdate(category_ids=[uuid.uuid4()]),
        )

    # delete:
    await client.delete_observation(result.id)
    with pytest.raises(HTTPNotFoundError):
        assert await client.get_observation(result.id)
    assert (await client.get_observations()).items == []
