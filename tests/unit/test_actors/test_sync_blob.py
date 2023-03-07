from hashlib import md5

import pytest

from pyhosting.domain.actors import sync_blob
from pyhosting.domain.entities import PageVersion
from pyhosting.domain.events.page_versions import (
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
)
from pyhosting.domain.events.pages import PageDeleted
from pyhosting.domain.gateways import BlobStorageGateway, EventBusGateway
from tests.utils import Waiter


@pytest.mark.asyncio
class TestSyncBlobActors:
    async def test_watch_page_version_created(
        self, blob_storage: BlobStorageGateway, event_bus: EventBusGateway
    ):
        content = b"<html></html>"
        checksum = md5(content).hexdigest()
        actor = sync_blob.UploadToBlobStorageOnVersionCreated(
            event_bus=event_bus,
            storage=blob_storage,
        )
        waiter = await Waiter.start_in_background(event_bus, PAGE_VERSION_UPLOADED)
        await actor.process_event(
            PageVersionCreated(
                document=PageVersion(
                    page_id="testid",
                    page_name="test",
                    version="1",
                    checksum=checksum,
                    created_timestamp=0,
                ),
                content=content,
                latest=False,
            )
        )
        await waiter.wait(timeout=0.1)

    async def test_watch_page_version_deleted(self, blob_storage: BlobStorageGateway):
        await blob_storage.put_version(
            page_id="testid", page_version="1", content=b"<html></html>"
        )
        assert await blob_storage.get_version("testid", page_version="1")
        actor = sync_blob.CleanBlobStorageOnVersionDelete(storage=blob_storage)
        await actor.process_event(
            PageVersionDeleted(page_id="testid", page_name="test", version="1")
        )
        assert not await blob_storage.get_version("testid", page_version="1")

    async def test_watch_page_deleted(self, blob_storage: BlobStorageGateway):
        for idx in range(3):
            await blob_storage.put_version(
                page_id="testid", page_version=str(idx), content=b"<html></html>"
            )
        for idx in range(3):
            assert await blob_storage.get_version("testid", page_version=str(idx))
        assert len(await blob_storage.list_versions("testid")) == 3
        actor = sync_blob.CleanBlobStorageOnPageDelete(storage=blob_storage)
        await actor.process_event(PageDeleted(id="testid", name="test"))
        for idx in range(3):
            assert not await blob_storage.get_version("testid", page_version=str(idx))
        assert len(await blob_storage.list_versions("testid")) == 0
