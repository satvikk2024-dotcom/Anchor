import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from llm.config import settings
from llm.client import complete
from llm.cache import cache_key, get_cached
from llm.schemas import CompleteRequest, CompleteResponse

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("anchor_llm_wrapper_starting", model=settings.ollama_model)
    yield
    logger.info("anchor_llm_wrapper_stopped")


app = FastAPI(title="Anchor LLM Wrapper", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.ollama_model}


@app.post("/complete", response_model=CompleteResponse)
async def complete_endpoint(req: CompleteRequest) -> CompleteResponse:
    resolved_model = req.model or settings.ollama_model
    was_cached = False
    if settings.cache_llm_calls:
        key = cache_key(resolved_model, req.prompt, req.system, req.json_mode)
        was_cached = (await get_cached(key)) is not None

    text = await complete(
        prompt=req.prompt,
        system=req.system,
        json_mode=req.json_mode,
        model=req.model,
    )
    return CompleteResponse(text=text, model=resolved_model, cached=was_cached)
