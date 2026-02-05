from datetime import datetime
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import os
import random
import re
import shutil
from pathlib import Path
from typing import Optional, Any

import requests
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from auth import hash_password, verify_password, create_access_token, get_current_user
from ai_image import generate_hero_image
from ai_text import generate_copy
from database import Base, engine, get_db
from models import User, Brochure
from render import render_brochure_html, export_assets_async

load_dotenv()

BASE_OUTPUT = Path("output/runs")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

app = FastAPI(title="AI Luxury Brochure", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def _ensure_schema_column() -> None:
    with engine.connect() as conn:
        rows = conn.execute(sql_text("PRAGMA table_info(brochures)")).fetchall()
        cols = [row[1] for row in rows]
        if "schema_json" not in cols:
            conn.execute(
                sql_text("ALTER TABLE brochures ADD COLUMN schema_json TEXT NOT NULL DEFAULT '{}'"),
            )
            conn.commit()


_ensure_schema_column()


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GenerateRequest(BaseModel):
    prompt: str
    hero_url: Optional[str] = None
    hero_path: Optional[str] = None


class BrochureResponse(BaseModel):
    id: int
    prompt: str
    hotel_name: str
    location: str
    headline: str
    description: str
    amenities: list[str]
    schema: Optional[dict] = None
    png_url: str
    pdf_url: str
    created_at: datetime


class EditRequest(BaseModel):
    instruction: str


DEFAULT_AMENITIES = [
    "Infinity pool",
    "Spa and wellness",
    "Ocean-view suites",
    "Gourmet dining",
    "Private beach",
    "Rooftop lounge",
    "Concierge service",
    "Signature cocktails",
]

TEMPLATES = [
    {
        "headline": "{name} - A Quiet Luxury in {location}",
        "description": "Sunlit suites, calm waters, and tailored service set a new pace for escape. {name} blends modern design with the natural beauty of {location} for a stay that feels effortless.",
    },
    {
        "headline": "Wake Up to {location} at {name}",
        "description": "A refined resort where soft light, open air, and curated experiences come together. Discover a serene stay with thoughtful details and elevated comfort.",
    },
    {
        "headline": "{name} - Modern Coastal Retreat",
        "description": "A minimalist sanctuary with expansive views, warm textures, and calm spaces. Indulge in slow mornings and golden evenings in {location}.",
    },
]

VERB_BLACKLIST = {"design", "create", "generate", "make", "build", "craft", "produce"}

SCHEMA_PATCH_SYSTEM_PROMPT = (
    "You are a schema patch generator. Convert a user's instruction into a JSON Patch for a brochure schema.\n\n"
    "STRICT RULES:\n"
    "- Output ONLY valid JSON. No markdown, no commentary.\n"
    "- Only include keys that must change. Do not return the full schema.\n"
    "- Allowed top-level keys: \"meta\", \"assets\", \"sections\".\n"
    "- Allowed section keys: hero, about, amenities, gallery.\n"
    "- Each section supports: \"visibility\": true | false.\n"
    "- Contact fields are READ-ONLY. Never add or modify: sections.contact.*\n"
    "- Do NOT add new sections or keys.\n"
    "- Do NOT change \"hotel_name\" or \"location\" unless explicitly requested.\n"
    "- Image edits are restricted to:\n"
    "  assets.hero_image.prompt_modifier\n"
    "  assets.hero_image.mood\n"
    "  assets.hero_image.time_of_day\n"
    "- Do NOT change assets.hero_image.url unless user explicitly uploaded an image.\n"
    "- Enforce constraints:\n"
    "  - hero.headline <= 80 chars\n"
    "  - hero.tagline <= 90 chars\n"
    "  - hero.description <= 320 chars\n"
    "  - about.body <= 500 chars\n"
    "  - amenities.items length 4–6\n"
    "  - each amenities item <= 6 words\n"
    "- If instruction is ambiguous or disallowed, return:\n"
    "  {\"error\":\"needs_clarification\",\"message\":\"<short reason>\"}\n"
    "- If instruction maps to no valid changes, return:\n"
    "  {\"error\":\"no_changes\",\"message\":\"No valid edits detected.\"}\n"
    "- Unmentioned sections must remain untouched.\n\n"
    "Return JSON only."
)


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "brochure"


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _extract_location(text: str) -> str | None:
    m = re.search(r"\b(?:in|at|near|on)\s+([A-Za-z ,.'\-]{3,60})", text, re.IGNORECASE)
    if m:
        loc = m.group(1)
        loc = re.split(r"\b(with|featuring|that|which|for|and)\b", loc, maxsplit=1, flags=re.IGNORECASE)[0]
        return loc.strip(" ,.")
    return None


def _clean_name(name: str, location: str | None) -> str:
    name = re.sub(r"\s+\b(in|at|near|on)\b\s+.+$", "", name, flags=re.IGNORECASE).strip(" ,.-")
    if location:
        name = re.sub(re.escape(location), "", name, flags=re.IGNORECASE).strip(" ,.-")
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name


def _is_valid_name(name: str | None, location: str | None) -> bool:
    if not name:
        return False
    words = name.split()
    if len(words) > 6:
        return False
    lowered = name.lower()
    if any(re.search(rf"\b{re.escape(v)}\b", lowered) for v in VERB_BLACKLIST):
        return False
    if location and re.search(re.escape(location), lowered, re.IGNORECASE):
        return False
    return True


def _fallback_name(text: str, location: str | None) -> str | None:
    caps = re.findall(r"\b[A-Z][A-Za-z'&\-]+\b", text)
    location_tokens = set(re.findall(r"[A-Za-z'&\-]+", location or ""))
    cleaned = []
    for w in caps:
        if w.lower() in VERB_BLACKLIST:
            continue
        if w in location_tokens:
            continue
        cleaned.append(w)
    if not cleaned:
        return None
    return " ".join(cleaned[:5]).strip() or None


def _extract_name(text: str, location: str | None) -> str | None:
    m = re.search(r"\bfor\s+([A-Za-z0-9'&\- ,]{3,80})", text, re.IGNORECASE)
    if m:
        candidate = _clean_name(m.group(1), location)
        if _is_valid_name(candidate, location):
            return candidate
    m = re.search(r'"([^\"]{3,80})"', text)
    if m:
        candidate = _clean_name(m.group(1), location)
        if _is_valid_name(candidate, location):
            return candidate
    patterns = [
        r"([A-Z][A-Za-z0-9'&\- ]+\b(?:Hotel|Resort|Lodge|Suites|Inn|Retreat|Palace|Villas))",
        r"([A-Z][A-Za-z0-9'&\- ]+\b(?:Spa|Club|Estate))",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            candidate = _clean_name(m.group(1), location)
            if _is_valid_name(candidate, location):
                return candidate
    return None


def extract_hotel_info(prompt: str) -> tuple[str, str]:
    text = prompt.strip()
    location = _extract_location(text) or "Amalfi Coast, Italy"
    name = _extract_name(text, location)
    if not name:
        name = _fallback_name(text, location)
    if not name:
        name = "Luxury Resort"
    return name, location


def generate_text(prompt: str, hotel_name: str, location: str) -> dict:
    ai_text = generate_copy(prompt, hotel_name, location)
    if ai_text:
        return ai_text
    tpl = random.choice(TEMPLATES)
    headline = tpl["headline"].format(name=hotel_name, location=location)
    description = tpl["description"].format(name=hotel_name, location=location)
    amenities = random.sample(DEFAULT_AMENITIES, k=6)
    return {
        "headline": headline,
        "description": description,
        "amenities": amenities,
    }


def _clamp_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len].rsplit(" ", 1)[0].strip()
    return trimmed or text[:max_len]


def _trim_amenity_words(text: str, max_words: int = 6) -> str:
    parts = [w for w in text.split() if w]
    return " ".join(parts[:max_words])


def _normalize_amenities(items: Any) -> list[str]:
    if isinstance(items, list):
        cleaned = [str(i).strip() for i in items if str(i).strip()]
    elif isinstance(items, str):
        cleaned = [s.strip() for s in re.split(r"[|,\n]+", items) if s.strip()]
    else:
        cleaned = []
    cleaned = [_trim_amenity_words(item, 6) for item in cleaned if item]
    return cleaned


def build_schema(
    prompt: str,
    hotel_name: str,
    location: str,
    hero_url: str,
    text: dict,
    hero_source: str,
) -> dict:
    return {
        "brochure_id": "",
        "version": 2,
        "preset": "editorial_luxury",
        "meta": {
            "hotel_name": hotel_name,
            "location": location,
            "tone": "editorial luxury",
            "language": "en",
        },
        "assets": {
            "hero_image": {
                "source": hero_source,
                "url": hero_url,
                "alt": f"{hotel_name} in {location}",
                "prompt_modifier": "",
                "mood": "",
                "time_of_day": "",
            },
            "gallery": [],
        },
        "sections": {
            "hero": {
                "headline": text.get("headline", ""),
                "tagline": "",
                "description": text.get("description", ""),
                "visibility": True,
            },
            "about": {
                "title": "About",
                "body": "",
                "visibility": True,
            },
            "amenities": {
                "title": "Amenities",
                "items": text.get("amenities", []),
                "visibility": True,
            },
            "gallery": {
                "enabled": False,
                "caption": "",
                "visibility": True,
            },
            "contact": {
                "email": None,
                "phone": None,
                "website": None,
                "address": None,
                "qr_code_url": None,
            },
        },
    }


def schema_to_render_data(schema: dict) -> dict:
    meta = schema.get("meta", {})
    sections = schema.get("sections", {})
    assets = schema.get("assets", {})

    hero = sections.get("hero", {})
    amenities = sections.get("amenities", {})

    hero_visible = hero.get("visibility", True)
    amenities_visible = amenities.get("visibility", True)

    hero_url = assets.get("hero_image", {}).get("url", "")

    return {
        "hero_url": hero_url,
        "location": meta.get("location", ""),
        "hotel_name": meta.get("hotel_name", ""),
        "headline": hero.get("headline", "") if hero_visible else "",
        "description": hero.get("description", "") if hero_visible else "",
        "amenities": amenities.get("items", []) if amenities_visible else [],
    }


def _schema_from_record(brochure: Brochure) -> dict:
    run_dir = Path("output") / brochure.png_path
    hero_path = run_dir.parent / "hero.png"
    hero_url = hero_path.resolve().as_uri() if hero_path.exists() else ""
    text = {
        "headline": brochure.headline,
        "description": brochure.description,
        "amenities": json.loads(brochure.amenities),
    }
    return build_schema(
        brochure.prompt,
        brochure.hotel_name,
        brochure.location,
        hero_url,
        text,
        "ai",
    )


def apply_schema_patch(schema: dict, patch: dict) -> dict:
    if not isinstance(patch, dict):
        return {"error": "needs_clarification", "message": "Invalid patch format."}
    if patch.get("error"):
        return patch
    if not patch:
        return {"error": "no_changes", "message": "No valid edits detected."}

    logging.info("Patch before normalization keys: %s", list(patch.keys()))

    # Convert JSON Patch style into schema patch.
    if set(patch.keys()) >= {"op", "path"} and isinstance(patch.get("path"), str):
        op = str(patch.get("op", "")).lower()
        path = patch.get("path", "")
        value = patch.get("value")
        if op in {"add", "replace"} and path.startswith("/"):
            parts = [p for p in path.strip("/").split("/") if p]
            if parts:
                root = parts[0]
                rest = parts[1:]
                if root in {"sections", "meta", "assets"} and rest:
                    cursor: dict = {root: {}}
                    node = cursor[root]
                    for idx, key in enumerate(rest):
                        if idx == len(rest) - 1:
                            node[key] = value
                        else:
                            node[key] = {}
                            node = node[key]
                    patch = cursor

    # Unwrap common wrapper keys if the model nests the patch.
    for wrapper_key in ("patch", "changes", "result", "data", "response", "output"):
        if wrapper_key in patch and isinstance(patch[wrapper_key], dict):
            patch = patch[wrapper_key]
            break

    # Normalize common minimal intents into a valid patch shape.
    # Example: {"action":"hide","section":"amenities"} -> {"sections":{"amenities":{"visibility":false}}}
    if "sections" not in patch and "section" in patch:
        section_name = str(patch.get("section", "")).strip().lower()
        action = str(patch.get("action", "")).strip().lower()
        visibility = patch.get("visibility")
        if visibility is None and action in {"hide", "remove", "disable"}:
            visibility = False
        if visibility is None and action in {"show", "enable", "add"}:
            visibility = True
        if section_name in {"hero", "about", "amenities", "gallery"} and isinstance(visibility, bool):
            patch = {"sections": {section_name: {"visibility": visibility}}}

    allowed_top = {"meta", "assets", "sections"}
    # If the model returned only unknown keys but one of them contains a valid patch, unwrap it.
    if not any(k in allowed_top for k in patch.keys()):
        for value in patch.values():
            if isinstance(value, dict) and any(k in allowed_top for k in value.keys()):
                patch = value
                break
    unknown_top = [k for k in patch.keys() if k not in allowed_top]
    if unknown_top:
        # If no valid keys remain, fail fast.
        if not any(k in allowed_top for k in patch.keys()):
            return {
                "error": "needs_clarification",
                "message": "Invalid top-level keys. Allowed: meta, assets, sections.",
            }
        # Strip unknown keys but continue with valid ones.
        patch = {k: v for k, v in patch.items() if k in allowed_top}

    logging.info("Patch after normalization keys: %s", list(patch.keys()))

    if "sections" in patch and "contact" in (patch.get("sections") or {}):
        return {"error": "needs_clarification", "message": "Contact fields are read-only."}

    allowed_sections = {"hero", "about", "amenities", "gallery"}
    allowed_section_fields = {
        "hero": {"headline", "tagline", "description", "visibility"},
        "about": {"body", "visibility"},
        "amenities": {"items", "visibility"},
        "gallery": {"enabled", "caption", "visibility"},
    }

    if "sections" in patch:
        for section_key, section_patch in (patch.get("sections") or {}).items():
            if section_key not in allowed_sections:
                return {"error": "needs_clarification", "message": "Invalid section key."}
            if not isinstance(section_patch, dict):
                return {"error": "needs_clarification", "message": "Invalid section patch."}
            for field in section_patch.keys():
                if field not in allowed_section_fields[section_key]:
                    return {"error": "needs_clarification", "message": "Invalid section field."}

    if "assets" in patch:
        assets_patch = patch.get("assets") or {}
        hero_patch = assets_patch.get("hero_image")
        if hero_patch:
            if not isinstance(hero_patch, dict):
                return {"error": "needs_clarification", "message": "Invalid hero_image patch."}
            allowed_hero_fields = {"prompt_modifier", "mood", "time_of_day"}
            if any(k not in allowed_hero_fields for k in hero_patch.keys()):
                return {"error": "needs_clarification", "message": "Invalid hero_image field."}
        if any(k not in {"hero_image"} for k in assets_patch.keys()):
            return {"error": "needs_clarification", "message": "Invalid assets field."}

    merged = json.loads(json.dumps(schema))

    def _deep_merge(base: dict, inc: dict) -> dict:
        for k, v in inc.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = _deep_merge(base.get(k, {}), v)
            else:
                base[k] = v
        return base

    merged = _deep_merge(merged, patch)

    hero = merged.get("sections", {}).get("hero", {})
    if "headline" in hero:
        hero["headline"] = _clamp_text(str(hero["headline"]), 80)
    if "tagline" in hero:
        hero["tagline"] = _clamp_text(str(hero["tagline"]), 90)
    if "description" in hero:
        hero["description"] = _clamp_text(str(hero["description"]), 320)

    about = merged.get("sections", {}).get("about", {})
    if "body" in about:
        about["body"] = _clamp_text(str(about["body"]), 500)

    amenities = merged.get("sections", {}).get("amenities", {})
    amenities_visible = amenities.get("visibility", True)
    if "items" in amenities:
        items = _normalize_amenities(amenities.get("items", []))
        if amenities_visible and len(items) < 4:
            return {"error": "needs_clarification", "message": "Amenities require 4–6 items."}
        amenities["items"] = items[:6]

    if json.dumps(merged, sort_keys=True) == json.dumps(schema, sort_keys=True):
        return {"error": "no_changes", "message": "No valid edits detected."}

    return merged


def generate_schema_patch(schema: dict, instruction: str) -> dict:
    token = os.getenv("HF_API_TOKEN")
    model = os.getenv("HF_T5_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    if not token:
        return {"error": "needs_clarification", "message": "Model token missing."}

    messages = [
        {"role": "system", "content": SCHEMA_PATCH_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Current schema:\n{json.dumps(schema)}\n\nUser instruction:\n{instruction}\n\nReturn ONLY the JSON patch.",
        },
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://router.huggingface.co/v1/chat/completions"

    resp = requests.post(url, headers=headers, json=payload, timeout=45)
    if resp.status_code != 200:
        return {"error": "needs_clarification", "message": "Patch generation failed."}
    try:
        data = resp.json()
    except ValueError:
        return {"error": "needs_clarification", "message": "Patch generation failed."}

    content = ""
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            content = (choices[0].get("message") or {}).get("content", "")

    if not content:
        return {"error": "needs_clarification", "message": "Patch generation failed."}
    logging.info("Patch raw content: %s", content[:500])
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"error": "needs_clarification", "message": "Patch generation failed."}
        else:
            return {"error": "needs_clarification", "message": "Patch generation failed."}

    if isinstance(parsed, dict) and parsed.get("error"):
        return parsed
    if isinstance(parsed, dict):
        if "patch" in parsed and isinstance(parsed["patch"], dict):
            return parsed["patch"]
        if "changes" in parsed and isinstance(parsed["changes"], dict):
            return parsed["changes"]
    if isinstance(parsed, dict):
        logging.info("Patch parsed keys: %s", list(parsed.keys()))
    return parsed if isinstance(parsed, dict) else {"error": "needs_clarification", "message": "Patch generation failed."}


def _download_image(url: str, out_path: Path) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return str(out_path)


def _prepare_hero(
    prompt: str,
    hotel_name: str,
    location: str,
    hero_url: Optional[str],
    hero_path: Optional[str],
    run_dir: Path,
) -> str:
    if hero_url:
        local_path = run_dir / "hero.png"
        _download_image(hero_url, local_path)
        return local_path.resolve().as_uri()

    if hero_path:
        src = Path(hero_path).expanduser().resolve()
        if src.exists():
            local_path = run_dir / src.name
            shutil.copy2(src, local_path)
            return local_path.resolve().as_uri()

    ai_hero = generate_hero_image(prompt, hotel_name, location, run_dir)
    if ai_hero:
        return ai_hero

    return ""


def _safe_path(path: str) -> Path:
    base = Path("output").resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return target


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if len(payload.password) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"user_id": user.id, "email": user.email})
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if len(payload.password) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": user.id, "email": user.email})
    return TokenResponse(access_token=token)


