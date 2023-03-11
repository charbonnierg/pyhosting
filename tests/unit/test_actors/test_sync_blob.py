from hashlib import md5

import pytest

from pyhosting.domain.entities import PageVersion
from pyhosting.domain.events.page import PAGE_DELETED, PageDeleted
from pyhosting.domain.events.version import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
)
from pyhosting.domain.gateways import BlobStorageGateway
from pyhosting.domain.usecases.effects import pages_control_plane
from synopsys import EventBus
from synopsys.adapters.memory import InMemoryMessage as Msg
from synopsys.concurrency import Waiter


@pytest.mark.asyncio
class TestSyncBlobActors:
    async def test_watch_page_version_created(
        self, blob_storage: BlobStorageGateway, event_bus: EventBus
    ):
        content = b"<html></html>"
        checksum = md5(content).hexdigest()
        actor = pages_control_plane.UploadToBlobStorageOnVersionCreated(
            event_bus=event_bus,
            storage=blob_storage,
        )
        waiter = await Waiter.create(event_bus.subscribe(PAGE_VERSION_UPLOADED))
        await actor(
            Msg(
                PAGE_VERSION_CREATED,
                subject="test",
                payload=PageVersionCreated(
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
                headers=None,
            )
        )
        await waiter.wait(timeout=0.1)

    async def test_watch_page_version_deleted(self, blob_storage: BlobStorageGateway):
        await blob_storage.put_version(
            page_id="testid", page_version="1", content=b"<html></html>"
        )
        assert await blob_storage.get_version("testid", page_version="1")
        actor = pages_control_plane.CleanBlobStorageOnVersionDelete(
            storage=blob_storage
        )
        await actor(
            Msg(
                PAGE_VERSION_DELETED,
                subject="test",
                payload=PageVersionDeleted(
                    page_id="testid", page_name="test", version="1"
                ),
                headers=None,
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
        actor = pages_control_plane.CleanBlobStorageOnPageDelete(storage=blob_storage)
        await actor(
            Msg(
                PAGE_DELETED,
                subject="test",
                payload=PageDeleted(id="testid", name="test"),
                headers=None,
            )
        )
        for idx in range(3):
            assert not await blob_storage.get_version("testid", page_version=str(idx))
        assert len(await blob_storage.list_versions("testid")) == 0
