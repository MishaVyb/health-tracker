"""initial

Revision ID: 10810ad48c83
Revises:
Create Date: 2025-08-20 16:32:46.709765

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "10810ad48c83"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "codeable_concept",
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_codeable_concept")),
    )
    op.create_table(
        "coding",
        sa.Column("system", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("display", sa.String(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coding")),
        sa.UniqueConstraint("code", name=op.f("uq_coding_code")),
    )
    op.create_table(
        "patient",
        sa.Column("name", JSONB, nullable=False),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patient")),
    )
    op.create_table(
        "codeable_concept_to_coding",
        sa.Column("codeable_concept_id", sa.Uuid(), nullable=False),
        sa.Column("coding_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["codeable_concept_id"],
            ["codeable_concept.id"],
            name=op.f(
                "fk_codeable_concept_to_coding_codeable_concept_id_codeable_concept"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["coding_id"],
            ["coding.id"],
            name=op.f("fk_codeable_concept_to_coding_coding_id_coding"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_codeable_concept_to_coding")),
        sa.UniqueConstraint(
            "codeable_concept_id",
            "coding_id",
            name=op.f("uq_codeable_concept_to_coding_codeable_concept_id"),
        ),
    )
    op.create_index(
        op.f("ix_codeable_concept_to_coding_codeable_concept_id"),
        "codeable_concept_to_coding",
        ["codeable_concept_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_codeable_concept_to_coding_coding_id"),
        "codeable_concept_to_coding",
        ["coding_id"],
        unique=False,
    )
    op.create_table(
        "observation",
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "effective_datetime_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "effective_datetime_end",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "issued",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("code_id", sa.Uuid(), nullable=False),
        sa.Column("value_quantity", sa.Float(), nullable=False),
        sa.Column("value_quantity_unit", sa.String(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["code_id"],
            ["codeable_concept.id"],
            name=op.f("fk_observation_code_id_codeable_concept"),
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["patient.id"],
            name=op.f("fk_observation_subject_id_patient"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observation")),
    )
    op.create_index(
        op.f("ix_observation_code_id"), "observation", ["code_id"], unique=False
    )
    op.create_index(
        op.f("ix_observation_subject_id"), "observation", ["subject_id"], unique=False
    )
    op.create_table(
        "codeable_concept_to_observation",
        sa.Column("codeable_concept_id", sa.Uuid(), nullable=False),
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["codeable_concept_id"],
            ["codeable_concept.id"],
            name=op.f(
                "fk_codeable_concept_to_observation_codeable_concept_id_codeable_concept"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observation.id"],
            name=op.f("fk_codeable_concept_to_observation_observation_id_observation"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_codeable_concept_to_observation")),
        sa.UniqueConstraint(
            "codeable_concept_id",
            "observation_id",
            name=op.f("uq_codeable_concept_to_observation_codeable_concept_id"),
        ),
    )
    op.create_index(
        op.f("ix_codeable_concept_to_observation_codeable_concept_id"),
        "codeable_concept_to_observation",
        ["codeable_concept_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_codeable_concept_to_observation_observation_id"),
        "codeable_concept_to_observation",
        ["observation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_codeable_concept_to_observation_observation_id"),
        table_name="codeable_concept_to_observation",
    )
    op.drop_index(
        op.f("ix_codeable_concept_to_observation_codeable_concept_id"),
        table_name="codeable_concept_to_observation",
    )
    op.drop_table("codeable_concept_to_observation")
    op.drop_index(op.f("ix_observation_subject_id"), table_name="observation")
    op.drop_index(op.f("ix_observation_code_id"), table_name="observation")
    op.drop_table("observation")
    op.drop_index(
        op.f("ix_codeable_concept_to_coding_coding_id"),
        table_name="codeable_concept_to_coding",
    )
    op.drop_index(
        op.f("ix_codeable_concept_to_coding_codeable_concept_id"),
        table_name="codeable_concept_to_coding",
    )
    op.drop_table("codeable_concept_to_coding")
    op.drop_table("patient")
    op.drop_table("coding")
    op.drop_table("codeable_concept")
