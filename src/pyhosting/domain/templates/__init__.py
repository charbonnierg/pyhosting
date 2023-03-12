"""Submodule holding HTML templates.

Templates are written using Jinja2 syntax.
"""
from pathlib import Path

__TEMPLATES_ROOT__ = Path(__file__).parent
DEFAULT_TEMPLATE = __TEMPLATES_ROOT__ / "index.html.j2"

__all__ = ["DEFAULT_TEMPLATE"]
