# Backend

## Setup

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```
uvicorn main:app --reload
```

# Endpoints

- POST /auth/signup
- POST /auth/login
- POST /brochures/generate (auth required)
- GET /brochures/my (auth required)
- GET /files/{path}
