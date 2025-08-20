import time
from dataclasses import dataclass, field
from functools import cache
from typing import Any, ClassVar, Generic, Sequence, Type, TypeAlias, TypeVar

from pydantic import BaseModel as BaseSchema
from pydantic import TypeAdapter
from sqlalchemy import ColumnExpressionArgument, Select, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.interfaces import ORMOption

from app.dependencies.dependencies import SessionDepends
from app.dependencies.logging import LoggerDepends

from .models import Base

ModelType = TypeVar("ModelType", bound=Base)
PrimaryKeyType = TypeVar("PrimaryKeyType")
SchemaType = TypeVar("SchemaType", bound=BaseSchema)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseSchema)


class SQLAlchemyRepositoryBase(
    Generic[ModelType, PrimaryKeyType, SchemaType, CreateSchemaType, UpdateSchemaType],
):
    """Pydantic oriented database repository on top of SQLAlchemy."""

    _model: ClassVar[Type[ModelType]]
    _schema: ClassVar[Type[SchemaType]]

    @dataclass(kw_only=True)
    class SelectContext:
        # where:
        filters_schema: BaseSchema | None = None
        extra_filters: dict = field(default_factory=dict)
        clauses: Sequence[ColumnExpressionArgument] = ()

        # options:
        cached: bool = False
        loading_options: tuple[ORMOption, ...] = ()

    def __init__(self, session: SessionDepends, logger: LoggerDepends) -> None:
        self._session = session
        self._logger = logger

    @classmethod
    @cache
    def database_fieldnames(cls) -> set[str]:
        """
        Returns table fieldnames for `SQLAlchemyRepositoryBase` processing.

        By default takes all sqlalchemy model attributes except relationships
        (i.e. `columns` + `hybrid_properties`).
        """
        i = inspect(cls._model)
        return set(i.all_orm_descriptors.keys()) - set(i.relationships.keys())

    async def get(self, pk: PrimaryKeyType, *, cached: bool = False) -> SchemaType:
        """Get one instance by PK. Using cached or querying database."""
        ctx = self.SelectContext(extra_filters=dict(id=pk), cached=cached)
        instance = await self._get_instance_by_id(pk, cached=cached)
        return self._use_result(instance, ctx=ctx)

    async def get_one(self, *, cached: bool = False, **filters) -> SchemaType:
        """
        Get one instance by filters/clauses.
        """
        ctx = self.SelectContext(
            extra_filters=filters,
            cached=cached,
        )
        stm = self._build_select_statement(ctx=ctx)
        instance = await self._get_instance(stm, ctx=ctx)
        return self._use_result(instance, ctx=ctx)

    async def get_one_or_none(
        self,
        *,
        cached: bool = False,
        **filters,
    ) -> SchemaType | None:
        try:
            return await self.get_one(cached=cached, **filters)
        except NoResultFound:
            return None

    async def get_all(
        self,
        *,
        cached: bool = False,
    ) -> list[SchemaType]:
        return await self.get_where(
            cached=cached,
        )

    async def get_where(
        self,
        filters_schema: BaseSchema | None = None,
        *,
        cached: bool = False,
        clauses: Sequence[ColumnExpressionArgument] = (),
        **extra_filters,
    ) -> list[SchemaType]:
        """
        Get many instances using filters.
        """
        ctx = self.SelectContext(
            filters_schema=filters_schema,
            extra_filters=extra_filters,
            clauses=clauses,
            cached=cached,
        )
        stm = self._build_select_statement(ctx=ctx)
        items = await self._get_instances_list(stm, ctx=ctx)
        return self._use_results_list(items, ctx=ctx)

    async def _get_instance_by_id(
        self,
        pk: PrimaryKeyType,
        *,
        cached: bool = False,
    ) -> ModelType:
        if cached:
            return await self._session.get_one(self._model, pk)

        # re-fetch instance:
        ctx = self.SelectContext(extra_filters=dict(id=pk), cached=cached)
        stm = self._build_select_statement(ctx=ctx)
        return await self._get_instance(stm, ctx=ctx)

    async def _get_instance(self, stm: Select, *, ctx: SelectContext) -> ModelType:
        t1 = time.time()
        r = await self._session.execute(stm)
        instance = r.scalar_one()
        self._logger.info("[DATABASE] Got: %s [%.3f]", instance, time.time() - t1)
        return instance

    async def _get_instances_list(
        self, stm: Select, *, ctx: SelectContext
    ) -> Sequence[ModelType]:
        t1 = time.time()
        res = await self._session.execute(stm)
        items = res.scalars().all()
        self._logger.info(
            "[DATABASE] Got: %s [%.3f]",
            (
                [str(i) for i in items]
                if 0 < len(items) and len(items) < 5
                else f"{len(items)} {self} items"
            ),
            time.time() - t1,
        )
        return items

    async def create(
        self,
        payload: CreateSchemaType,
        refresh: bool = False,
        **extra_values,
    ) -> SchemaType:
        data = self._use_payload_create(payload, **extra_values)
        instance = self._model(**data)
        self._logger.debug("[DATABASE] Add and flush: %s", instance)
        self._session.add(instance)
        await self._session.flush([instance])
        if refresh:
            instance = await self._get_instance_by_id(instance.id, cached=False)
        return self._use_result(instance)

    async def pending_create(
        self,
        payload: CreateSchemaType,
        **extra_values,
    ) -> None:
        data = self._use_payload_create(payload, **extra_values)
        instance = self._model(**data)
        self._logger.debug("[DATABASE] Add: %s", instance)
        self._session.add(instance)

    async def update(
        self,
        pk: PrimaryKeyType,
        payload: UpdateSchemaType | None,
        refresh: bool = False,
        **extra_values,
    ) -> SchemaType:
        data = self._use_payload_update(payload, **extra_values)
        instance = await self._get_instance_by_id(pk)
        if not data:
            return self._use_result(instance)

        self._logger.debug("[DATABASE] Update and flush: %s", instance)
        for k, v in data.items():
            setattr(instance, k, v)

        await self._session.flush([instance])

        if refresh:
            instance = await self._get_instance_by_id(instance.id, cached=False)
        return self._use_result(instance)

    async def pending_update(
        self,
        pk: PrimaryKeyType,
        payload: UpdateSchemaType | None,
        **extra_values,
    ) -> None:
        data = self._use_payload_update(payload, **extra_values)
        instance = await self._get_instance_by_id(pk)
        if not data:
            return

        self._logger.debug("[DATABASE] Update: %s", instance)
        for k, v in data.items():
            setattr(instance, k, v)

    async def delete(self, pk: PrimaryKeyType, flush: bool = False) -> None:
        instance = await self._get_instance_by_id(pk)

        self._logger.debug("[DATABASE] Delete: %s", instance)
        await self._session.delete(instance)
        if flush:
            await self._session.flush([instance])

    def _use_payload_create(
        self, payload: CreateSchemaType | UpdateSchemaType, **extra_values
    ) -> dict:
        fieldnames = self.database_fieldnames()
        extra_values = {k: v for k, v in extra_values.items() if k in fieldnames}
        extra_values |= self._use_payload_create_defaults(
            payload, exclude=set(extra_values)
        )

        # HACK:
        # sqlalchemy expire all many-to-many / one-to-many relationship on flush
        # if it's not set explicitly on model creation as empty list
        # (obviously, for just created instance, all its list relationships are empty)
        ensure_empty_list_relationships: dict = {
            k: []
            for k, v in inspect(self.__class__._model).relationships.items()
            if v.uselist
        }
        return self._use_payload(
            payload, **extra_values, **ensure_empty_list_relationships
        )

    def _use_payload_create_defaults(
        self, payload: CreateSchemaType | UpdateSchemaType, exclude: set[str]
    ) -> dict[str, Any]:
        fieldnames = self.database_fieldnames()
        defaults = {}
        for fieldname, field in payload.model_fields.items():
            if (
                fieldname in fieldnames
                and fieldname not in exclude
                and fieldname not in payload.model_fields_set
            ):
                default = field.get_default(call_default_factory=True)
                if default is not None:
                    defaults[fieldname] = default
        return defaults

    def _use_payload_update(
        self, payload: CreateSchemaType | UpdateSchemaType | None, **extra_values
    ) -> dict:
        fieldnames = self.database_fieldnames()
        extra_values = {k: v for k, v in extra_values.items() if k in fieldnames}
        return self._use_payload(payload, **extra_values)

    def _use_payload(
        self,
        payload: CreateSchemaType | UpdateSchemaType | None,
        **extra_values,
    ) -> dict:
        if not payload:
            return extra_values

        payload_fields = payload.model_fields_set & self.database_fieldnames()
        payload_values = payload.model_dump(include=payload_fields)
        return payload_values | extra_values

    def _build_select_statement(
        self,
        stm: Select | None = None,
        *,
        ctx: SelectContext,
    ) -> Select:
        self._logger.info("[DATABASE] Querying %s %s. ", self, ctx)

        stm = stm if stm is not None else select(self._model)
        stm = self._apply_filters(stm, ctx=ctx)
        stm = self._apply_loading_options(stm, ctx=ctx)
        stm = self._apply_execution_options(stm, ctx=ctx)
        stm = self._apply_order(stm, ctx=ctx)
        return stm

    def _apply_filters(
        self,
        stm: Select,
        *,
        ctx: SelectContext,
    ) -> Select:
        filters: dict[str, Any] = {}
        if ctx.filters_schema:
            filters |= ctx.filters_schema.model_dump(exclude_unset=True)

        filters |= ctx.extra_filters
        filters = {k: v for k, v in filters.items() if k in self.database_fieldnames()}

        return stm.filter_by(**filters).where(*ctx.clauses)

    def _apply_loading_options(self, stm: Select, *, ctx: SelectContext) -> Select:
        return stm.options(*ctx.loading_options)

    def _apply_execution_options(self, stm: Select, *, ctx: SelectContext) -> Select:
        return stm.execution_options(populate_existing=not ctx.cached)

    def _apply_order(self, stm: Select, *, ctx: SelectContext) -> Select:
        return stm.order_by(self._model.id)

    # @overload
    # def _use_result(
    #     self,
    #     instance: ModelType,
    #     *,
    #     ctx: SelectContext | None = None,
    #     adapter: None = None,
    # ) -> SchemaType:
    #     ...

    # @overload
    # def _use_result(
    #     self,
    #     instance: Sequence[ModelType],
    #     *,
    #     ctx: SelectContext | None = None,
    #     adapter: TypeAdapter[list[SchemaType]],
    # ) -> list[SchemaType]:
    #     ...

    def _use_result(
        self,
        instance: ModelType | Sequence[ModelType],
        *,
        ctx: SelectContext | None = None,
        adapter: TypeAdapter[list[SchemaType]] | None = None,
    ) -> SchemaType | list[SchemaType]:
        adapter = adapter or TypeAdapter(self._schema)
        return adapter.validate_python(instance, from_attributes=True)

    def _use_results_list(
        self,
        instances: Sequence[ModelType],
        *,
        ctx: SelectContext | None = None,
    ) -> list[SchemaType]:
        schema: TypeAlias = self._schema  # type: ignore
        adp = TypeAdapter(list[schema])
        return self._use_result(instances, adapter=adp, ctx=ctx)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def __str__(self) -> str:
        return repr(self._model.__tablename__)
