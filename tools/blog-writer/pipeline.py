from __future__ import annotations
import json
import re
import asyncio
import os
import httpx
from bs4 import BeautifulSoup
import anthropic

SITE_URL = os.environ.get("SITE_URL", "https://gtwog.ch")
MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _repair_json(s: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", s)


def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    candidate = fence.group(1).strip() if fence else None
    if candidate is None:
        m = re.search(r"\{[\s\S]*\}", raw)
        candidate = m.group(0) if m else None
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except Exception:
        pass
    try:
        return json.loads(_repair_json(candidate))
    except Exception:
        return None


async def _stream_phase(system: str, messages: list, max_tokens: int, emit, phase_name: str) -> tuple[dict | None, str]:
    loop = asyncio.get_running_loop()

    async def _stream_into_queue(msgs: list) -> str:
        raw = ""
        queue: asyncio.Queue = asyncio.Queue()

        def _worker():
            nonlocal raw
            with client.messages.stream(model=MODEL, max_tokens=max_tokens, system=system, messages=msgs) as stream:
                for text in stream.text_stream:
                    raw += text
                    loop.call_soon_threadsafe(queue.put_nowait, text)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        future = loop.run_in_executor(None, _worker)
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            await emit({"type": f"{phase_name}_delta", "text": chunk})
        await future
        return raw

    raw = await _stream_into_queue(messages)
    result = _extract_json(raw)
    if result:
        return result, raw

    await emit({"type": "status", "text": f"{phase_name}: invalid JSON — retrying..."})
    retry_messages = [
        *messages,
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": (
                "Your response contained invalid JSON. "
                "Return ONLY a valid JSON object, no markdown fences, no explanation. "
                "Use single quotes for all HTML attributes (e.g. class='foo') to avoid breaking the JSON string."
            ),
        },
    ]
    retry_raw = await _stream_into_queue(retry_messages)
    return _extract_json(retry_raw), retry_raw


