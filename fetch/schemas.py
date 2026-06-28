from typing import Any, Literal

from pydantic import BaseModel


class FetchRequest(BaseModel):
    url: str


class FetchResponse(BaseModel):
    url: str
    text: str
    length: int


class RenderPdfRequest(BaseModel):
    template: Literal["resume", "cover_letter"]
    data: dict[str, Any]
