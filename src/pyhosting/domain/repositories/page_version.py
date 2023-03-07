import abc
import typing as t

from ..entities import PageVersion


class PageVersionRepository(metaclass=abc.ABCMeta):
    """Repository where page versions are stored."""

    @abc.abstractmethod
    async def version_exists(self, page_id: str, version: str) -> t.Optional[bool]:
        """Return True when page version exists."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def get_version(self, page_id: str, version: str) -> t.Optional[PageVersion]:
        """Get a single page version."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def create_version(self, version: PageVersion) -> None:
        """Create and store a new page version."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_versions(self, page_id: str) -> t.List[PageVersion]:
        """List existing version for a page."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete_version(self, page_id: str, version: str) -> bool:
        """Delete a page version"""
        raise NotImplementedError  # pragma: no cover
