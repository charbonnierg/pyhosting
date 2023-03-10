from dataclasses import dataclass

from pyhosting.core import StaticEvent

from ..entities import PageVersion


@dataclass
class PageVersionCreated:
    """Payload of page-version-created event."""

    document: PageVersion
    content: bytes
    latest: bool


PAGE_VERSION_CREATED = StaticEvent("page-version-created", PageVersionCreated)


@dataclass
class PageVersionUploaded:
    """Payload of page-version uploaded event."""

    page_id: str
    page_name: str
    version: str


PAGE_VERSION_UPLOADED = StaticEvent("page-version-uploaded", PageVersionUploaded)


@dataclass
class PageVersionDeleted:
    """Payload of page-version-deleted event."""

    page_id: str
    page_name: str
    version: str


PAGE_VERSION_DELETED = StaticEvent("page-version-deleted", PageVersionDeleted)
