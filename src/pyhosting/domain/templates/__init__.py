import typing as t
from pathlib import Path

import jinja2

TEMPLATE_DIR = Path(__file__).parent / "content"
LOADER = jinja2.FileSystemLoader(TEMPLATE_DIR, followlinks=False)


def load_template_from_name(template: str) -> jinja2.Template:
    """Load a jinja2 template from name."""
    environment = jinja2.Environment(loader=LOADER, autoescape=True)
    return environment.get_template(template)


DEFAULT_TEMPLATE = load_template_from_name("index.html.j2")


def render_default_template(**context: t.Any) -> str:
    return DEFAULT_TEMPLATE.render(context)
