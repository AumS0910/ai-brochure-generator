from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from jinja2 import Template
from playwright.async_api import async_playwright

TEMPLATE = Path("brochure.html").read_text(encoding="utf-8")


def _split_hotel_lines(name: str) -> tuple[str, str, str]:
    words = [w for w in name.strip().split() if w]
    if not words:
        return "", "", ""
    if len(words) == 1:
        return words[0], "", ""
    if len(words) == 2:
        return words[0], words[1], ""
    return words[0], words[1], " ".join(words[2:])


def _embed_hero_data_url(hero_url: str) -> str:
    if not hero_url or not hero_url.startswith("file://"):
        return hero_url
    file_path = Path(hero_url.replace("file:///", "")).resolve()
    if not file_path.exists():
        return hero_url
    suffix = file_path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def render_brochure_html(data: dict) -> str:
    amenities = data.get("amenities", [])
    if isinstance(amenities, list):
        amenities_text = " - ".join(amenities)
    else:
        amenities_text = str(amenities)

    line1, line2, line3 = _split_hotel_lines(data.get("hotel_name", ""))
    hero_url = _embed_hero_data_url(data.get("hero_url", ""))

    html = Template(TEMPLATE).render(
        hero_url=hero_url,
        location=data.get("location", ""),
        hotel_line1=line1,
        hotel_line2=line2,
        hotel_line3=line3,
        headline=data.get("headline", ""),
        description=data.get("description", ""),
        amenities=amenities_text,
    )
    return html


async def export_assets_async(html: str, out_dir: Path, base_name: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"{base_name}.png"
    pdf_path = out_dir / f"{base_name}.pdf"

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=2,
        )
        page = await context.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(png_path), full_page=False)
        await page.pdf(
            path=str(pdf_path),
            width="1080px",
            height="1350px",
            print_background=True,
        )
        await context.close()
        await browser.close()

    return {"png_path": str(png_path), "pdf_path": str(pdf_path)}
