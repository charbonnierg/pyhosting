import typing as t
from dataclasses import dataclass


@dataclass
class Page:
    """Page entity."""

    id: str
    name: str
    title: str
    description: str
    latest_version: t.Optional[str]
