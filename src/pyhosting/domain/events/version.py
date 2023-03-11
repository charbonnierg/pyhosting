from dataclasses import dataclass

from synopsys import create_event

from ..entities import PageVersion


@dataclass
class PageVersionCreated:
    """Payload of page-version-created event."""

    document: PageVersion
    content: bytes
    latest: bool


PAGE_VERSION_CREATED = create_event(
    name="page-version-created",
    address="pages.created",
    schema=PageVersionCreated,
)


@dataclass
class PageVersionUploaded:
    """Payload of page-version uploaded event."""

    page_id: str
    page_name: str
    version: str


PAGE_VERSION_UPLOADED = create_event(
    name="page-version-uploaded",
    address="pages.versions.uploaded",
    schema=PageVersionUploaded,
)


@dataclass
class PageVersionDeleted:
    """Payload of page-version-deleted event."""

    page_id: str
    page_name: str
    version: str


PAGE_VERSION_DELETED = create_event(
    name="page-version-deleted",
    address="pages.versions.deleted",
    schema=PageVersionDeleted,
)
