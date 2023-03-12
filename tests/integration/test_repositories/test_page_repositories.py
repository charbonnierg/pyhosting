import pytest
from _pytest.fixtures import SubRequest

from pyhosting.adapters.repositories import InMemoryPageRepository
from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import PageNotFoundError, VersionNotFoundError
from pyhosting.domain.repositories import PageRepository


@pytest.fixture
def repository(request: SubRequest):
    param = request.param
    yield param()


@pytest.mark.asyncio
@pytest.mark.parametrize("repository", [InMemoryPageRepository], indirect=True)
class TestVersionRepository:
    async def test_get_page_id_not_found(self, repository: InMemoryPageRepository):
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-name"
        ):
            await repository.get_page_id("not-an-existing-name")

    async def test_get_page_not_found(self, repository: PageRepository):
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await repository.get_page_id("not-an-existing-id")

    async def test_get_page_id(self, repository: PageRepository):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version="1",
            )
        )
        assert await repository.get_page_id("test") == "testid"

    async def test_create_page_without_latest_version(self, repository: PageRepository):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version=None,
            )
        )
        page_by_id = await repository.get_page("testid")
        assert page_by_id == Page(
            id="testid",
            name="test",
            title="Test",
            description="Something",
            latest_version=None,
        )

    async def test_create_page_with_latest_version(self, repository: PageRepository):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version="1",
            )
        )
        page_by_id = await repository.get_page("testid")
        assert page_by_id == Page(
            id="testid",
            name="test",
            title="Test",
            description="Something",
            latest_version="1",
        )

    async def test_list_pages(self, repository: PageRepository):
        assert await repository.list_pages() == []
        page1 = Page(
            "testid1",
            "test1",
            "Test",
            "1",
            None,
        )
        await repository.create_page(page1)
        assert await repository.list_pages() == [page1]
        page2 = Page("testid2", "test2", "Test", "2", None)
        await repository.create_page(page2)
        assert await repository.list_pages() == [page1, page2]

    async def test_delete_page(self, repository: PageRepository):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version="1",
            )
        )
        await repository.delete_page("testid")
        # Cannot be deleted twice
        with pytest.raises(PageNotFoundError, match="Page not found: testid"):
            await repository.delete_page("testid")
        # No longer possible to get page
        with pytest.raises(PageNotFoundError, match="Page not found: testid"):
            await repository.get_page("testid")
        # No longer possible to get id
        with pytest.raises(PageNotFoundError, match="Page not found: test"):
            await repository.get_page_id("test")

    async def test_update_latest_version_page_not_found(
        self, repository: PageRepository
    ):
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await repository.update_latest_version(
                Version(
                    page_id="not-an-existing-id",
                    page_name="fake",
                    page_version="1",
                    checksum="",
                    created_timestamp=0,
                )
            )

    async def test_update_latest_version_version_not_found(
        self, repository: PageRepository
    ):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version=None,
            )
        )
        with pytest.raises(VersionNotFoundError, match="Version not found: test/1"):
            await repository.update_latest_version(
                Version(
                    page_id="testid",
                    page_name="test",
                    page_version="1",
                    checksum="",
                    created_timestamp=0,
                )
            )

    async def test_update_latest_version_version_success(
        self, repository: PageRepository
    ):
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version=None,
            )
        )
        v1 = Version(
            page_id="testid",
            page_name="test",
            page_version="1",
            checksum="",
            created_timestamp=0,
        )
        await repository.create_version(v1)
        await repository.update_latest_version(v1)
        assert await repository.get_page("testid") == Page(
            id="testid",
            name="test",
            title="Test",
            description="Something",
            latest_version="1",
        )

    async def test_create_version_page_not_found(self, repository: PageRepository):
        with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
            await repository.create_version(
                Version(
                    page_id="fakeid",
                    page_name="test",
                    page_version="1",
                    checksum="",
                    created_timestamp=0,
                )
            )

    async def test_create_version(self, repository: PageRepository):
        await repository.create_page(Page("fakeid", "test", "test", "", None))
        write_version = Version(
            page_id="fakeid",
            page_name="test",
            page_version="1",
            checksum="",
            created_timestamp=0,
        )
        await repository.create_version(write_version)
        read_version = await repository.get_version("fakeid", "1")
        assert write_version == read_version
        assert await repository.version_exists("fakeid", "1")

    async def test_get_version_page_not_found(self, repository: PageRepository):
        with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
            await repository.get_version("fakeid", "1")

    async def test_delete_version_page_not_found(self, repository: PageRepository):
        with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
            await repository.delete_version("fakeid", "1")

    async def test_delete_version_not_found(self, repository: PageRepository):
        await repository.create_page(Page("fakeid", "test", "test", "", None))
        with pytest.raises(VersionNotFoundError, match="Version not found: test/1"):
            await repository.delete_version("fakeid", "1")

    async def test_delete_version(self, repository: PageRepository):
        await repository.create_page(Page("fakeid", "test", "test", "", None))
        await repository.create_version(Version("fakeid", "test", "1", "", 0))
        await repository.delete_version("fakeid", "1")
        assert not await repository.version_exists("fakeid", "1")
        with pytest.raises(VersionNotFoundError, match="Version not found: test/1"):
            await repository.get_version("fakeid", "1")

    async def test_list_versions_page_not_found(self, repository: PageRepository):
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await repository.list_versions("not-an-existing-id")
        await repository.create_page(
            Page(
                id="testid",
                name="test",
                title="Test",
                description="Something",
                latest_version=None,
            )
        )
        assert await repository.get_page_id("test") == "testid"

    async def test_list_versions(self, repository: PageRepository):
        await repository.create_page(Page("fakeid", "test", "test", "", None))
        assert await repository.list_versions("fakeid") == []
        await repository.create_version(Version("fakeid", "test", "1", "", 0))
        assert await repository.list_versions("fakeid") == [
            Version("fakeid", "test", "1", "", 0)
        ]
        await repository.create_version(Version("fakeid", "test", "2", "", 0))
        assert await repository.list_versions("fakeid") == [
            Version("fakeid", "test", "1", "", 0),
            Version("fakeid", "test", "2", "", 0),
        ]

    async def test_version_exists_page_not_found(self, repository: PageRepository):
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await repository.version_exists("not-an-existing-id", "1")
