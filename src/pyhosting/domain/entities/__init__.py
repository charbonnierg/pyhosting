"""The `pyhosting.domain.entities` subpackage defines the entities used within the application.

Entities are pure python-object which defines the attributes and properties of a domain object.
They do not implement any processing logic (methods), but may implement validation logic (initialization).
"""
from .page import Page
from .version import Version

__all__ = ["Page", "Version"]
