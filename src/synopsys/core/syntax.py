from dataclasses import dataclass


@dataclass
class FilterSyntax:
    """Address filter syntax."""

    match_sep: str = "."
    """The character used to separate filter tokens."""

    match_all: str = ">"
    """The character used to match all tokens."""

    match_one: str = "*"
    """The character used to match a single token."""


DEFAULT_SYNTAX = FilterSyntax()
