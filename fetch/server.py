import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from playwright.async_api import async_playwright, Browser

from fetch.config import settings
from fetch.schemas import FetchRequest, FetchResponse, RenderPdfRequest

logger = structlog.get_logger()

_state: dict[str, object] = {}

_jinja_env = Environment(
    loader=FileSystemLoader(settings.pdf_templates_dir),
    autoescape=select_autoescape(["html"]),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("anchor_fetch_service_starting")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    _state["playwright"] = playwright
    _state["browser"] = browser
    yield
    await browser.close()
    await playwright.stop()
    logger.info("anchor_fetch_service_stopped")


app = FastAPI(title="Anchor Fetch Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/fetch", response_model=FetchResponse)
async def fetch_endpoint(req: FetchRequest) -> FetchResponse:
    browser: Browser = _state["browser"]  # type: ignore[assignment]
    page = await browser.new_page()
    try:
        await page.goto(req.url, wait_until="networkidle", timeout=settings.fetch_timeout_ms)
        text = (await page.inner_text("body")).strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {req.url}: {e}")
    finally:
        await page.close()

    logger.info("fetch_done", url=req.url, chars=len(text))
    return FetchResponse(url=req.url, text=text, length=len(text))


@app.post("/render-pdf")
async def render_pdf_endpoint(req: RenderPdfRequest) -> Response:
    try:
        template = _jinja_env.get_template(f"{req.template}.html")
    except TemplateNotFound:
        raise HTTPException(status_code=404, detail=f"Unknown template: {req.template}")

    html = template.render(**req.data)

    browser: Browser = _state["browser"]  # type: ignore[assignment]
    page = await browser.new_page()
    try:
        await page.set_content(html, wait_until="load")
        pdf_bytes = await page.pdf(format="Letter", print_background=True)
    finally:
        await page.close()

    logger.info("render_pdf_done", template=req.template, bytes=len(pdf_bytes))
    return Response(content=pdf_bytes, media_type="application/pdf")
