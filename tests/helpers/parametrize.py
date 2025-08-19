from typing import Any, Callable, Sequence

import pytest


class Param:
    """Helper to support kwarg values for `pytest.mark.parametrize`."""

    def __init__(
        self,
        id: str | None = None,
        marks: pytest.MarkDecorator | Sequence[pytest.MarkDecorator | pytest.Mark] = (),
        **kwargs,
    ) -> None:
        self.id = _normalize_test_description(id) if id else ""
        self.marks = marks
        self.kwargs = kwargs

    def build_param_id(self, index: int) -> str:
        return f"PARAM_{index}: {self.id}" if self.id else f"PARAM_{index}"

    def construct(self, index: int, keys: list[str]):
        if missing := set(self.kwargs) - set(keys):
            raise ValueError(
                f"Missing arguments: {missing}. "
                "Specify these keys at test function signature as KEYWORD_ONLY arguments. ",
            )
        return pytest.param(
            *[self.kwargs.get(k) for k in keys],
            id=self.build_param_id(index),
            marks=self.marks,
        )


class parametrize:
    """
    Helper decorator factory to support custom `Param` type.

    It works the same way as `pytest.mark.parametrize` does, but initializes
    parametrized argument names from `Param` kwargs.

    Argument names can be parametrized values or **fixture** overrides or even
    pure fixture function arguments. Docs:
    https://docs.pytest.org/en/stable/how-to/fixtures.html#override-a-fixture-with-direct-test-parametrization
    """

    def __init__(self, *params: Param) -> None:
        self.params = params

    def __call__(self, func: Callable) -> Any:
        keys = set()
        for param in self.params:
            keys |= set(param.kwargs)

        argnames = list(keys)
        params = [p.construct(i + 1, argnames) for i, p in enumerate(self.params)]
        return pytest.mark.parametrize(argnames, params)(func)


def _normalize_test_description(v: str, with_underscore: bool = False):
    lines = [l.strip() for l in v.split()]
    v = " ".join(lines)
    if with_underscore:
        v = v.replace(" ", "_").replace(".", "_")
    return v
