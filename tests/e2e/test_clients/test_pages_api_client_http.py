from hashlib import md5

import pytest
from starlette import status

from pyhosting import __version__
from pyhosting.adapters.clients.http.testing import PagesAPITestHTTPClient
from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import (
    InvalidRequestError,
    PageAlreadyExistsError,
    PageNotFoundError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from pyhosting.domain.operations.archives import create_archive_from_content
from tests.utils import parametrize_clock, parametrize_id_generator

TEST_CONTENT = "<html><body></body></html>".encode()
TEST_ARCHIVE = create_archive_from_content(TEST_CONTENT)
TEST_CONTENT_MD5 = md5(TEST_ARCHIVE).hexdigest()


def test_get_api_version(client: PagesAPITestHTTPClient):
    version = client.api_version()
    assert version == __version__


def test_get_page_does_not_exist(client: PagesAPITestHTTPClient):
    """Check response from GET /pages/<id>"""
    with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
        client.get_page("fakeid")


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_page(client: PagesAPITestHTTPClient):
    """Check response from POST /pages/{page_id}/versions/."""
    # Create a new page
    created_page = client.create_page(name="test", title="Test Page")
    # Expect content (client already validates status code and parse response)
    assert created_page == Page(
        id="fakeid", name="test", title="Test Page", description="", latest_version=None
    )


@parametrize_id_generator("constant", value="fakeid")
def test_get_page(client: PagesAPITestHTTPClient):
    """Check response from GET /pages/<id>"""
    created_page = client.create_page(name="test", title="Test Page")
    client.delete_page(id=created_page.id)
    with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
        client.get_page(created_page.id)


@parametrize_id_generator("constant", value="fakeid")
def test_get_page_by_name(client: PagesAPITestHTTPClient) -> None:
    created_page = client.create_page(name="test")
    read_page = client.get_page_by_name("test")
    assert created_page == read_page


def test_get_page_by_name_not_found(client: PagesAPITestHTTPClient) -> None:
    with pytest.raises(PageNotFoundError, match="Page not found: test"):
        client.get_page_by_name("test")
    client.create_page(name="test")
    with pytest.raises(Exception, match="not-an-existing-id"):
        client.get_page_by_name("not-an-existing-id")


def test_list_pages_empty(client: PagesAPITestHTTPClient):
    """Check response from GET /pages."""
    pages = client.list_pages()
    assert pages == []


@parametrize_id_generator("incremental")
def test_list_pages_many(client: PagesAPITestHTTPClient):
    for idx in range(3):
        client.create_page(name=f"test-{idx}")
    pages = client.list_pages()
    assert pages == [
        Page("0", name="test-0", title="test-0", description="", latest_version=None),
        Page("1", name="test-1", title="test-1", description="", latest_version=None),
        Page("2", name="test-2", title="test-2", description="", latest_version=None),
    ]


@parametrize_id_generator("constant", value="fakeid")
def test_create_page_already_exists(client: PagesAPITestHTTPClient):
    """Check response from POST /pages."""
    client.create_page(name="test", title="Test Page")
    with pytest.raises(PageAlreadyExistsError, match="Page already exists: test"):
        client.create_page(name="test", title="Test Page")


def test_delete_page_not_found(client: PagesAPITestHTTPClient) -> None:
    with pytest.raises(PageNotFoundError, match="Page not found: fakeid"):
        client.delete_page("fakeid")


def test_create_version_page_not_found(client: PagesAPITestHTTPClient):
    with pytest.raises(PageNotFoundError, match="Page not found: not-an-existing-id"):
        # Attempt to create a page with empty content
        client.publish_page_version(
            "not-an-existing-id",
            version="1",
            content=b"hello",
        )


def test_create_version_page_not_found_evaluate_content_first(
    client: PagesAPITestHTTPClient,
):
    with pytest.raises(InvalidRequestError, match="Invalid request: Content is empty"):
        # Attempt to create a page with empty content
        client.publish_page_version(
            "not-an-existing-id",
            version="1",
            content=b"",
        )


def test_create_version_error_missing_header(client: PagesAPITestHTTPClient):
    # Attempt to create a page without "x-page-version" header
    response = client.http.post(
        "/api/pages/fakeid/versions/",
        content=TEST_ARCHIVE,
    )
    assert response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
    assert "x-page-version header must be present" in response.content.decode()


@parametrize_id_generator("constant", value="fakeid")
def test_create_version_error_missing_payload(client: PagesAPITestHTTPClient):
    # Create a new page
    client.create_page(name="test")
    with pytest.raises(InvalidRequestError, match="Content is empty"):
        # Attempt to create a page with empty content
        client.publish_page_version(
            "fakeid",
            version="1",
            content=b"",
        )


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_version_already_exists(client: PagesAPITestHTTPClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # Create a new latest version
    client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=True)
    with pytest.raises(
        VersionAlreadyExistsError, match="Version already exists: test/1"
    ):
        client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=True)


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_version_latest(client: PagesAPITestHTTPClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # Create a new latest version
    version = client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=True)
    # Expect content (client already validates status code and parse response)
    assert version == Version(
        page_id="fakeid",
        page_name="test",
        page_version="1",
        checksum=TEST_CONTENT_MD5,
        created_timestamp=0,
    )
    assert client.get_page("fakeid") == Page(
        id="fakeid",
        name="test",
        title="Test Page",
        description="",
        latest_version="1",
    )


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_version_non_latest(client: PagesAPITestHTTPClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # Create a new latest version
    version = client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=False)
    # Get page version
    read_version = client.get_page_version("fakeid", "1")
    # Expect content (client already validates status code and parse response)
    assert (
        read_version
        == version
        == Version(
            page_id="fakeid",
            page_name="test",
            page_version="1",
            checksum=TEST_CONTENT_MD5,
            created_timestamp=0,
        )
    )
    assert client.get_page("fakeid") == Page(
        id="fakeid",
        name="test",
        title="Test Page",
        description="",
        latest_version=None,
    )


