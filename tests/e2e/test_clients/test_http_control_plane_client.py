from pyhosting.adapters.clients.pages.http import HTTPPagesClient


def test_http_client_init():
    client = HTTPPagesClient("http://somewhere")
    assert client.http.base_url == "http://somewhere"