async def scrape_url(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as http:
            r = await http.get(url, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title else url
        content = (
            soup.find("article") or soup.find("main") or
            soup.find(class_=re.compile(r"content|post|article", re.I)) or
            soup.body
        )
        text = content.get_text(separator=" ", strip=True) if content else ""
        return {"url": url, "title": title, "text": text[:4000]}
    except Exception as e:
        return {"url": url, "title": url, "text": f"[Could not fetch: {e}]"}


async def run_pipeline(topic: str, post_type: str, category_name: str, reference_urls: list[str], recent_posts: list[dict], emit):
    try:
        await emit({"type": "status", "text": "Gathering context..."})
        scraped = await asyncio.gather(*[scrape_url(u) for u in reference_urls])

        context_lines = [
            f'### Reference: "{item["title"]}"\nURL: {item["url"]}\n{item["text"]}'
            for item in scraped
            if item["text"] and not item["text"].startswith("[Could not fetch")
        ]

        internal_links_context = ""
        if recent_posts:
            lines = [f'- "{p["title"]}" → {SITE_URL}/en/blog/{p["slug"]}/' for p in recent_posts]
            internal_links_context = "### Existing Blog Posts (use for internal links)\n" + "\n".join(lines)

        context_block = "\n\n".join(context_lines)

        await emit({"type": "phase", "phase": "seo", "label": "SEO Strategist"})

        seo_system = f"""You are a senior SEO strategist specialising in B2B textile and custom clothing manufacturing content.
Your job is to produce a strategic brief for a blog article for gtwog.ch — a B2B custom clothing manufacturer serving sports clubs, retail brands, corporate buyers, and NGOs in Switzerland and Europe.

Target audience: procurement managers, brand owners, sports club administrators, marketing managers sourcing custom uniforms, sportswear, workwear, or retail collections.

Site URL: {SITE_URL}

Relevant B2B search queries to draw from:
- "custom sportswear manufacturer europe", "minimum order quantity custom clothing", "tech pack template",
  "sustainable fabric certification B2B", "sublimation printing vs screen printing", "private label clothing manufacturer",
  "custom workwear supplier switzerland", "factory direct clothing production", "GOTS certified manufacturer"

Return ONLY valid JSON with this exact structure:
{{
  "primary_keyword": "main B2B search term to rank for",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "search_intent": "informational | commercial | navigational",
  "heading_structure": [
    {{"tag": "h2", "text": "Section heading"}},
    {{"tag": "h3", "text": "Subsection (optional)"}}
  ],
  "internal_links": [
    {{"anchor": "suggested anchor text", "url": "full URL from existing posts list"}}
  ],
  "engagement_hooks": ["hook 1", "hook 2", "hook 3"],
  "meta_framework": {{
    "title": "Proposed meta title (max 60 chars)",
    "description": "Proposed meta description (max 160 chars)",
    "slug": "url-slug"
  }},
  "word_count_target": 900
}}"""

        seo_user = f"""Write an SEO brief for a blog article on this topic:

**{topic}**

Post type: {post_type}
Category: {category_name or "General"}

{internal_links_context}

{context_block}"""

        seo_brief, _ = await _stream_phase(seo_system, [{"role": "user", "content": seo_user}], max_tokens=1500, emit=emit, phase_name="seo")
        seo_brief = seo_brief or {}
        await emit({"type": "seo_done", "brief": seo_brief})

        await emit({"type": "phase", "phase": "writing", "label": "Content Writer"})

        writer_system = f"""You are an expert content writer for gtwog.ch, a B2B custom clothing manufacturer in Switzerland.

Your writing is authoritative, clear, and genuinely useful to procurement professionals. You write like a trusted industry expert, not a marketing copywriter. Your readers are making real business decisions — sourcing partners, production volumes, fabric specifications, certification requirements.

Site URL: {SITE_URL}

Domain expertise to weave in naturally:
- Fabrics: 100% cotton, polyester blends, recycled PET, Merino wool, stretch fabrics, sublimation-compatible polyester, fleece, woven vs knit constructions
- Techniques: embroidery, screen printing, DTF (Direct to Film), DTG (Direct to Garment), sublimation printing, heat transfer, dye sublimation
- Business terms: MOQ (minimum order quantity), tech packs, BOM (bill of materials), CMT (cut-make-trim), FOB pricing, lead times, sampling process, production runs
- Certifications: GOTS, OEKO-TEX, Fair Wear Foundation, GRS (Global Recycled Standard)
- Production countries: Portugal, Turkey, Bangladesh, China, India — trade-offs to discuss honestly
- Product categories: sportswear, workwear/uniforms, retail collections, promotional clothing, teamwear, corporate apparel, hospitality uniforms

Rules:
- Follow the heading structure from the SEO brief exactly (use <h2> and <h3> — no <h1> in body)
- Weave in primary and secondary keywords naturally, never stuffed
- Include internal links from the brief using suggested anchor text
- Open with one of the engagement hooks from the brief
- Aim for the word count target
- For case studies: use challenge → solution → result structure

CRITICAL: Use single quotes for ALL HTML attributes inside body (e.g. class='foo', href='...') so they do not break the JSON string.

Return ONLY valid JSON:
{{
  "title": "Article title (H1 level — not included in body HTML)",
  "body": "Full article HTML — <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>, <a href='...'>",
  "excerpt": "1-2 sentence teaser for listing pages (max 300 chars)",
  "meta_title": "SEO meta title from brief (max 60 chars)",
  "meta_description": "SEO meta description from brief (max 160 chars)",
  "slug": "url-slug from brief"
}}"""

        writer_user = f"""Write the blog article using this SEO brief:

```json
{json.dumps(seo_brief, indent=2)}
```

## Original topic
{topic}

{context_block}"""

        article, _ = await _stream_phase(writer_system, [{"role": "user", "content": writer_user}], max_tokens=4096, emit=emit, phase_name="writing")
        article = article or {}

        await emit({"type": "phase", "phase": "qa", "label": "QA Editor"})

        qa_system = f"""You are a QA editor for gtwog.ch B2B blog content.

Check and fix every one of the following issues. Add a "fixes" array listing every change made.

1. HTML structure — use <h2> for sections, <h3> for subsections. Fix out-of-order headings. No <h1> in body.
2. Internal links — every <a href> must use absolute URLs starting with {SITE_URL}. Prefix relative links. Remove placeholder or obviously wrong links.
3. Keyword density — primary keyword must appear in at least one <h2> and the opening <p>.
4. Excerpt — must be under 300 characters. Trim if needed.
5. Meta title — max 60 characters. Trim or rewrite if needed.
6. Meta description — max 160 characters. Trim or rewrite if needed.
7. Unclosed or malformed HTML tags — fix all.
8. Empty elements — remove <p></p>, <li></li>, etc.
9. B2B tone — rewrite any phrasing that sounds like B2C consumer copy rather than professional B2B.
10. Slug — must be lowercase, hyphen-separated, no special characters, max 80 chars.

CRITICAL: Use single quotes for ALL HTML attributes. Return ONLY valid JSON:
{{
  "title": "...",
  "body": "corrected HTML",
  "excerpt": "...",
  "meta_title": "...",
  "meta_description": "...",
  "slug": "...",
  "fixes": ["description of fix 1", "description of fix 2"]
}}"""

        qa_user = f"""QA and fix this article draft:

```json
{json.dumps(article, indent=2)}
```

Primary keyword from SEO brief: {seo_brief.get("primary_keyword", "")}"""

        qa_result, _ = await _stream_phase(qa_system, [{"role": "user", "content": qa_user}], max_tokens=4096, emit=emit, phase_name="qa")
        if qa_result:
            article = qa_result
        else:
            await emit({"type": "warning", "text": "QA phase could not parse — using writer output unchanged."})

        await emit({"type": "phase", "phase": "translation", "label": "German Translator"})

        translation_system = """You are a professional translator specialising in B2B textile and manufacturing content.
You translate English blog articles to natural, professional German for Swiss B2B audiences.

Language standard: Standard German (Hochdeutsch) — not Swiss dialect, not Austrian.
Register: professional, direct, precise. Use 'Sie' when addressing the reader.

Rules:
- Translate ALL visible text to fluent German
- Keep ALL HTML tags and attributes exactly unchanged (same single quotes, same structure)
- Keep all URLs, href values, and src attributes unchanged
- Keep brand names "G2G Textiles" unchanged
- Keep technical acronyms unchanged: MOQ, FOB, CMT, GOTS, OEKO-TEX, DTF, DTG, GRS, BOM — these are used as-is in German B2B contexts
- Excerpt must remain under 300 characters after translation

CRITICAL: Use single quotes for ALL HTML attributes. Return ONLY valid JSON:
{
  "title_de": "German title",
  "body_de": "Full HTML with all visible text translated, all tags/attrs preserved unchanged",
  "excerpt_de": "German excerpt (max 300 chars)"
}"""

        translation_user = f"""Translate this article to German:

Title: {article.get("title", "")}

Excerpt: {article.get("excerpt", "")}

Body:
{article.get("body", "")}"""

        translation_result, _ = await _stream_phase(translation_system, [{"role": "user", "content": translation_user}], max_tokens=4096, emit=emit, phase_name="translation")
        translation_result = translation_result or {}

        await emit({"type": "done", "article": {
            "title": article.get("title", ""),
            "title_de": translation_result.get("title_de", ""),
            "body": article.get("body", ""),
            "body_de": translation_result.get("body_de", ""),
            "excerpt": article.get("excerpt", ""),
            "excerpt_de": translation_result.get("excerpt_de", ""),
            "slug": article.get("slug", ""),
            "meta_title": article.get("meta_title", ""),
            "meta_description": article.get("meta_description", ""),
            "fixes": article.get("fixes", []),
        }})
        await emit(None)

    except Exception as e:
        await emit({"type": "error", "text": str(e)})
        await emit(None)
