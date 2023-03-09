from hashlib import md5

import pytest

from pyhosting.core.adapters import InMemoryMessage as Msg
from pyhosting.core.interfaces import EventBus
from pyhosting.domain.actors import sync_blob
from pyhosting.domain.entities import PageVersion
from pyhosting.domain.events.page_versions import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
)
from pyhosting.domain.events.pages import PAGE_DELETED, PageDeleted
from pyhosting.domain.gateways import BlobStorageGateway
from tests.utils import Waiter


@pytest.mark.asyncio
class TestSyncBlobActors:
    async def test_watch_page_version_created(
        self, blob_storage: BlobStorageGateway, event_bus: EventBus
    ):
        content = b"<html></html>"
        checksum = md5(content).hexdigest()
        actor = sync_blob.UploadToBlobStorageOnVersionCreated(
            event_bus=event_bus,
            storage=blob_storage,
        )
        waiter = await Waiter.create(event_bus, PAGE_VERSION_UPLOADED)
        await actor.handler(
            Msg(
                PAGE_VERSION_CREATED,
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
                ),
            )
        )
        await waiter.wait(timeout=0.1)

    async def test_watch_page_version_deleted(self, blob_storage: BlobStorageGateway):
        await blob_storage.put_version(
            page_id="testid", page_version="1", content=b"<html></html>"
        )
        assert await blob_storage.get_version("testid", page_version="1")
        actor = sync_blob.CleanBlobStorageOnVersionDelete(storage=blob_storage)
        await actor.handler(
            Msg(
                PAGE_VERSION_DELETED,
                PageVersionDeleted(page_id="testid", page_name="test", version="1"),
            )
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
        await actor.handler(Msg(PAGE_DELETED, PageDeleted(id="testid", name="test")))
        for idx in range(3):
            assert not await blob_storage.get_version("testid", page_version=str(idx))
        assert len(await blob_storage.list_versions("testid")) == 0
