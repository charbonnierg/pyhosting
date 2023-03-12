from pyhosting.adapters.clients.http import PagesAPIHTTPClient


def test_http_client_init():
    client = PagesAPIHTTPClient("http://somewhere")
    assert client.http.base_url == "http://somewhere"
