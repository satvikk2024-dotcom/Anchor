from pathlib import Path

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

import httpx

from llm.config import settings
from llm.client import complete
from llm.cache import cache_key, get_cached
from llm.schemas import (
    CompleteRequest,
    CompleteResponse,
    SlackNotifyRequest,
    SlackNotifyResponse,
)

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


@app.post("/notify-slack", response_model=SlackNotifyResponse)
async def notify_slack(req: SlackNotifyRequest) -> SlackNotifyResponse:
    """
    Forward a message to the Slack Incoming Webhook configured via
    SLACK_WEBHOOK_URL. Keeps the webhook URL out of n8n workflow JSON
    (which is committed to git) — n8n calls this local endpoint instead.
    """
    if not settings.slack_webhook_url:
        raise HTTPException(status_code=503, detail="SLACK_WEBHOOK_URL not configured")

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        response = await client.post(settings.slack_webhook_url, json={"text": req.text})
        response.raise_for_status()

    return SlackNotifyResponse(sent=True)


def _resolve_system_prompt(req: CompleteRequest) -> str | None:
    if not req.system_prompt_name:
        return req.system

    prompts_dir = Path(settings.prompts_dir).resolve()
    prompt_path = (prompts_dir / f"{req.system_prompt_name}.md").resolve()
    if not prompt_path.is_relative_to(prompts_dir):
        raise HTTPException(status_code=400, detail="Invalid system_prompt_name")
    try:
        return prompt_path.read_text()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Unknown system_prompt_name: {req.system_prompt_name}"
        )


@app.post("/complete", response_model=CompleteResponse)
async def complete_endpoint(req: CompleteRequest) -> CompleteResponse:
    resolved_model = req.model or settings.ollama_model
    system = _resolve_system_prompt(req)

    was_cached = False
    if settings.cache_llm_calls:
        key = cache_key(resolved_model, req.prompt, system, req.json_mode)
        was_cached = (await get_cached(key)) is not None

    text = await complete(
        prompt=req.prompt,
        system=system,
        json_mode=req.json_mode,
        model=req.model,
    )
    return CompleteResponse(text=text, model=resolved_model, cached=was_cached)
