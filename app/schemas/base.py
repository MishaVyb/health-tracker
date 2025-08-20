import uuid
import warnings
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, RootModel
from pydantic.alias_generators import to_camel

# enable pydantic warning as error to not miss type mismatch
warnings.filterwarnings("error", r"Pydantic serializer warnings")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        populate_by_name=True,
        alias_generator=to_camel,
        use_attribute_docstrings=True,
        json_schema_serialization_defaults_required=True,
    )

    def __repr_args__(self):
        for k, v in super().__repr_args__():
            if k in self.model_fields_set and self.model_fields[k].repr:
                yield (k, v)


class ReadSchemaBase(BaseSchema):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class CreateSchemaBase(BaseSchema):
    pass


class UpdateSchemaBase(BaseSchema):
    pass


_T = TypeVar("_T", bound=BaseSchema)


class ItemsResponseBase(BaseSchema, Generic[_T]):
    items: list[_T]


# ???
class DictModel(RootModel[dict[str, Any]]):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(root=kwargs)

    def __getitem__(self, key: str) -> Any:
        return self.root[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.root[key] = value


EMPTY_PAYLOAD = BaseSchema()
