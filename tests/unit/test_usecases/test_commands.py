from hashlib import md5
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from genid import IDGenerator

from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import (
    CannotDeleteLatestVersionError,
    EmptyContentError,
    InvalidContentError,
    PageAlreadyExistsError,
    PageNotFoundError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from pyhosting.domain.events import (
    PAGE_CREATED,
    PAGE_DELETED,
    VERSION_CREATED,
    VERSION_DELETED,
    PageCreated,
    PageDeleted,
    VersionCreated,
    VersionDeleted,
)
from pyhosting.domain.operations.archives import (
    create_archive,
    create_archive_from_content,
)
from pyhosting.domain.repositories import PageRepository
from pyhosting.domain.usecases import commands, queries
from synopsys import EventBus
from synopsys.concurrency import Waiter
from tests.utils import parametrize_id_generator, parametrize_page_repository

TEST_ARCHIVE = create_archive_from_content(b"<html></html>")


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestPublishVersion:
    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_non_latest(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        publish_version = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Prepare queries
        query_page = queries.pages.GetPage(page_repository)
        query_version = queries.pages.GetPageVersion(page_repository=page_repository)
        # Run test
        waiter = await Waiter.create(event_bus.subscribe(VERSION_CREATED))
        version = await publish_version(
            page_id="fakeid",
            page_version="1",
            content=TEST_ARCHIVE,
            latest=False,
        )
        event = await waiter.wait(0.1)
        assert event.data == VersionCreated(
            document=version,
            content=TEST_ARCHIVE,
            latest=False,
        )
        # Check page entity
        result = await query_page(page_id="fakeid")
        assert result.latest_version is None
        # Check page version entity
        version_result = await query_version(page_id="fakeid", page_version="1")
        assert version_result == Version(
            page_id="fakeid",
            page_name="test",
            page_version="1",
            checksum=md5(TEST_ARCHIVE).hexdigest(),
            created_timestamp=0,
        )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_latest(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        # Prepare queries
        query_page = queries.pages.GetPage(page_repository)
        query_version = queries.pages.GetLatestPageVersion(
            page_repository=page_repository
        )
        # Run test
        publish_version = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        waiter = await Waiter.create(event_bus.subscribe(VERSION_CREATED))
        # Run test
        version = await publish_version(
            page_id="fakeid",
            page_version="1",
            content=TEST_ARCHIVE,
            latest=True,
        )
        event = await waiter.wait()
        assert event.data == VersionCreated(
            document=version,
            content=TEST_ARCHIVE,
            latest=True,
        )
        # Test page entity query
        result = await query_page(page_id="fakeid")
        assert result.latest_version == "1"
        # Test page version entity query
        version_result = await query_version(page_id="fakeid")
        assert version_result == Version(
            page_id="fakeid",
            page_name="test",
            page_version="1",
            checksum=md5(TEST_ARCHIVE).hexdigest(),
            created_timestamp=0,
        )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_already_exists(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Create version a first time
        await command(
            page_id="fakeid",
            page_version="1",
            content=TEST_ARCHIVE,
            latest=True,
        )
        # Run test: attempt to create same version a second time
        with pytest.raises(
            VersionAlreadyExistsError, match="Version already exists: test/1"
        ):
            await command(
                page_id="fakeid",
                page_version="1",
                content=TEST_ARCHIVE,
                latest=True,
            )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_empty_content(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Run test: attempt to publish a version with empty content
        with pytest.raises(EmptyContentError, match="Content is empty"):
            await command(
                page_id="fakeid",
                page_version="1",
                content=b"",
                latest=True,
            )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_invalid_tar_archive(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Run test: attempt to publish a version with empty content
        with pytest.raises(
            InvalidContentError, match="Content is not a valid tar archive"
        ):
            await command(
                page_id="fakeid",
                page_version="1",
                content=b"invalid-tar-file",
                latest=True,
            )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_missing_index_html(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Prepare some invalid content
        with TemporaryDirectory() as tmpdir:
            invalid_source = Path(tmpdir).joinpath("invalid")
            invalid_source.mkdir()
            invalid_source.joinpath("some_non_html_file.txt").write_bytes(
                b"some content"
            )
            # Run test: attempt to publish a version with empty content
            with pytest.raises(
                InvalidContentError, match="No index.html found in content"
            ):
                await command(
                    page_id="fakeid",
                    page_version="1",
                    content=create_archive(invalid_source),
                    latest=True,
                )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_without_top_level_dir(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Prepare some invalid content
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir).joinpath("valid")
            source.mkdir()
            source.joinpath("index.html").write_bytes(b"<html></html>")
            # Run test: attempt to publish a version with empty content
            await command(
                page_id="fakeid",
                page_version="1",
                content=create_archive(source, omit_top_level=True),
                latest=True,
            )

    @parametrize_id_generator("constant", value="fakeid")
    async def test_publish_version_with_top_level_dir(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        # Prepare some invalid content
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir).joinpath("valid")
            source.mkdir()
            source.joinpath("index.html").write_bytes(b"<html></html>")
            # Run test: attempt to publish a version with empty content
            await command(
                page_id="fakeid",
                page_version="1",
                content=create_archive(source, omit_top_level=False),
                latest=True,
            )


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestCreatePage:
    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_page_minimal(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        name = "test"
        command = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        waiter = await Waiter.create(event_bus.subscribe(PAGE_CREATED))
        expected_page = Page(
            id="fakeid",
            name=name,
            title=name,
            description="",
            latest_version=None,
        )
        assert await command(name=name) == expected_page
        # Check that event was received
        event = await waiter.wait(0.1)
        assert event.data == PageCreated(document=expected_page)
        # Check that query returns successfully
        query = queries.pages.GetPage(page_repository=page_repository)
        assert await query("fakeid") == expected_page

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_page_with_title(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        name, title = "test", "Some title"
        command = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        waiter = await Waiter.create(event_bus.subscribe(PAGE_CREATED))
        expected_page = Page(
            id="fakeid",
            name=name,
            title=title,
            description="",
            latest_version=None,
        )
        assert await command(name=name, title=title) == expected_page
        # Check that event was received
        event = await waiter.wait(0.1)
        assert event.data == PageCreated(document=expected_page)
        # Check that query returns successfully
        query = queries.pages.GetPage(page_repository=page_repository)
        assert await query("fakeid") == expected_page

    @parametrize_id_generator("constant", value="fakeid")
    async def test_create_page_with_description(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        name, description = "test", "Some description"
        command = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        waiter = await Waiter.create(event_bus.subscribe(PAGE_CREATED))
        expected_page = Page(
            id="fakeid",
            name=name,
            title=name,
            description=description,
            latest_version=None,
        )
        assert await command(name=name, description=description) == expected_page
        # Check that event was received
        event = await waiter.wait(0.1)
        assert event.data == PageCreated(document=expected_page)
        # Check that query returns successfully
        query = queries.pages.GetPage(page_repository=page_repository)
        assert await query("fakeid") == expected_page

    async def test_create_page_already_exists(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        command = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await command(name="test")
        with pytest.raises(PageAlreadyExistsError, match="Page already exists: test"):
            await command(name="test")


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestDeletePage:
    async def test_delete_page_not_found(
        self, page_repository: PageRepository, event_bus: EventBus
    ):
        command = commands.pages.DeletePage(
            page_repository=page_repository, event_bus=event_bus
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await command(page_id="not-an-existing-id")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_page_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_usecase = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        page = await create_usecase(name="test", title=None, description=None)
        # Run test
        waiter = await Waiter.create(event_bus.subscribe(PAGE_DELETED))
        delete_usecase = commands.pages.DeletePage(
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await delete_usecase(page.id)
        event = await waiter.wait(0.1)
        assert event.data == PageDeleted(page_id=page.id, page_name=page.name)
        # Check that query raises an error
        query = queries.pages.GetPage(page_repository=page_repository)
        with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
            await query(page_id=page.id)


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestUpdateLatestVersion:
    @parametrize_id_generator("constant", value="fakeid")
    async def test_update_latest_version_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test (create page and version)
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        page = await create_page(name="test")
        assert page.latest_version is None
        publish_version = commands.pages.PublishVersion(
            page_repository=page_repository, event_bus=event_bus, clock=lambda: 0
        )
        await publish_version(
            page.id,
            "1",
            content=TEST_ARCHIVE,
            latest=False,
        )
        # Prepare query to check latest version
        query = queries.pages.GetPage(page_repository=page_repository)
        # Run test
        update_latest_version = commands.pages.UpdateLatestPageVersion(page_repository)
        await update_latest_version("fakeid", "1")
        # Check that latest version was updated
        page = await query(page_id="fakeid")
        assert page.latest_version == "1"
        # Publish a new version
        await publish_version(
            page.id,
            "2",
            content=TEST_ARCHIVE,
            latest=True,
        )
        # Check that latest version was updated
        page = await query(page_id="fakeid")
        assert page.latest_version == "2"
        # Update version (should not do anything)
        await update_latest_version(
            page_id="fakeid",
            page_version="2",
        )
        # Check that latest version was updated
        page = await query(page_id="fakeid")
        assert page.latest_version == "2"

    async def test_update_latest_version_not_found(
        self,
        page_repository: PageRepository,
    ):
        command = commands.pages.UpdateLatestPageVersion(page_repository)
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await command("not-an-existing-id", "1")


@pytest.mark.asyncio
@parametrize_page_repository("memory")
class TestDeleteVersion:
    async def test_delete_version_page_not_found(
        self,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        command = commands.pages.DeletePageVersion(
            page_repository=page_repository,
            event_bus=event_bus,
        )
        with pytest.raises(
            PageNotFoundError, match="Page not found: not-an-existing-id"
        ):
            await command(page_id="not-an-existing-id", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_not_found(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        command = commands.pages.DeletePageVersion(
            page_repository=page_repository,
            event_bus=event_bus,
        )
        with pytest.raises(VersionNotFoundError, match="Version not found: test/0"):
            await command(page_id="fakeid", page_version="0")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_cannot_delete_latest(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        # Prepare test
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        publish_version = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        await publish_version(
            page_id="fakeid",
            page_version="1",
            content=TEST_ARCHIVE,
            latest=True,
        )
        # Run test
        command = commands.pages.DeletePageVersion(
            page_repository=page_repository,
            event_bus=event_bus,
        )

        with pytest.raises(
            CannotDeleteLatestVersionError,
            match="Cannot delete latest page version: test/1",
        ):
            await command(page_id="fakeid", page_version="1")

    @parametrize_id_generator("constant", value="fakeid")
    async def test_delete_version_success(
        self,
        id_generator: IDGenerator,
        page_repository: PageRepository,
        event_bus: EventBus,
    ):
        create_page = commands.pages.CreatePage(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
        )
        await create_page(name="test")
        publish_version = commands.pages.PublishVersion(
            page_repository=page_repository,
            event_bus=event_bus,
            clock=lambda: 0,
        )
        await publish_version(
            page_id="fakeid",
            page_version="1",
            content=TEST_ARCHIVE,
            latest=True,
        )
        await publish_version(
            page_id="fakeid",
            page_version="2",
            content=TEST_ARCHIVE,
            latest=True,
        )
        # Run test
        command = commands.pages.DeletePageVersion(
            page_repository=page_repository,
            event_bus=event_bus,
        )
        waiter = await Waiter.create(event_bus.subscribe(VERSION_DELETED))
        await command(page_id="fakeid", page_version="1")
        event = await waiter.wait(0.1)
        assert event.data == VersionDeleted(
            page_id="fakeid", page_name="test", page_version="1"
        )
        # Test queries
        query_latest_version = queries.pages.GetLatestPageVersion(
            page_repository=page_repository
        )
        query_version = queries.pages.GetPageVersion(page_repository=page_repository)
        latest_version = await query_latest_version(page_id="fakeid")
        version_2 = await query_version(page_id="fakeid", page_version="2")

        assert (
            version_2
            == latest_version
            == Version(
                page_id="fakeid",
                page_name="test",
                page_version="2",
                checksum=md5(TEST_ARCHIVE).hexdigest(),
                created_timestamp=0,
            )
        )

        with pytest.raises(VersionNotFoundError, match="Version not found: test/1"):
            await query_version(page_id="fakeid", page_version="1")
