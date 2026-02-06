"""AI hero image generation helper with free-provider fallback support."""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import logging
import requests

logger = logging.getLogger(__name__)


def _build_prompt(prompt: str, hotel_name: str, location: str) -> str:
    """Compose a constrained visual prompt for consistent brochure heroes."""
    base = (
        "Luxury resort photography, exterior beachfront view, realistic, "
        "editorial travel magazine style, soft natural daylight, refined "
        "tropical architecture, ocean and sky visible, palm trees, "
        "infinity pool or lagoon, wide-angle composition"
    )
    return f"{base}. Hotel: {hotel_name}. Location: {location}. Prompt: {prompt}"


def _generate_hero_pollinations(prompt: str, hotel_name: str, location: str, run_dir: Path) -> Optional[str]:
    """Generate hero image through free Pollinations endpoint."""
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "hero.png"
    pollinations_prompt = _build_prompt(prompt, hotel_name, location)
    url = (
        f"https://image.pollinations.ai/prompt/{quote(pollinations_prompt)}"
        "?width=1080&height=1350&nologo=true&enhance=true"
    )
    try:
        resp = requests.get(url, timeout=90)
    except requests.RequestException as exc:
        logger.warning("Pollinations image request failed: %s", exc)
        return None
    if resp.status_code != 200:
        logger.warning("Pollinations image failed (status=%s): %s", resp.status_code, resp.text[:200])
        return None
    out_path.write_bytes(resp.content)
    logger.info("Pollinations: image generated at %s", out_path)
    return out_path.resolve().as_uri()


def generate_hero_image(prompt: str, hotel_name: str, location: str, run_dir: Path) -> Optional[str]:
    """Generate hero image using configured provider with automatic fallback."""
    image_provider = os.getenv("IMAGE_PROVIDER", "auto").strip().lower()
    token = os.getenv("HF_API_TOKEN")
    model = os.getenv("HF_SD_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    if image_provider == "pollinations":
        return _generate_hero_pollinations(prompt, hotel_name, location, run_dir)
    if not token:
        if image_provider == "auto":
            logger.warning("HF_API_TOKEN missing; falling back to free image provider.")
            return _generate_hero_pollinations(prompt, hotel_name, location, run_dir)
        logger.warning("HF_API_TOKEN missing; skipping SD generation.")
        return None
    logger.info("SD: using model %s", model)

    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": _build_prompt(prompt, hotel_name, location),
        "parameters": {
            "negative_prompt": (
                "interior, bedroom, ceiling, roof beams, people, text, words, letters, "
                "typography, logo, watermark, caption, signage, poster, brochure, flyer, "
                "illustration, cartoon, CGI, 3d, low quality, blurry"
            ),
            "num_inference_steps": 30,
            "guidance_scale": 7.0,
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        logger.warning("SD request failed (status=%s): %s", resp.status_code, resp.text[:200])
        if image_provider == "auto" and resp.status_code == 402:
            logger.info("SD credits unavailable; switching to free image provider.")
            return _generate_hero_pollinations(prompt, hotel_name, location, run_dir)
        return None
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        logger.warning("SD returned JSON instead of image: %s", resp.text[:200])
        if image_provider == "auto":
            return _generate_hero_pollinations(prompt, hotel_name, location, run_dir)
        return None

    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "hero.png"
    out_path.write_bytes(resp.content)
    logger.info("SD: image generated at %s", out_path)
    return out_path.resolve().as_uri()
