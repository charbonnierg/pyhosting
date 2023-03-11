import typing as t
from dataclasses import dataclass

from ...entities import Page, PageVersion
from ...errors import PageNotFoundError, VersionNotFoundError
from ...repositories import PageRepository, PageVersionRepository


@dataclass
class GetPage:
    """Use case for retrieving an existing page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    page_repository: PageRepository

    async def __call__(self, page_id: str) -> Page:
        """Execute usecase: Get a page."""
        page = await self.page_repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        return page


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

    version_repository: PageVersionRepository
    get_page: GetPage

    async def __call__(self, page_id: str, page_version: str) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page(page_id=page_id)
        version = await self.version_repository.get_version(
            page_id=page_id, version=page_version
        )
        if version is None:
            raise VersionNotFoundError(page.name, page_version)
        return version


@dataclass
class GetLatestPageVersion:
    """Use case for retrieving an existing page."""

    version_repository: PageVersionRepository
    get_page: GetPage

    async def __call__(self, page_id: str) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page(page_id=page_id)
        if page.latest_version is None:
            raise VersionNotFoundError(page.name, version="latest")
        version = await self.version_repository.get_version(
            page_id=page_id, version=page.latest_version
        )
        # QUESTION: This should never happen, because version is defined on the page entity
        # Should we test this line ?
        if version is None:
            raise VersionNotFoundError(page.name, page.latest_version)
        return version


@dataclass
class ListPagesVersions:
    """Use case for listing existing page versions."""

    version_repository: PageVersionRepository
    get_page: GetPage

    async def __call__(self, page_id: str) -> t.List[PageVersion]:
        """Execute usecase: List existing pages."""
        await self.get_page(page_id=page_id)
        return await self.version_repository.list_versions(page_id=page_id)
