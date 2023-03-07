import abc
import typing as t

from ..entities import Page, PageVersion


class PageRepository(metaclass=abc.ABCMeta):
    """Repository where pages are stored."""

    @abc.abstractmethod
    async def page_name_exists(self, name: str) -> t.Optional[str]:
        """Get either None or an ID of page with given name."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def get_page_by_id(self, id: str) -> t.Optional[Page]:
        """Get a single page by ID."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def create_page(self, page: Page) -> None:
        """Create and store a new page."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete_page(self, id: str) -> bool:
        """Delete an existing page"""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_pages(self) -> t.List[Page]:
        """List existing pages."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def update_latest_version(self, id: str, version: PageVersion) -> None:
        raise NotImplementedError  # pragma: no cover
