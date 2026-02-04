import os
from pathlib import Path
from typing import Optional

import logging
import requests

logger = logging.getLogger(__name__)


def _build_prompt(prompt: str, hotel_name: str, location: str) -> str:
    base = (
        "Luxury resort photography, exterior beachfront view, realistic, "
        "editorial travel magazine style, soft natural daylight, refined "
        "tropical architecture, ocean and sky visible, palm trees, "
        "infinity pool or lagoon, wide-angle composition"
    )
    return f"{base}. Hotel: {hotel_name}. Location: {location}. Prompt: {prompt}"


def generate_hero_image(prompt: str, hotel_name: str, location: str, run_dir: Path) -> Optional[str]:
    token = os.getenv("HF_API_TOKEN")
    model = os.getenv("HF_SD_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    if not token:
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
        return None
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        logger.warning("SD returned JSON instead of image: %s", resp.text[:200])
        return None

    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "hero.png"
    out_path.write_bytes(resp.content)
    logger.info("SD: image generated at %s", out_path)
    return out_path.resolve().as_uri()
