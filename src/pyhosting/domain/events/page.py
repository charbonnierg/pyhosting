from dataclasses import dataclass

from synopsys import create_event

from ..entities import Page


@dataclass
class PageCreated:
    """Notify that a page has been created."""

    document: Page


PAGE_CREATED = create_event(
    name="page-created",
    address="page.created",
    schema=PageCreated,
)


@dataclass
class PageDeleted:
    """Notify that a page has been deleted"""

    id: str
    name: str


PAGE_DELETED = create_event(
    name="page-deleted",
    address="page.deleted",
    schema=PageDeleted,
)
