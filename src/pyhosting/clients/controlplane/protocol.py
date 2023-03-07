import typing as t

from ...domain.entities import Page, PageVersion


class ControlPlaneClient(t.Protocol):
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
    ) -> str:
        """Create a new page."""
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
