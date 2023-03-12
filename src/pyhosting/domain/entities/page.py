import typing as t
from dataclasses import dataclass


@dataclass
class Page:
    """Page entity.

    A page is a namespace for a single page web application.

    Once a page is created, it is possible to create versions for the page.

    Versions are created by publishing a directory containing an index.html file, but page entities
    do not require any content to be created.

    A page entity may indicate a reference to its latest version available.
    """

    id: str
    """The page ID. Unique, generated automatically."""

    name: str
    """The page name. Unique. Only '-' and alphanumerical characters are allowed."""

    title: str
    """A human friendly title for the page."""

    description: str
    """A short description of the page application."""

    latest_version: t.Optional[str]
    """The latest version available for this page.

    This field always reference an existing page version.
    """
