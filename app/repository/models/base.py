from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic.alias_generators import to_snake
from sqlalchemy import JSON, DateTime, MetaData, engine, types
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.orm.exc import DetachedInstanceError


# NOTE workaround fro SQLAlchemy and SQLite issue
# https://github.com/sqlalchemy/sqlalchemy/issues/1985
class _DateTimeForceTimezone(types.TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(
        self,
        value: datetime | None,
        dialect: engine.interfaces.Dialect,
    ):
        if value and isinstance(dialect, SQLiteDialect):
            return value.replace(tzinfo=timezone.utc)
        return value


# # UNUSED
# # NOTE: enforce storing python value as simple string
# class ForceString(types.TypeDecorator):
#     impl = String
#     cache_ok = True

#     def process_bind_param(self, value: Any | None, dialect: engine.interfaces.Dialect):
#         if value:
#             return str(value)
#         return value


# class DatabaseStringEnum(types.TypeDecorator):
#     impl = String()
#     cache_ok = True

#     def __init__(self, enum_class: Type[StrEnum], *args: Any, **kwargs: Any) -> None:
#         self._enum_class = enum_class
#         super().__init__(*args, **kwargs)

#     def process_bind_param(
#         self,
#         value: Any | None,
#         dialect: engine.interfaces.Dialect,
#     ) -> None | str:
#         if value is None:
#             return value
#         return str(value)

#     def process_result_value(
#         self,
#         value: Any | None,
#         dialect: engine.interfaces.Dialect,
#     ) -> None | StrEnum:
#         if value is None:
#             return value
#         return self._enum_class(value)


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    type_annotation_map = {
        datetime: _DateTimeForceTimezone(),
        dict: JSON,  # NOTE: JSONB is used for PostgreSQL (see Alembic migrations)
        list: JSON,
        list[dict]: JSON,
    }

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=lambda: uuid.uuid4(),
    )

    def __repr__(self) -> str:
        try:
            return f"<{self.__class__.__name__}({self.id=})>"
        except DetachedInstanceError:
            return f"<{self.__class__.__name__}(detached)>"

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return to_snake(cls.__name__)
