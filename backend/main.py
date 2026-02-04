from datetime import datetime
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import random
import re
import shutil
from pathlib import Path
from typing import Optional

import requests
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
    png_url: str
    pdf_url: str
    created_at: datetime


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

    data = {
        "hero_url": hero_url,
        "location": location,
        "hotel_name": hotel_name,
        "headline": text["headline"],
        "description": text["description"],
        "amenities": text["amenities"],
    }

    (run_dir / "prompt.txt").write_text(payload.prompt, encoding="utf-8")
    (run_dir / "data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    html = render_brochure_html(data)
    export_paths = await export_assets_async(html, run_dir, "brochure")

    brochure = Brochure(
        user_id=user.id,
        prompt=payload.prompt,
        hotel_name=hotel_name,
        location=location,
        headline=text["headline"],
        description=text["description"],
        amenities=json.dumps(text["amenities"]),
        png_path=str(Path(export_paths["png_path"]).relative_to("output")),
        pdf_path=str(Path(export_paths["pdf_path"]).relative_to("output")),
    )
    db.add(brochure)
    db.commit()
    db.refresh(brochure)

    return BrochureResponse(
        id=brochure.id,
        prompt=brochure.prompt,
        hotel_name=brochure.hotel_name,
        location=brochure.location,
        headline=brochure.headline,
        description=brochure.description,
        amenities=text["amenities"],
        png_url=f"/files/{brochure.png_path}",
        pdf_url=f"/files/{brochure.pdf_path}",
        created_at=brochure.created_at,
    )


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
        results.append(
            BrochureResponse(
                id=b.id,
                prompt=b.prompt,
                hotel_name=b.hotel_name,
                location=b.location,
                headline=b.headline,
                description=b.description,
                amenities=json.loads(b.amenities),
                png_url=f"/files/{b.png_path}",
                pdf_url=f"/files/{b.pdf_path}",
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
