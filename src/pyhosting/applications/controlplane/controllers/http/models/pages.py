import typing as t

from pydantic import BaseModel

from pyhosting.domain.entities import Page


class GetPageResult(BaseModel):
    document: Page


class ListPagesResult(BaseModel):
    documents: t.List[Page]


class CreatePageOptions(BaseModel):
    name: str
    title: t.Optional[str] = None
    description: t.Optional[str] = None


class CreatePageResult(BaseModel):
    document: Page
