import pytest
from _pytest.fixtures import SubRequest

from pyhosting.adapters.gateways.templates import Jinja2Loader
from pyhosting.domain.gateways import TemplateLoader


@pytest.fixture
def templates(request: SubRequest):
    param = request.param
    yield param()


@pytest.mark.parametrize("templates", [Jinja2Loader], indirect=True)
class TestTemplatesAdapters:
    def test_load_template_from_string(self, templates: TemplateLoader):
        template = templates.load_template("{{ something }}")
        assert template.render(something="hello world") == "hello world"
