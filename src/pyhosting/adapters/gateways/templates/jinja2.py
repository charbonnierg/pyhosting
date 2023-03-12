import jinja2

from pyhosting.domain.gateways import TemplateLoader


class Jinja2Loader(TemplateLoader):
    """Jinja2 template loader can be used to load templates from strings."""

    def __init__(self) -> None:
        """Create a new loader. Does not accept argument."""
        super().__init__()
        # Note that loader is provided but is NEVER used
        # Templates are only loaded from strings
        self._environment = jinja2.Environment(
            loader=jinja2.BaseLoader(), autoescape=True
        )

    def load_template(self, content: str) -> jinja2.Template:
        """Load a template from string (in-memory).

        This template can then be used to render a string according to some context.

        Arguments:
            content: a jinja2 template as a string

        Returns:
            A `jinja2.Template` object
        """
        return self._environment.from_string(content)
