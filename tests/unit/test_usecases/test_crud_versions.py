from hashlib import md5

import pytest
from genid import IDGenerator

from pyhosting.domain.entities import PageVersion
from pyhosting.domain.errors import (
    CannotDeleteLatestVersionError,
    PageNotFoundError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from pyhosting.domain.gateways import EventBusGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from pyhosting.domain.usecases import crud_pages, crud_versions
from tests.utils import (
    parametrize_id_generator,
    parametrize_page_repository,
    parametrize_page_version_repository,
)


@pytest.mark.asyncio
@parametrize_page_repository("memory")
@parametrize_page_version_repository("memory")
class TestPageCrudUseCases:
    async def test_list_versions_page_not_found(
        self, page_repository: PageRepository, version_repository: PageVersionRepository
    ):
        list_uscase = crud_versions.ListPagesVersions(
            repository=version_repository,
            get_page=crud_pages.GetPage(repository=page_repository),
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await list_uscase.do(page_id="not-an-existing-id")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_list_versions_empty(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        list_uscase = crud_versions.ListPagesVersions(
            repository=version_repository,
            get_page=crud_pages.GetPage(repository=page_repository),
        )
        result = await list_uscase.do(page_id="fakeid")
        assert result == []

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_and_list_many_versions(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        get_usecase = crud_pages.GetPage(page_repository)
        for idx in range(10):
            await publish_usecase.do(
                page_id="fakeid",
                page_version=str(idx),
                content=str(idx).encode(),
                latest=True,
            )
            page = await get_usecase.do(page_id="fakeid")
            assert page.latest_version == str(idx)

        list_usecase = crud_versions.ListPagesVersions(
            repository=version_repository,
            get_page=crud_pages.GetPage(repository=page_repository),
        )
        result = await list_usecase.do(page_id="fakeid")
        assert len(result) == 10

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_non_latest_version(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        get_version_usecase = crud_versions.GetPageVersion(
            repository=version_repository, get_page=get_page_usecase
        )
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        await publish_usecase.do(
            page_id="fakeid", page_version="1", content=b"<html></html>", latest=False
        )
        result = await get_page_usecase.do(page_id="fakeid")
        assert result.latest_version is None
        version_result = await get_version_usecase.do(
            page_id="fakeid", page_version="1"
        )
        assert version_result == PageVersion(
            page_id="fakeid",
            page_name="test",
            version="1",
            checksum=md5(b"<html></html>").hexdigest(),
            created_timestamp=0,
        )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_latest_version(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        get_version_usecase = crud_versions.GetLatestPageVersion(
            repository=version_repository, get_page=get_page_usecase
        )
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        await publish_usecase.do(
            page_id="fakeid", page_version="1", content=b"<html></html>", latest=True
        )
        result = await get_page_usecase.do(page_id="fakeid")
        assert result.latest_version == "1"
        version_result = await get_version_usecase.do(page_id="fakeid")
        assert version_result == PageVersion(
            page_id="fakeid",
            page_name="test",
            version="1",
            checksum=md5(b"<html></html>").hexdigest(),
            created_timestamp=0,
        )

    async def test_get_version_page_not_found(
        self,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
    ):
        get_page_usecase = crud_pages.GetPage(page_repository)
        get_version_usecase = crud_versions.GetPageVersion(
            repository=version_repository, get_page=get_page_usecase
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await get_version_usecase.do(page_id="not-an-existing-id", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_get_version_not_found(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        get_version_usecase = crud_versions.GetPageVersion(
            repository=version_repository, get_page=get_page_usecase
        )
        with pytest.raises(VersionNotFoundError, match="Version not found: test/0"):
            await get_version_usecase.do(page_id="fakeid", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_get_latest_version_not_found(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        get_version_usecase = crud_versions.GetLatestPageVersion(
            repository=version_repository, get_page=get_page_usecase
        )
        with pytest.raises(
            VersionNotFoundError, match="Version not found: test/latest"
        ):
            await get_version_usecase.do(page_id="fakeid")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_version_already_exists(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        await publish_usecase.do(
            page_id="fakeid", page_version="1", content=b"<html></html>", latest=True
        )
        with pytest.raises(
            VersionAlreadyExistsError, match="Version already exists: test/1"
        ):
            await publish_usecase.do(
                page_id="fakeid",
                page_version="1",
                content=b"<html></html>",
                latest=True,
            )

    async def test_delete_version_page_not_found(
        self,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        get_page_usecase = crud_pages.GetPage(page_repository)
        delete_version = crud_versions.DeletePageVersion(
            repository=version_repository,
            get_page=get_page_usecase,
            event_bus=event_bus,
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await delete_version.do(page_id="not-an-existing-id", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_not_found(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        delete_version_usecase = crud_versions.DeletePageVersion(
            repository=version_repository,
            get_page=get_page_usecase,
            event_bus=event_bus,
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
        )
        with pytest.raises(VersionNotFoundError, match="Version not found: test/0"):
            await delete_version_usecase.do(page_id="fakeid", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_cannot_delete_latest(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        delete_version_usecase = crud_versions.DeletePageVersion(
            repository=version_repository,
            get_page=get_page_usecase,
            event_bus=event_bus,
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
        )
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        await publish_usecase.do(
            page_id="fakeid", page_version="1", content=b"<html></html>", latest=True
        )
        with pytest.raises(
            CannotDeleteLatestVersionError,
            match="Cannot delete latest page version: test/1",
        ):
            await delete_version_usecase.do(page_id="fakeid", page_version="1")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        version_repository: PageVersionRepository,
        event_bus: EventBusGateway,
    ):
        create_usecase = crud_pages.CreatePage(
            id_generator=id_generator, repository=page_repository, event_bus=event_bus
        )
        await create_usecase.do(name="test")
        get_page_usecase = crud_pages.GetPage(page_repository)
        delete_version_usecase = crud_versions.DeletePageVersion(
            repository=version_repository,
            get_page=get_page_usecase,
            event_bus=event_bus,
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
        )
        publish_usecase = crud_versions.CreatePageVersion(
            repository=version_repository,
            event_bus=event_bus,
            get_page=crud_pages.GetPage(page_repository),
            update_latest_version=crud_pages.UpdateLatestPageVersion(page_repository),
            clock=lambda: 0,
        )
        await publish_usecase.do(
            page_id="fakeid", page_version="1", content=b"<html></html>", latest=True
        )
        page = await get_page_usecase.do("fakeid")
        assert page.latest_version == "1"

        await publish_usecase.do(
            page_id="fakeid", page_version="2", content=b"<html></html>", latest=True
        )

        await delete_version_usecase.do(page_id="fakeid", page_version="1")

        get_latest_version_usecase = crud_versions.GetLatestPageVersion(
            version_repository, get_page_usecase
        )
        get_version_usecase = crud_versions.GetPageVersion(
            version_repository, get_page_usecase
        )

        latest_version = await get_latest_version_usecase.do(page_id="fakeid")
        version_2 = await get_version_usecase.do(page_id="fakeid", page_version="2")

        assert (
            version_2
            == latest_version
            == PageVersion(
                page_id="fakeid",
                page_name="test",
                version="2",
                checksum=md5(b"<html></html>").hexdigest(),
                created_timestamp=0,
            )
        )

        with pytest.raises(VersionNotFoundError, match="Version not found: test/1"):
            await get_version_usecase.do(page_id="fakeid", page_version="1")
