import typing as t

import pytest

from synopsys.core.events import DEFAULT_SYNTAX
from synopsys.core.utils import normalize_filter_subject


@pytest.mark.parametrize(
    "subject,expected,expected_placeholders",
    [
        ("a", "a", {}),
        ("a.b", "a.b", {}),
        ("a.{device}", "a.*", {"device": 1}),
        ("a.b.{device}", "a.b.*", {"device": 2}),
        ("{device}.{sensor}", "*.*", {"device": 0, "sensor": 1}),
    ],
)
def test_normalize_subject(
    subject: str, expected: str, expected_placeholders: t.Dict[str, int]
):
    result, placeholders = normalize_filter_subject(subject, DEFAULT_SYNTAX)
    assert result == expected
    assert placeholders == expected_placeholders


@pytest.mark.parametrize(
    "invalid_filter",
    [
        "some{placeholder}",
        "some.other{placeholder}",
        "some.other{{placeholder}",
        "{placeholder}remaining",
        "{{placeholder}}",
        "some.{placeholder}remaining",
        "some.{placeholder}}.remaining",
    ],
)
def test_normalize_subject_invalid_filter(invalid_filter: str):
    with pytest.raises(ValueError, match="Placeholder must occupy whole token"):
        normalize_filter_subject(invalid_filter, DEFAULT_SYNTAX)


@pytest.mark.parametrize(
    "invalid_filter",
    [
        "{place.holder}",
        "{.}",
    ],
)
def test_normalize_subject_invalid_placeholder(invalid_filter: str):
    with pytest.raises(ValueError, match="Invalid placeholder name: Contains '.'"):
        normalize_filter_subject(invalid_filter, DEFAULT_SYNTAX)


def test_normalize_subject_empty_placeholder():
    with pytest.raises(ValueError, match="Placeholder cannot be empty: 'test.{}'"):
        normalize_filter_subject("test.{}", DEFAULT_SYNTAX)
