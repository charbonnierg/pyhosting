from dataclasses import dataclass


@dataclass
class ListPageVersionsCommand:
    """Options provided to list page versions"""

    page_id: str


@dataclass
class CreatePageVersionCommand:
    """Options provided to create page version."""

    page_id: str
    version: str
    content: bytes
    latest: bool


@dataclass
class GetPageVersionCommand:
    """Options provided to get a infos for a page version."""

    page_id: str
    version: str


@dataclass
class GetLatestPageVersionCommand:
    """Options provided to get infos for latest page version."""

    page_id: str


@dataclass
class DeletePageVersionCommand:
    """Options provided to delete a page."""

    page_id: str
    version: str
