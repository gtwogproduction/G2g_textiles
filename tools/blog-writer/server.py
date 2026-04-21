"""
G2G Blog Writer — FastAPI server.
Run from the project venv: uvicorn server:app --port 3001 --reload
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load tool .env first, then fall back to main project .env for shared keys (Cloudinary etc.)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ── Bootstrap Django ORM ──────────────────────────────────────────────────────
_django_path = os.environ.get("DJANGO_PROJECT_PATH", str(Path(__file__).parent.parent.parent))
if _django_path not in sys.path:
    sys.path.insert(0, _django_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "g2g_textiles.settings"))

import django
django.setup()

# ── Configure Cloudinary ──────────────────────────────────────────────────────
import cloudinary_client as cc
cc.configure()

# ── FastAPI imports ───────────────────────────────────────────────────────────
from typing import Optional
from asgiref.sync import sync_to_async
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import django_client as dc
import pipeline as pl

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PUBLIC_DIR = Path(__file__).parent / "public"
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

_INDEX_HTML = (PUBLIC_DIR / "index.html").read_text()


@app.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX_HTML


# ── Data endpoints ────────────────────────────────────────────────────────────
@app.get("/api/categories")
async def api_categories():
    return await sync_to_async(dc.get_categories)()


@app.get("/api/posts")
async def api_posts():
    return await sync_to_async(dc.get_recent_posts)()


@app.post("/api/scrape-url")
async def api_scrape_url(url: str = Form(...)):
    result = await pl.scrape_url(url)
    return result


@app.post("/api/upload-image")
async def api_upload_image(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    file_bytes = await image.read()
    result = await cc.upload_cover_image(file_bytes, image.filename)
    return result


# ── SSE generation endpoint ───────────────────────────────────────────────────
@app.post("/api/generate")
async def api_generate(
    topic: str = Form(...),
    post_type: str = Form("article"),
    category_name: str = Form(""),
    urls: str = Form("[]"),
):
    url_list = json.loads(urls)
    recent_posts = await sync_to_async(dc.get_recent_posts)(limit=30)

    queue: asyncio.Queue = asyncio.Queue()

    async def emit(obj):
        await queue.put(obj)

    async def event_stream():
        asyncio.create_task(
            pl.run_pipeline(
                topic=topic,
                post_type=post_type,
                category_name=category_name,
                reference_urls=url_list,
                recent_posts=recent_posts,
                emit=emit,
            )
        )
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Publish (save draft) ──────────────────────────────────────────────────────
class PublishPayload(BaseModel):
    title: str = ""
    title_de: str = ""
    slug: str = ""
    post_type: str = "article"
    category_id: Optional[int] = None
    excerpt: str = ""
    excerpt_de: str = ""
    body: str = ""
    body_de: str = ""
    meta_title: str = ""
    meta_description: str = ""
    cover_public_id: str = ""


@app.post("/api/publish")
async def api_publish(payload: PublishPayload):
    # Ensure slug is unique
    slug = payload.slug or payload.title.lower().replace(" ", "-")[:80]
    base_slug = slug
    counter = 1
    while await sync_to_async(dc.slug_exists)(slug):
        slug = f"{base_slug}-{counter}"
        counter += 1

    result = await sync_to_async(dc.create_draft_post)({
        "title": payload.title,
        "title_de": payload.title_de,
        "slug": slug,
        "post_type": payload.post_type,
        "category_id": payload.category_id,
        "excerpt": payload.excerpt,
        "excerpt_de": payload.excerpt_de,
        "body": payload.body,
        "body_de": payload.body_de,
        "meta_title": payload.meta_title,
        "meta_description": payload.meta_description,
        "cover_public_id": payload.cover_public_id,
    })
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
