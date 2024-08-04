from typing import Any, Iterable, Optional, Union
import pytest
from plug_in.tools.introspect import contains_forward_refs


class A:
    pass


@pytest.mark.parametrize(
    "type_, expected",
    [
        (list, False),
        ("list", True),
        (dict[int, list[Any]], False),
        (dict[str, "A"], True),
        (list[tuple[dict[str, Union[int, "A"]]]], True),
        (list[tuple[dict[str, Optional["A"]]]], True),
        (list[tuple[dict[str, Iterable[Union[A, "str"]]]]], True),
        (list[tuple[dict[str, Iterable[Union["A", str]]]]], True),
        (list[tuple[dict[str, Iterable[Union[A, str]]]]], False),
    ],
)
def test_contains_forward_refs(type_: type, expected: bool):
    assert contains_forward_refs(type_) is expected
