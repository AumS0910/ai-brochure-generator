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

## 4) Demo Prompts (pick 2–3)
- Create a luxury brochure for Aurora Vista Resort in Santorini with cliffside suites, a sunset terrace, and a private spa. Calm, editorial tone.
- Design a premium brochure for Azure Meridian Resort in Maldives with overwater villas, a glassy lagoon, and chef-led dining. Minimal, refined language.
- Generate a luxury brochure for Verdant Tide Resort in Seychelles featuring beachfront villas, palm-lined pool, and open-air wellness rituals.

## 5) Success Criteria
- PNG preview renders
- PDF download works
- History shows the latest run
