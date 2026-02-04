# AI Luxury Brochure Generator (V1 ? V1.1)

A premium AI brochure generator for luxury hotels and resorts. Generate editorial-grade marketing brochures with cinematic AI imagery, refined copy, and instant PNG/PDF exports.

## Who It’s For
- Hospitality brands and boutique hotels
- Creative studios and marketing teams
- Product demos and portfolio presentations

## Tech Stack
**Backend**
- Python 3.11
- FastAPI
- SQLAlchemy + SQLite
- Playwright (Chromium)
- Hugging Face Inference (text + image)

**Frontend**
- Next.js 14 (App Router)
- Tailwind CSS
- Framer Motion

---

## Local Setup

### 1) Backend

**Requirements**
- Python **3.11** (required on Windows for Playwright stability)

**Create venv + install**
```powershell
cd E:\ai-brochure-v1\backend
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

**Create .env**
`backend/.env`
```
HF_API_TOKEN=your_hf_token_here
HF_T5_MODEL=meta-llama/Llama-3.1-8B-Instruct
HF_SD_MODEL=black-forest-labs/FLUX.1-schnell
JWT_SECRET=change-me-in-production
```

**Run backend**
```powershell
uvicorn main:app
```

### 2) Frontend

**Install + run**
```powershell
cd E:\ai-brochure-v1\frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`
Backend: `http://127.0.0.1:8000`

---

## Troubleshooting

**Playwright crash on Windows**
- Use Python **3.11** and run `uvicorn main:app` **without** `--reload`.
- Playwright relies on subprocess support; Windows + Python 3.11 is stable.

**Hugging Face 401 / 403**
- Regenerate token and ensure it has Inference access.
- Update `HF_API_TOKEN` in `backend/.env`.

**No image output**
- Ensure `python -m playwright install chromium` succeeded.

---

## API Overview (brief)
- `POST /auth/signup` ? create account
- `POST /auth/login` ? get JWT
- `POST /brochures/generate` ? generate brochure (auth required)
- `GET /brochures/my` ? list history (auth required)
- `GET /files/{path}` ? serve PNG/PDF

---

## Notes
- Output files are stored under `backend/output/runs/`.
- The brochure template is `backend/brochure.html`.
