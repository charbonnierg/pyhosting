from dataclasses import dataclass

from ..entities import Page, Version


@dataclass
class PageCreated:
    """Paylaod of a page-created event."""

    document: Page


@dataclass
class PageDeleted:
    """Payload of a page-deleted event."""

    page_id: str
    page_name: str


@dataclass
class VersionCreated:
    """Payload of version-created event."""

    document: Version
    content: str
    latest: bool


@dataclass
class VersionUploaded:
    """Payload of version-uploaded event."""

    page_id: str
    page_name: str
    page_version: str
    is_latest: bool


@dataclass
class VersionDeleted:
    """Payload of version-deleted event."""

    page_id: str
    page_name: str
    page_version: str
