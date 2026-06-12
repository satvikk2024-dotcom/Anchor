from pydantic import BaseModel


class CompleteRequest(BaseModel):
    prompt: str
    system: str | None = None
    json_mode: bool = False
    model: str | None = None


class CompleteResponse(BaseModel):
    text: str
    model: str
    cached: bool
