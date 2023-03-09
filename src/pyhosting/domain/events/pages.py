from dataclasses import dataclass

from pyhosting.core.entities import Event

from ..entities import Page


@dataclass
class PageCreated:
    """Notify that a page has been created."""

    document: Page


PAGE_CREATED = Event("page-created", PageCreated)


@dataclass
class PageDeleted:
    """Notify that a page has been deleted"""

    id: str
    name: str


PAGE_DELETED = Event("page-deleted", PageDeleted)
