# Product Flow Overview

This product generates structured luxury hotel brochures end-to-end. The brochure schema is the source of truth.

## Core Flow (V1 + V2.1)
1. User signs up and logs in
2. User enters a prompt
3. Backend extracts hotel data
4. AI generates text and image
5. Schema is built and stored
6. HTML brochure is rendered from schema
7. PNG and PDF are exported
8. User previews and downloads
9. User refines using natural language (V2.1)
10. Schema patch applied and re-rendered

## V2.2 Assets Flow
1. User uploads a hero image or gallery images
2. Schema updates with user asset URLs
3. Brochure re-renders immediately

## Output Artifacts
- `schema.json` (source of truth)
- `data.json` (render payload)
- `hero.png` or `hero_user.png`
- `brochure.png`
- `brochure.pdf`

All outputs are stored under `backend/output/runs/<brochure_id>/`.
