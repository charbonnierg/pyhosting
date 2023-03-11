import typing as t
from re import escape

import pytest

from synopsys.core.events import DEFAULT_SYNTAX
from synopsys.core.utils import render_subject


@pytest.mark.parametrize(
    "tokens,placeholders,context,result",
    [
        (["test"], {}, {}, "test"),
        (["test"], {}, {"extra": "ignored"}, "test"),
        (["test", "*"], {"device": 1}, {"device": "XXX"}, "test.XXX"),
        (
            ["test", "*", "*"],
            {"device": 1, "location": 2},
            {"device": "XXX", "location": "westus"},
            "test.XXX.westus",
        ),
    ],
)
def test_render_subject(
    tokens: t.List[str],
    placeholders: t.Dict[str, int],
    context: t.Mapping[str, t.Any],
    result: str,
):
    assert render_subject(tokens, placeholders, context, DEFAULT_SYNTAX) == result


def test_render_subject_missing_placeholder():
    with pytest.raises(
        ValueError,
        match=escape("Cannot render subject. Missing placeholders: ['device']"),
    ):
        render_subject(
            ["test", "*"], placeholders={"device": 1}, context={}, syntax=DEFAULT_SYNTAX
        )