@parametrize_id_generator("constant", value="fakeid")
def test_delete_version_non_latest(client: PagesAPITestHTTPClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # The create a new version with latest=False
    client.publish_page_version("fakeid", "1", TEST_ARCHIVE, latest=False)
    # Delete the version
    client.delete_page_version("fakeid", "1")
    # Expect get to raise an error
    with pytest.raises(VersionNotFoundError, match="Version not found: fakeid/1"):
        client.get_page_version("fakeid", "1")


def test_delete_version_page_not_found(client: PagesAPITestHTTPClient):
    with pytest.raises(
        VersionNotFoundError, match="Version not found: not-an-existing-id/0"
    ):
        client.delete_page_version("not-an-existing-id", "0")


@parametrize_id_generator("constant", value="fakeid")
def test_delete_version_not_found(client: PagesAPITestHTTPClient):
    client.create_page(name="test", title="Test Page")
    with pytest.raises(VersionNotFoundError, match="Version not found: fakeid/0"):
        client.delete_page_version("fakeid", "0")


def test_list_versions_page_not_found(client: PagesAPITestHTTPClient):
    with pytest.raises(PageNotFoundError, match="Page not found: not-an-existing-id"):
        client.list_page_versions("not-an-existing-id")


@parametrize_id_generator("constant", value="fakeid")
def test_list_versions_empty(client: PagesAPITestHTTPClient):
    client.create_page(name="test", title="Test Page")
    versions = client.list_page_versions("fakeid")
    assert versions == []


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_list_versions_many_results(client: PagesAPITestHTTPClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # The create a new version with latest=False
    for idx in range(10):
        client.publish_page_version("fakeid", str(idx), TEST_ARCHIVE, latest=True)
    result = client.list_page_versions("fakeid")
    assert len(result) == 10
    assert result == [
        Version(
            page_id="fakeid",
            page_name="test",
            page_version=str(idx),
            checksum=TEST_CONTENT_MD5,
            created_timestamp=0,
        )
        for idx in range(10)
    ]
