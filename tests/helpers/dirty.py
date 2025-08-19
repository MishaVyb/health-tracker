from typing import Any

import dirty_equals
from pydantic import BaseModel


class IsPartialSchema(dirty_equals.IsPartialDict):
    def __init__(
        self, expected: dict[Any, Any] | BaseModel | None = None, **expected_kwargs: Any
    ):
        if isinstance(expected, BaseModel):
            expected = expected.model_dump(exclude_unset=True)
        if expected and expected_kwargs:
            super().__init__(**expected, **expected_kwargs)  # merge expected kwargs
        elif expected:
            super().__init__(expected)
        else:
            super().__init__(**expected_kwargs)

    def equals(self, other: dict | BaseModel) -> bool:
        data = self.use_result(other)
        return super().equals(data)

    def use_result(self, other: dict | BaseModel):
        if not isinstance(other, BaseModel):
            return other
        result_data = other.model_dump()

        # supports for model properties, etc
        for attr in self.expected_values:
            if attr not in other.model_fields:
                try:
                    result_data[attr] = getattr(other, attr)
                except AttributeError:
                    pass

        return result_data

    def get_operands(self, other: dict | BaseModel | Any):
        if isinstance(other, BaseModel):
            other = self.use_result(other)

        elif not isinstance(other, dict):
            return self.expected_values, other

        values = self.expected_values
        if self.partial:
            other = {k: v for k, v in other.items() if k in values}
        if self.ignore:
            values = self._filter_dict(self.expected_values)
            other = self._filter_dict(other)
        return values, other
