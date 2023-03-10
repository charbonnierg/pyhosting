from dataclasses import dataclass

from pyhosting.core import StaticEvent

from ..entities import Page


@dataclass
class PageCreated:
    """Notify that a page has been created."""

    document: Page


PAGE_CREATED = StaticEvent("page-created", PageCreated)


@dataclass
class PageDeleted:
    """Notify that a page has been deleted"""

    id: str
    name: str


PAGE_DELETED = StaticEvent("page-deleted", PageDeleted)
