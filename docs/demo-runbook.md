# Demo Runbook (Live Walkthrough)

## 1) Start Backend
```powershell
cd E:\ai-brochure-v1\backend
.\.venv\Scripts\activate
uvicorn main:app
```

## 2) Start Frontend
```powershell
cd E:\ai-brochure-v1\frontend
npm run dev
```

## 3) Demo Flow (Script)
1. Open `http://localhost:3000`
2. Go to **Signup** and create a new account
3. Login and land on **Dashboard**
4. Open **Generate**
5. Paste a prompt and click **Generate brochure**
6. Show the **Preview** image
7. Download **PNG** and **PDF**
8. Open **History** to show saved runs

## 4) V2.1 Edit Demo
1. In **Refine with AI**, enter:
   - `Hide amenities`
2. Show preview updates and amenities disappear
3. Enter:
   - `Show amenities and replace items with: Open-Air Spa, Wellness Suites, Sunrise Yoga, Quiet Garden, Saltwater Pool.`
4. Show amenities updated

## 5) V2.2 Assets Demo (Backend Only)
1. Upload a hero image via API (see `docs/assets-upload.md`)
2. Refresh preview to show new hero

## 6) Demo Prompts (pick 2–3)
- Create a luxury brochure for Aurora Vista Resort in Santorini with cliffside suites, a sunset terrace, and a private spa. Calm, editorial tone.
- Design a premium brochure for Azure Meridian Resort in Maldives with overwater villas, a glassy lagoon, and chef-led dining. Minimal, refined language.
- Generate a luxury brochure for Verdant Tide Resort in Seychelles featuring beachfront villas, palm-lined pool, and open-air wellness rituals.

## 7) Success Criteria
- PNG preview renders
- PDF download works
- History shows the latest run
- Refine updates preview
