import typing as t

import pytest
from genid import IDGenerator

from pyhosting.core.interfaces import EventBus
from pyhosting.domain.entities import Page, PageVersion
from pyhosting.domain.errors import PageAlreadyExistsError, PageNotFoundError
from pyhosting.domain.events import PAGE_CREATED, PAGE_DELETED
from pyhosting.domain.repositories import PageRepository
from pyhosting.domain.usecases import crud_pages
from tests.utils import Waiter, parametrize_id_generator, parametrize_page_repository


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestPageCrudUseCases:
    """Test CRUD Page usecases."""

    async def test_list_pages_empty(self, page_repository: PageRepository):
        result = await crud_pages.ListPages(page_repository).do()
        assert result == []

    @pytest.mark.parametrize(
        "name,title,description,page",
        [
            (
                "test",
                "Test Page",
                "Something",
                Page(
                    id="fakeid",
                    name="test",
                    title="Test Page",
                    description="Something",
                    latest_version=None,
                ),
            ),
            (
                "other",
                None,
                None,
                Page(
                    id="fakeid",
                    name="other",
                    title="other",
                    description="",
                    latest_version=None,
                ),
            ),
        ],
    )
    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_page_success(
        self,
        name: str,
        title: str,
        description: t.Optional[str],
        page: Page,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        waiter = await Waiter.create(event_bus, PAGE_CREATED)
        result = await crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        ).do(name=name, title=title, description=description)
        assert result == page
        await waiter.wait(timeout=0.1)

    @parametrize_id_generator("incremental")
    async def test_create_page_already_exists(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        result = await usecase.do(name="test")
        assert result == Page(
            id="0", name="test", title="test", description="", latest_version=None
        )
        with pytest.raises(PageAlreadyExistsError, match="Page already exists: test"):
            await usecase.do(name="test")

    @parametrize_id_generator("incremental")
    async def test_list_pages_many(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        for i in range(10):
            await create_usecase.do(name=f"test-{i}")
        list_usecase = crud_pages.ListPages(page_repository)
        result = await list_usecase.do()
        assert result == [
            Page(
                id=str(idx),
                name=f"test-{idx}",
                title=f"test-{idx}",
                description="",
                latest_version=None,
            )
            for idx in range(10)
        ]

    @parametrize_id_generator("constant", value="fakeid")
    async def test_get_page_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        page = await create_usecase.do(name="test")
        get_usecase = crud_pages.GetPage(repository=page_repository)
        get_result = await get_usecase.do(page_id="fakeid")
        assert (
            page
            == get_result
            == Page(
                id="fakeid",
                name="test",
                title="test",
                description="",
                latest_version=None,
            )
        )

    async def test_get_page_not_found(self, page_repository: PageRepository):
        usecase = crud_pages.GetPage(repository=page_repository)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await usecase.do(page_id="not-an-existing-id")

    async def test_delete_page_not_found(
        self, page_repository: PageRepository, event_bus: EventBus
    ):
        usecase = crud_pages.DeletePage(repository=page_repository, event_bus=event_bus)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await usecase.do(page_id="not-an-existing-id")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_page_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        waiter = await Waiter.create(event_bus, PAGE_DELETED)
        page = await create_usecase.do(name="test", title=None, description=None)
        delete_usecase = crud_pages.DeletePage(
            repository=page_repository, event_bus=event_bus
        )
        await delete_usecase.do(page.id)
        await waiter.wait(0.1)
        get_usecase = crud_pages.GetPage(repository=page_repository)
        with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
            await get_usecase.do(page_id=page.id)

    @parametrize_id_generator("constant", value="fakeid")
    async def test_update_latest_version_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        page = await create_usecase.do(name="test")
        assert page.latest_version is None
        update_usecase = crud_pages.UpdateLatestPageVersion(page_repository)
        await update_usecase.do(
            "fakeid",
            version=PageVersion(
                page_id="fakeid",
                page_name="test",
                version="1",
                checksum="",
                created_timestamp=0,
            ),
        )
        get_usecase = crud_pages.GetPage(repository=page_repository)
        page = await get_usecase.do(page_id="fakeid")
        assert page.latest_version == "1"
        await update_usecase.do(
            "fakeid",
            version=PageVersion(
                page_id="fakeid",
                page_name="test",
                version="2",
                checksum="",
                created_timestamp=0,
            ),
        )
        page = await get_usecase.do(page_id="fakeid")
        assert page.latest_version == "2"

    async def test_update_latest_version_not_found(
        self,
        page_repository: PageRepository,
    ):
        update_usecase = crud_pages.UpdateLatestPageVersion(page_repository)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await update_usecase.do(
                "not-an-existing-id",
                version=PageVersion(
                    page_id="not-an-existing-id",
                    page_name="test",
                    version="1",
                    checksum="",
                    created_timestamp=0,
                ),
            )
