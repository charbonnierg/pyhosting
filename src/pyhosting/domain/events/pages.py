from dataclasses import dataclass

from ..entities import Page


@dataclass
class PageCreated:
    """Notify that a page has been created."""

    document: Page


PAGE_CREATED = ("page-created", PageCreated)


@dataclass
class PageDeleted:
    """Notify that a page has been deleted"""

    id: str
    name: str


PAGE_DELETED = ("page-deleted", PageDeleted)
