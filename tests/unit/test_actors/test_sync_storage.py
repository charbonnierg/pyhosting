from pathlib import Path

import pytest

from pyhosting.domain.actors import sync_local
from pyhosting.domain.entities import Page
from pyhosting.domain.events.page_versions import (
    PageVersionDeleted,
    PageVersionUploaded,
)
from pyhosting.domain.events.pages import PageCreated, PageDeleted
from pyhosting.domain.gateways import BlobStorageGateway, LocalStorageGateway


@pytest.mark.asyncio
class TestSyncLocalActors:
    async def test_generate_default_index_on_page_created(
        self, local_storage: LocalStorageGateway
    ):
        actor = sync_local.GenerateDefaultIndexOnPageCreated(
            local_storage=local_storage, base_url="http://testapp"
        )
        default_path = local_storage.get_latest_path_or_default("test")
        assert not Path(default_path).exists()
        await actor.process_event(
            PageCreated(
                document=Page(
                    id="testid",
                    name="test",
                    title="Test App",
                    description="",
                    latest_version=None,
                )
            )
        )
        assert Path(default_path).is_dir()
        assert Path(default_path).joinpath("index.html").is_file()

    async def test_clean_local_storage_on_page_deleted(
        self, local_storage: LocalStorageGateway
    ):
        await local_storage.unpack_archive("test", "1", b"<html></html>", latest=True)
        await local_storage.unpack_archive("test", "2", b"<html></html>", latest=True)
        assert local_storage.root.joinpath(
            local_storage.get_version_path("test", "1")
        ).is_dir()
        assert local_storage.root.joinpath(
            local_storage.get_version_path("test", "2")
        ).is_dir()
        actor = sync_local.CleanLocalStorageOnPageDeleted(local_storage)
        await actor.process_event(PageDeleted(id="testid", name="test"))
        assert not local_storage.root.joinpath(
            local_storage.get_version_path("test", "1")
        ).is_dir()
        assert not local_storage.root.joinpath(
            local_storage.get_version_path("test", "2")
        ).is_dir()

    async def test_clean_local_storage_on_version_deleted(
        self,
        local_storage: LocalStorageGateway,
    ):
        await local_storage.unpack_archive("test", "1", b"<html></html>", latest=True)
        assert local_storage.root.joinpath(
            local_storage.get_version_path("test", "1")
        ).is_dir()
        actor = sync_local.CleanLocalStorageOnVersionDeleted(
            local_storage=local_storage
        )
        await actor.process_event(
            PageVersionDeleted(page_id="testid", page_name="test", version="1")
        )
        assert not local_storage.root.joinpath(
            local_storage.get_version_path("test", "1")
        ).is_dir()

    async def test_download_to_local_storage_on_page_version_uploaded(
        self,
        local_storage: LocalStorageGateway,
        blob_storage: BlobStorageGateway,
    ):
        assert not local_storage.root.joinpath(
            local_storage.get_version_path("test", "1")
        ).is_dir()
        await blob_storage.put_version("testid", "1", b"<html></html>")
        actor = sync_local.DownloadToLocalStorageOnVersionUploaded(
            local_storage=local_storage,
            blob_storage=blob_storage,
        )
        await actor.process_event(
            PageVersionUploaded(
                page_id="testid",
                page_name="test",
                version="1",
            )
        )
        assert (
            local_storage.root.joinpath(
                local_storage.get_version_path("test", "1", ["index.html"])
            ).read_bytes()
            == b"<html></html>"
        )