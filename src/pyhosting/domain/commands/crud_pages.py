import typing as t
from dataclasses import dataclass


@dataclass
class CreatePageCommand:
    """Options provided to create page command."""

    name: str
    title: t.Optional[str] = None
    description: t.Optional[str] = None


@dataclass
class GetPageCommand:
    """Options provided to get a infos for a page."""

    id: str


@dataclass
class DeletePageCommand:
    """Options provided to delete a page."""

    id: str
