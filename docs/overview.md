
**docs/overview.md**
```md
# Product Flow Overview

This product generates luxury hotel brochures end-to-end.

## Flow
1. User signs up and logs in
2. User enters a prompt
3. Backend extracts hotel data
4. AI generates text and image
5. HTML brochure is rendered
6. PNG and PDF are exported
7. User previews and downloads

## Output Artifacts
- `data.json`
- `hero.png`
- `brochure.png`
- `brochure.pdf`

All outputs are stored locally under `backend/output/runs/`.
