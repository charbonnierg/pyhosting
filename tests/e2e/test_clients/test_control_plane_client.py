import pytest
from starlette import status

from pyhosting.clients.controlplane.testing import HTTPTestClient
from pyhosting.domain.entities import Page, PageVersion
from tests.utils import parametrize_clock, parametrize_id_generator

TEST_CONTENT = "<html><body></body></html>"
TEST_CONTENT_MD5 = "b256d97fbb697428b7a1286ea33539c0"


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_page(client: HTTPTestClient):
    """Check response from POST /pages/{page_id}/versions/."""
    # Create a new page
    page = client.create_page(name="test", title="Test Page")
    # Expect content (client already validates status code and parse response)
    assert page == Page(
        id="fakeid", name="test", title="Test Page", description="", latest_version=None
    )


@parametrize_id_generator("constant", value="fakeid")
def test_get_page(client: HTTPTestClient):
    """Check response from GET /pages/<id>"""
    created_page = client.create_page(name="test", title="Test Page")
    read_page = client.get_page("fakeid")
    assert (
        created_page
        == read_page
        == Page(
            id="fakeid",
            name="test",
            title="Test Page",
            description="",
            latest_version=None,
        )
    )
    client.delete_page(id="fakeid")
    with pytest.raises(Exception):
        client.get_page("fakeid")


@parametrize_id_generator("constant", value="fakeid")
def test_get_page_by_name(client: HTTPTestClient) -> None:
    with pytest.raises(Exception):
        client.get_page_by_name("test")
    client.create_page(name="test")
    client.get_page_by_name("test")
    client.delete_page(id="fakeid")
    with pytest.raises(Exception):
        client.get_page_by_name("test")


def test_get_page_by_name_not_found(client: HTTPTestClient) -> None:
    client.create_page(name="test")
    with pytest.raises(Exception):
        client.get_page_by_name("not-an-existing-id")


def test_list_pages_empty(client: HTTPTestClient):
    """Check response from GET /pages."""
    pages = client.list_pages()
    assert pages == []


@parametrize_id_generator("incremental")
def test_list_pages_many(client: HTTPTestClient):
    for idx in range(3):
        client.create_page(name=f"test-{idx}")
    pages = client.list_pages()
    assert pages == [
        Page("0", name="test-0", title="test-0", description="", latest_version=None),
        Page("1", name="test-1", title="test-1", description="", latest_version=None),
        Page("2", name="test-2", title="test-2", description="", latest_version=None),
    ]


def test_get_page_does_not_exist(client: HTTPTestClient):
    """Check response from GET /pages/<id>"""
    response = client.http.get("/api/pages/fakeid")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Page not found: fakeid"}}


@parametrize_id_generator("constant", value="fakeid")
def test_create_page_already_exists(client: HTTPTestClient):
    """Check response from POST /pages."""
    client.create_page(name="test", title="Test Page")
    response = client.http.post("/api/pages/", json={"name": "test"})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": {"error": "Page already exists: test"}}


def test_delete_page_not_found(client: HTTPTestClient) -> None:
    response = client.http.delete("/api/pages/fakeid")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Page not found: fakeid"}}


def test_create_version_error_missing_header(client: HTTPTestClient):
    # Attempt to create a page without "x-page-version" header
    version_create_response = client.http.post(
        "/api/pages/fakeid/versions/",
        content=TEST_CONTENT.encode(),
    )
    # Expect an error with appropriate status code
    assert version_create_response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
    assert version_create_response.json() == {
        "detail": {"error": "x-page-version header must be present"}
    }


@parametrize_id_generator("constant", value="fakeid")
def test_create_version_error_missing_payload(client: HTTPTestClient):
    # Create a new page
    client.create_page(name="test")
    # Attempt to create a page without "x-page-version" header
    version_create_response = client.http.post(
        "/api/pages/fakeid/versions/", headers={"x-page-version": "1"}
    )
    # Expect an error with appropriate status code
    assert version_create_response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
    assert version_create_response.json() == {"detail": {"error": "Content is empty"}}


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_create_version_latest(client: HTTPTestClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # Create a new latest version
    version = client.publish_page_version(
        "fakeid", "1", TEST_CONTENT.encode(), latest=True
    )
    # Expect content (client already validates status code and parse response)
    assert version == PageVersion(
        page_id="fakeid",
        page_name="test",
        version="1",
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
def test_create_version_non_latest(client: HTTPTestClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # Create a new latest version
    version = client.publish_page_version(
        "fakeid", "1", TEST_CONTENT.encode(), latest=False
    )
    # Get page version
    read_version = client.get_page_version("fakeid", "1")
    # Expect content (client already validates status code and parse response)
    assert (
        read_version
        == version
        == PageVersion(
            page_id="fakeid",
            page_name="test",
            version="1",
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
def test_delete_version_non_latest(client: HTTPTestClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # The create a new version with latest=False
    client.publish_page_version("fakeid", "1", TEST_CONTENT.encode(), latest=False)
    # Delete the version
    client.delete_page_version("fakeid", "1")
    # Expect get to raise an error
    with pytest.raises(Exception, match="404 Not Found"):
        client.get_page_version("fakeid", "1")


def test_delete_version_page_not_found(client: HTTPTestClient):
    with pytest.raises(Exception, match="404 Not Found"):
        client.delete_page_version("not-an-existin-id", "0")


@parametrize_id_generator("constant", value="fakeid")
def test_delete_version_not_found(client: HTTPTestClient):
    client.create_page(name="test", title="Test Page")
    with pytest.raises(Exception, match="404 Not Found"):
        client.delete_page_version("fakeid", "0")


def test_list_versions_page_not_found(client: HTTPTestClient):
    with pytest.raises(Exception, match="404 Not Found"):
        client.list_page_versions("not-an-existin-id")


@parametrize_id_generator("constant", value="fakeid")
def test_list_versions_empty(client: HTTPTestClient):
    client.create_page(name="test", title="Test Page")
    versions = client.list_page_versions("fakeid")
    assert versions == []


@parametrize_id_generator("constant", value="fakeid")
@parametrize_clock(lambda: 0)
def test_list_versions_many_results(client: HTTPTestClient):
    # Start by creating a page
    client.create_page(name="test", title="Test Page")
    # The create a new version with latest=False
    for idx in range(10):
        client.publish_page_version(
            "fakeid", str(idx), TEST_CONTENT.encode(), latest=True
        )
    result = client.list_page_versions("fakeid")
    assert len(result) == 10
    assert result == [
        PageVersion(
            page_id="fakeid",
            page_name="test",
            version=str(idx),
            checksum=TEST_CONTENT_MD5,
            created_timestamp=0,
        )
        for idx in range(10)
    ]
