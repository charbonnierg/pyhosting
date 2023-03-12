import pytest

from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import PageNotFoundError, VersionNotFoundError
from pyhosting.domain.repositories import PageRepository
from pyhosting.domain.usecases import queries
from tests.utils import parametrize_page_repository


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestGetPage:
    async def test_get_page_success(
        self,
        page_repository: PageRepository,
    ):
        # Prepare test
        page = Page(
            id="testid", name="test", title="test", description="", latest_version=None
        )
        await page_repository.create_page(page)
        # Run test
        query = queries.pages.GetPage(page_repository=page_repository)
        assert await query(page_id="testid") == page

    async def test_get_page_not_found(self, page_repository: PageRepository):
        query = queries.pages.GetPage(page_repository=page_repository)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await query(page_id="not-an-existing-id")


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestGetVersion:
    """Test queries related to Pages and Versions entities."""

    async def test_get_version_page_not_found(
        self,
        page_repository: PageRepository,
    ):
        query = queries.pages.GetPageVersion(page_repository=page_repository)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await query(page_id="not-an-existing-id", page_version="0")

    async def test_get_version_not_found(
        self,
        page_repository: PageRepository,
    ):
        # Prepare test
        await page_repository.create_page(
            Page(
                id="testid",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
        )
        # Run test
        query = queries.pages.GetPageVersion(page_repository=page_repository)
        with pytest.raises(VersionNotFoundError, match="Version not found: test/0"):
            await query(page_id="testid", page_version="0")

    async def test_get_latest_version_not_found(
        self,
        page_repository: PageRepository,
    ):
        # Prepare test
        await page_repository.create_page(
            Page(
                id="testid",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
        )
        query = queries.pages.GetLatestPageVersion(page_repository=page_repository)
        with pytest.raises(
            VersionNotFoundError, match="Version not found: test/latest"
        ):
            await query(page_id="testid")


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestListPages:
    async def test_list_pages_empty(self, page_repository: PageRepository):
        """An empty list is returned when no page exist."""
        query = queries.pages.ListPages(page_repository)
        result = await query()
        assert result == []

    async def test_list_pages_many(
        self,
        page_repository: PageRepository,
    ):
        # Directly write into page repository
        for idx in range(10):
            await page_repository.create_page(
                Page(
                    id=f"test-{idx}",
                    name="test",
                    title="test",
                    description="",
                    latest_version=None,
                )
            )
        # List pages
        query = queries.pages.ListPages(page_repository)
        assert await query() == [
            Page(
                id=f"test-{idx}",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
            for idx in range(10)
        ]


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestListVersions:
    """Test queries related to Pages and Versions entities."""

    async def test_list_versions_page_not_found(self, page_repository: PageRepository):
        query = queries.pages.ListPagesVersions(
            page_repository=page_repository,
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await query(page_id="not-an-existing-id")

    async def test_list_versions_empty(
        self,
        page_repository: PageRepository,
    ):
        # Prepare test
        await page_repository.create_page(
            Page(
                id="test",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
        )
        query = queries.pages.ListPagesVersions(
            page_repository=page_repository,
        )
        assert await query(page_id="test") == []

    async def test_list_many_versions(
        self,
        page_repository: PageRepository,
    ):
        # Prepare test
        await page_repository.create_page(
            Page(
                id="testid",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
        )
        versions = [
            Version(
                page_id="testid",
                page_name="test",
                page_version=str(idx),
                checksum="0",
                created_timestamp=0,
            )
            for idx in range(10)
        ]
        for idx in range(10):
            await page_repository.create_version(versions[idx])
        # Run test
        query = queries.pages.ListPagesVersions(
            page_repository=page_repository,
        )
        result = await query(page_id="testid")
        assert result == versions
