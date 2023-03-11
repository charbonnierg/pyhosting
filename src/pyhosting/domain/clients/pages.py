import typing as t

from ..entities import Page, PageVersion


class PagesClient(t.Protocol):
    def list_pages(self) -> t.List[Page]:
        """List pages"""
        raise NotImplementedError  # pragma: no cover

    def get_page_by_name(self, name: str) -> Page:
        """Get a page by name"""
        raise NotImplementedError  # pragma: no cover

    def get_page(self, id: str) -> Page:
        """Get a page by id"""
        raise NotImplementedError  # pragma: no cover

    def create_page(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Create a new page."""
        raise NotImplementedError  # pragma: no cover

    def delete_page(self, id: str) -> None:
        """Delete a page."""
        raise NotImplementedError  # pragma: no cover

    def publish_page_version(
        self,
        id: str,
        version: str,
        content: bytes,
        latest: bool = False,
    ) -> PageVersion:
        """Publish a new page version."""
        raise NotImplementedError  # pragma: no cover

    def delete_page_version(
        self,
        id: str,
        version: str,
    ) -> None:
        """Delete a page version."""
        raise NotImplementedError  # pragma: no cover

    def list_page_versions(self, id: str) -> t.List[PageVersion]:
        """List page versions."""
        raise NotImplementedError  # pragma: no cover
