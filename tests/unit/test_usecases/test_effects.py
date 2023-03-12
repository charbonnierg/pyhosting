from hashlib import md5

import pytest

from pyhosting.adapters.gateways.templates import Jinja2Loader
from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import BlobNotFoundError
from pyhosting.domain.events import (
    PAGE_CREATED,
    PAGE_DELETED,
    VERSION_CREATED,
    VERSION_DELETED,
    VERSION_UPLOADED,
    PageCreated,
    PageDeleted,
    VersionCreated,
    VersionDeleted,
    VersionUploaded,
)
from pyhosting.domain.gateways import BlobStorageGateway, FilestorageGateway
from pyhosting.domain.operations.archives import create_archive_from_content
from pyhosting.domain.usecases.effects import pages_control_plane, pages_data_plane
from synopsys import EventBus
from synopsys.adapters.memory import InMemoryMessage as Msg
from synopsys.concurrency import Waiter

TEST_CONTENT = b"<html></html>"
TEST_ARCHIVE = create_archive_from_content(TEST_CONTENT)
TEST_MD5 = md5(TEST_ARCHIVE).hexdigest()


@pytest.mark.asyncio
class TestUploadContentOnVersionCreated:
    async def test_watch_page_version_created(
        self, blob_storage: BlobStorageGateway, event_bus: EventBus
    ):
        # Prepare test
        effect = pages_control_plane.UploadContentOnVersionCreated(
            event_bus=event_bus,
            storage=blob_storage,
        )
        waiter = await Waiter.create(event_bus.subscribe(VERSION_UPLOADED))
        # Run effet
        await effect(
            Msg(
                VERSION_CREATED,
                subject="test",
                payload=VersionCreated(
                    document=Version(
                        page_id="testid",
                        page_name="test",
                        page_version="1",
                        checksum=TEST_MD5,
                        created_timestamp=0,
                    ),
                    content=TEST_ARCHIVE,
                    latest=False,
                ),
                headers=None,
            )
        )
        # Check that event was published
        event = await waiter.wait(timeout=0.1)
        assert event.data == VersionUploaded(
            page_id="testid", page_name="test", page_version="1", is_latest=False
        )
        # Check that blob has been uploaded
        assert await blob_storage.get("testid", "1") == TEST_ARCHIVE


@pytest.mark.asyncio
class TestCleanStorageOnVersionDeleted:
    async def test_watch_page_version_deleted(self, blob_storage: BlobStorageGateway):
        # Prepare test
        page_id, page_version = "testid", "1"
        await blob_storage.put(page_id, page_version, blob=TEST_ARCHIVE)
        effect = pages_control_plane.CleanStorageOnVersionDeleted(storage=blob_storage)
        # Run effect
        await effect(
            Msg(
                VERSION_DELETED,
                subject="test",
                payload=VersionDeleted(
                    page_id="testid", page_name="test", page_version="1"
                ),
                headers=None,
            )
        )
        # Check that blob has been deleted from blob storage
        with pytest.raises(BlobNotFoundError):
            await blob_storage.get(page_id, page_version)


@pytest.mark.asyncio
class TestCleanStorageOnPageDeleted:
    async def test_watch_page_deleted(self, blob_storage: BlobStorageGateway):
        page_id, page_name = "testid", "test"
        for idx in range(3):
            await blob_storage.put(page_id, str(idx), blob=TEST_CONTENT)
        effect = pages_control_plane.CleanStorageOnPageDeleted(storage=blob_storage)
        await effect(
            Msg(
                PAGE_DELETED,
                subject="test",
                payload=PageDeleted(page_id=page_id, page_name=page_name),
                headers=None,
            )
        )
        assert len(await blob_storage.list_keys(page_id)) == 0
        assert len(await blob_storage.list_keys()) == 0


@pytest.mark.asyncio
class TestInitCacheOnPageCreated:
    async def test_generate_default_index_on_page_created(
        self, local_storage: FilestorageGateway
    ):
        # Prepare test
        default_path = local_storage.get_path("test", "__default__")
        assert not default_path.exists()

        effect = pages_data_plane.InitCacheOnPageCreated(
            local_storage=local_storage,
            base_url="http://testapp",
            templates=Jinja2Loader(),
        )
        # Run effect
        await effect(
            Msg(
                event=PAGE_CREATED,
                subject="test",
                payload=PageCreated(
                    document=Page(
                        id="testid",
                        name="test",
                        title="Test App",
                        description="",
                        latest_version=None,
                    )
                ),
                headers=None,
            )
        )
        # Check that default index was created
        assert default_path.is_dir()
        assert default_path.joinpath("index.html").is_file()


