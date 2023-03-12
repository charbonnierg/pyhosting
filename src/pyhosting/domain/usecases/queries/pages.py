import typing as t
from dataclasses import dataclass

from ...entities import Page, Version
from ...errors import VersionNotFoundError
from ...repositories import PageRepository


@dataclass
class GetPage:
    """Use case for retrieving an existing page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    page_repository: PageRepository

    async def __call__(self, page_id: str) -> Page:
        """Execute usecase: Get a page."""
        return await self.page_repository.get_page(page_id)


@dataclass
class ListPages:
    """Use case for listing existing pages.

    Dependencies:
        repository: An implementation of `PageRepository`.
    """

    page_repository: PageRepository

    async def __call__(self) -> t.List[Page]:
        """Execute usecase: List existing pages."""
        return await self.page_repository.list_pages()


@dataclass
class GetPageVersion:
    """Use case for retrieving an existing page."""

    page_repository: PageRepository

    async def __call__(self, page_id: str, page_version: str) -> Version:
        """Execute usecase: Get a page version."""
        return await self.page_repository.get_version(
            page_id=page_id, page_version=page_version
        )


@dataclass
class GetLatestPageVersion:
    """Use case for retrieving an existing page."""

    page_repository: PageRepository

    async def __call__(self, page_id: str) -> Version:
        """Execute usecase: Get a page version."""
        page = await self.page_repository.get_page(page_id=page_id)
        if page.latest_version is None:
            raise VersionNotFoundError(page.name, version="latest")
        version = await self.page_repository.get_version(
            page_id=page_id, page_version=page.latest_version
        )
        return version


@dataclass
class ListPagesVersions:
    """Use case for listing existing page versions."""

    page_repository: PageRepository

    async def __call__(self, page_id: str) -> t.List[Version]:
        """Execute usecase: List existing pages."""
        await self.page_repository.get_page(page_id=page_id)
        return await self.page_repository.list_versions(page_id=page_id)
