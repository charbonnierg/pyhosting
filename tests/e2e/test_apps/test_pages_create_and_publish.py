from hashlib import md5

import pytest

from pyhosting.adapters.clients.http.testing import PagesAPITestHTTPClient
from pyhosting.domain.events import VERSION_CREATED, VERSION_UPLOADED
from pyhosting.domain.operations.archives import create_archive_from_content
from synopsys import EventBus
from synopsys.concurrency import Waiter
from tests.utils import parametrize_clock, parametrize_id_generator

TEST_CONTENT = "<html><body></body></html>".encode()
TEST_ARCHIVE = create_archive_from_content(TEST_CONTENT)
TEST_CONTENT_MD5 = md5(TEST_ARCHIVE).hexdigest()


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
@pytest.mark.asyncio
async def test_create_page_and_publish_version_then_expect_pages(
    client: PagesAPITestHTTPClient, event_bus: EventBus
) -> None:
    """Check response from POST /pages/{page_id}/versions/."""
    # Start by creating a new page
    client.create_page(name="test", title="Test Page")
    # Expect fileserver to serve default index until a version is created
    page_response = client.http.get("/pages/test/")
    assert page_response.status_code == 200
    assert "Start by publishing a new version" in page_response.content.decode()
    # Create a waiter in background
    created_waiter = await Waiter.create(event_bus.subscribe(VERSION_CREATED))
    uploaded_waiter = await Waiter.create(event_bus.subscribe(VERSION_UPLOADED))
    # Create a new page version
    client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=True)
    # Expect event to be emitted
    await created_waiter.wait(timeout=0.1)
    # Expect actor to upload version to blob storage
    await uploaded_waiter.wait(timeout=0.5)
    # Expect fileserver to serve latest page version with test content
    page_response = client.http.get("/pages/test/")
    assert page_response.status_code == 200
    assert page_response.content == TEST_CONTENT
    # Expect fileserver to page version
    page_response = client.http.get("/pages/versions/test/1/")
    assert page_response.status_code == 200
    assert page_response.content == TEST_CONTENT
