import typing as t
from re import escape

import pytest

from synopsys.core.events import DEFAULT_SYNTAX
from synopsys.core.utils import extract_subject_placeholders


@pytest.mark.parametrize(
    "subject,placeholders,result",
    [
        ("test", {}, {}),
        ("test.someid", {"device": 1}, {"device": "someid"}),
        (
            "test.someid.westus",
            {"device": 1, "location": 2},
            {"device": "someid", "location": "westus"},
        ),
    ],
)
def test_extract_subject_placeholders(
    subject: str, placeholders: t.Dict[str, int], result: t.Dict[str, str]
):
    assert extract_subject_placeholders(subject, placeholders, DEFAULT_SYNTAX) == result


def test_extract_subject_placeholders_missing():
    with pytest.raises(
        ValueError,
        match=escape("Invalid subject. Missing placeholder: device (index: 1)"),
    ):
        extract_subject_placeholders("test", {"device": 1}, DEFAULT_SYNTAX)

    with pytest.raises(
        ValueError,
        match=escape("Invalid subject. Missing placeholder: location (index: 2)"),
    ):
        extract_subject_placeholders(
            "test.device", {"device": 1, "location": 2}, DEFAULT_SYNTAX
        )