@pytest.mark.asyncio
class TestCleanCacheOnPageDeleted:
    async def test_clean_local_storage_on_page_deleted(
        self, local_storage: FilestorageGateway
    ):
        # Prepare test
        v1 = await local_storage.write_bytes(
            "test", "1", "index.html", content=TEST_CONTENT, create_parents=True
        )
        v2 = await local_storage.write_bytes(
            "test", "2", "index.html", content=TEST_CONTENT, create_parents=True
        )
        # Some assertions to make sure that we're ready to test
        assert v1.is_file() and v2.is_file()
        latest_link = v2.parent.parent.joinpath("__default__")
        latest_link.symlink_to(v2, target_is_directory=True)
        assert latest_link.is_symlink()
        # Run efect
        effect = pages_data_plane.CleanCacheOnPageDeleted(local_storage)
        await effect(
            Msg(
                PAGE_DELETED,
                subject="test",
                payload=PageDeleted(page_id="testid", page_name="test"),
                headers=None,
            )
        )
        # Check that files were deleted
        assert not v1.parent.is_dir()
        assert not v2.parent.is_dir()
        assert not latest_link.is_symlink()


@pytest.mark.asyncio
class TestCleanCacheOnVersionDeleted:
    async def test_clean_local_storage_on_version_deleted(
        self,
        local_storage: FilestorageGateway,
    ):
        # Prepare test
        v1 = await local_storage.write_bytes(
            "test", "1", "index.html", content=TEST_CONTENT, create_parents=True
        )
        assert v1.is_file()
        # Run effect
        effect = pages_data_plane.CleanCacheOnVersionDeleted(
            local_storage=local_storage
        )
        await effect(
            Msg(
                VERSION_DELETED,
                subject="test",
                payload=VersionDeleted(
                    page_id="testid", page_name="test", page_version="1"
                ),
                headers=None,
            )
        )
        # Check that files were deleted
        assert not v1.parent.is_dir()


@pytest.mark.asyncio
class TestUpdateCacheOnVersionUploaded:
    async def test_download_to_local_storage_on_latest_page_version_uploaded(
        self,
        local_storage: FilestorageGateway,
        blob_storage: BlobStorageGateway,
    ):
        # Prepare test
        await blob_storage.put("testid", "1", blob=TEST_ARCHIVE)
        # Run actor
        effect = pages_data_plane.UpdateCacheOnVersionUploaded(
            local_storage=local_storage,
            blob_storage=blob_storage,
        )
        await effect(
            Msg(
                VERSION_UPLOADED,
                subject="test",
                payload=VersionUploaded(
                    page_id="testid",
                    page_name="test",
                    page_version="1",
                    is_latest=True,
                ),
                headers=None,
            )
        )
        assert (
            local_storage.get_path("test", "1", "index.html").read_bytes()
            == TEST_CONTENT
        )
        assert (
            local_storage.get_path("test", "__latest__", "index.html").read_bytes()
            == TEST_CONTENT
        )

    async def test_download_to_local_storage_on_non_latest_page_version_uploaded(
        self,
        local_storage: FilestorageGateway,
        blob_storage: BlobStorageGateway,
    ):
        # Prepare test
        await blob_storage.put("testid", "1", blob=TEST_ARCHIVE)
        # Run actor
        effect = pages_data_plane.UpdateCacheOnVersionUploaded(
            local_storage=local_storage,
            blob_storage=blob_storage,
        )
        await effect(
            Msg(
                VERSION_UPLOADED,
                subject="test",
                payload=VersionUploaded(
                    page_id="testid",
                    page_name="test",
                    page_version="1",
                    is_latest=False,
                ),
                headers=None,
            )
        )
        assert (
            local_storage.get_path("test", "1", "index.html").read_bytes()
            == TEST_CONTENT
        )
        assert not local_storage.get_path("test", "__latest__", "index.html").exists()
        assert not local_storage.get_path("test", "__latest__").exists()
