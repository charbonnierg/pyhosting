from pydantic import BaseModel

from pyhosting.domain.entities.version import PageVersion


class CreatePageVersionResult(BaseModel, extra="allow"):
    """Result returned after successfully created page version."""

    document: PageVersion