@app.post("/brochures/generate", response_model=BrochureResponse)
async def generate_brochure(
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not payload.prompt or len(payload.prompt.strip()) < 5:
        raise HTTPException(status_code=400, detail="Prompt is too short")

    hotel_name, location = extract_hotel_info(payload.prompt)
    text = generate_text(payload.prompt, hotel_name, location)

    run_id = f"{_timestamp()}_{_slugify(hotel_name)}"
    run_dir = BASE_OUTPUT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    hero_url = _prepare_hero(payload.prompt, hotel_name, location, payload.hero_url, payload.hero_path, run_dir)
    if hero_url:
        logging.info("Hero image resolved: %s", hero_url)
    else:
        logging.info("Hero image missing; using layout without image.")

    hero_source = "user" if payload.hero_url or payload.hero_path else "ai"
    schema = build_schema(payload.prompt, hotel_name, location, hero_url, text, hero_source)
    render_data = schema_to_render_data(schema)

    (run_dir / "prompt.txt").write_text(payload.prompt, encoding="utf-8")
    (run_dir / "data.json").write_text(json.dumps(render_data, indent=2), encoding="utf-8")
    (run_dir / "schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")

    html = render_brochure_html(render_data)
    export_paths = await export_assets_async(html, run_dir, "brochure")

    brochure = Brochure(
        user_id=user.id,
        prompt=payload.prompt,
        hotel_name=hotel_name,
        location=location,
        headline=text["headline"],
        description=text["description"],
        amenities=json.dumps(text["amenities"]),
        schema_json=json.dumps(schema),
        png_path=Path(export_paths["png_path"]).relative_to("output").as_posix(),
        pdf_path=Path(export_paths["pdf_path"]).relative_to("output").as_posix(),
    )
    db.add(brochure)
    db.commit()
    db.refresh(brochure)

    png_url = f"/files/{brochure.png_path}".replace("\\", "/")
    pdf_url = f"/files/{brochure.pdf_path}".replace("\\", "/")
    return BrochureResponse(
        id=brochure.id,
        prompt=brochure.prompt,
        hotel_name=brochure.hotel_name,
        location=brochure.location,
        headline=brochure.headline,
        description=brochure.description,
        amenities=text["amenities"],
        schema=schema,
        png_url=png_url,
        pdf_url=pdf_url,
        created_at=brochure.created_at,
    )


@app.post("/brochures/{brochure_id}/edit")
async def edit_brochure(
    brochure_id: int,
    payload: EditRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not payload.instruction or len(payload.instruction.strip()) < 3:
        return {"error": "needs_clarification", "message": "Instruction is too short."}

    brochure = (
        db.query(Brochure)
        .filter(Brochure.id == brochure_id, Brochure.user_id == user.id)
        .first()
    )
    if not brochure:
        raise HTTPException(status_code=404, detail="Brochure not found")

    current_schema = None
    if brochure.schema_json:
        try:
            current_schema = json.loads(brochure.schema_json)
        except json.JSONDecodeError:
            current_schema = None
    if not current_schema:
        current_schema = _schema_from_record(brochure)

    patch = generate_schema_patch(current_schema, payload.instruction.strip())
    if isinstance(patch, dict) and patch.get("error"):
        return patch

    merged = apply_schema_patch(current_schema, patch)
    if isinstance(merged, dict) and merged.get("error"):
        return merged

    render_data = schema_to_render_data(merged)
    html = render_brochure_html(render_data)

    run_dir = (Path("output") / brochure.png_path).resolve().parent
    export_paths = await export_assets_async(html, run_dir, "brochure")

    brochure.schema_json = json.dumps(merged)
    brochure.headline = render_data.get("headline", "")
    brochure.description = render_data.get("description", "")
    brochure.amenities = json.dumps(render_data.get("amenities", []))
    output_root = Path("output").resolve()
    brochure.png_path = Path(export_paths["png_path"]).resolve().relative_to(output_root).as_posix()
    brochure.pdf_path = Path(export_paths["pdf_path"]).resolve().relative_to(output_root).as_posix()
    db.add(brochure)
    db.commit()
    db.refresh(brochure)

    png_url = f"/files/{brochure.png_path}".replace("\\", "/")
    pdf_url = f"/files/{brochure.pdf_path}".replace("\\", "/")
    return {
        "schema": merged,
        "png_url": png_url,
        "pdf_url": pdf_url,
    }


@app.get("/brochures/my", response_model=list[BrochureResponse])
def my_brochures(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = (
        db.query(Brochure)
        .filter(Brochure.user_id == user.id)
        .order_by(Brochure.created_at.desc())
        .all()
    )
    results = []
    for b in items:
        png_url = f"/files/{b.png_path}".replace("\\", "/")
        pdf_url = f"/files/{b.pdf_path}".replace("\\", "/")
        results.append(
            BrochureResponse(
                id=b.id,
                prompt=b.prompt,
                hotel_name=b.hotel_name,
                location=b.location,
                headline=b.headline,
                description=b.description,
                amenities=json.loads(b.amenities),
                schema=json.loads(b.schema_json) if b.schema_json else None,
                png_url=png_url,
                pdf_url=pdf_url,
                created_at=b.created_at,
            )
        )
    return results


@app.get("/files/{path:path}")
def get_file(path: str):
    target = _safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target)
