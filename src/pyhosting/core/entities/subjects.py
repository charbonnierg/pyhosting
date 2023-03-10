import typing as t

from ..utils.events import DEFAULT_SYNTAX as DEFAULT_SYNTAX
from ..utils.events import FilterSyntax as FilterSyntax
from ..utils.events import (
    extract_subject_placeholders,
    filter_match,
    substitute_placeholders,
)


class Filter:
    """A subject filter is a dot-separated string."""

    def match(self, subject: str) -> bool:
        """Return True if a filter matches given subject."""
        return filter_match(
            subject=subject,
            filter=self.value,
            syntax=self.syntax,
        )

    def extract(self, subject: str) -> t.Dict[str, str]:
        return extract_subject_placeholders(subject, self._placeholders, self.syntax)

    @property
    def placeholders(self) -> t.Dict[str, int]:
        """Return placeholders found in filter."""
        return self._placeholders

    @property
    def subject(self) -> str:
        """Return a valid NATS subject according to filter."""
        return self._subject

    def __init__(
        self,
        value: str,
        context: t.Optional[t.Dict[str, str]] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        """Create a new event using a subjet and a schema."""
        self.value = value
        self.context = context or {}
        self.syntax = syntax or DEFAULT_SYNTAX
        self._subject, self._placeholders = substitute_placeholders(
            self.value, self.context
        )
        self._tokens = self._subject.split(self.syntax.match_sep)

    def __str__(self) -> str:
        """Basic string representation."""
        return self._subject

    def __repr__(self) -> str:
        """User-friendly String representation."""
        return self.value

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, Filter):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        raise TypeError(f"Cannot compare Subject with {type(other).__name__}")
