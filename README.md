# AI Luxury Brochure Generator

An end-to-end application that turns a short hotel prompt into a polished brochure you can preview, refine, and export as PNG or PDF.

This project is built as a portfolio-quality product demo. It is not positioned as a public SaaS platform. The focus is clear product behavior, strong system design, and practical AI-assisted workflows.

## Why This Project Exists

Most AI design demos stop at a single generated image. Real brochure workflows need structure, iteration, and control.

This project solves that gap by combining:
- AI-assisted content generation
- Deterministic brochure rendering
- Editable schema-based data
- User-controlled assets and contact details
- Download-ready outputs

## What It Does

- Generates a complete brochure from a prompt
- Exports brochure output as PNG and PDF
- Supports user authentication and brochure history
- Lets users refine an existing brochure using plain-English instructions
- Supports user hero image and gallery uploads
- Embeds a QR code when website details are provided
- Uses free-fallback AI paths when paid provider credits are unavailable

## Live Demo

Live demo: [Add deployed demo URL here]  
Demo credentials: [Add recruiter-safe test account here]  
Demo video walkthrough: [Add link here]

## What a Recruiter Can Try in 30 Seconds

1. Sign up or log in
2. Generate a brochure from a prompt
3. Click "Refine with AI" and request a change such as "hide amenities" or "make tone calmer"
4. Download PNG/PDF output

That flow demonstrates prompt-to-product generation, structured editing, rendering, and export.

## Core Product Flow

1. User submits brochure input from the frontend
2. Backend builds or updates a structured brochure schema
3. AI services generate or refine text/image fields when needed
4. Rendering pipeline converts schema data into brochure HTML
5. HTML is exported to PNG/PDF
6. Assets and schema are persisted for history and later edits

## Advanced Usage

### User-Provided Text Override
If the prompt includes explicit fields:
- Headline:
- Description:
- Amenities:

the system validates that content and uses it directly instead of AI text generation. If fields are missing or invalid, it falls back to AI text generation.

### Conversational Refinement
The "Refine with AI" flow takes plain-English edit instructions and converts them into safe schema patches. Only allowed fields are updated; the brochure is re-rendered immediately.

### User Hero Image Upload
Users can upload a hero image during generation or after generation. When a user image is present, it is used directly instead of AI hero generation.

### QR Code Embedding
When contact website data is provided, the backend generates a QR code image and includes it in brochure output.

## Tech Stack

- Frontend: Next.js
- Backend: FastAPI
- Database: SQLite via SQLAlchemy
- Rendering: HTML/CSS to PNG/PDF using Playwright
- AI: Text and image generation with free fallback handling
- Auth: Token-based authentication

## Design Constraints

- Single deterministic brochure layout
- No free-form template editing
- Schema is the source of truth for brochure state
- Refinements update schema, then re-render output

## Repository Highlights

- Strong backend/frontend contract for generation and edit flows
- State persistence across history and refresh
- Practical guardrails for AI-generated patch updates
- Product-oriented features beyond one-shot generation

## Current Status

Feature-complete for portfolio demonstration:
- Generation
- Refinement
- User assets
- Contact + QR
- Export + history

## Future Direction (Optional)

- Additional brochure layout families
- Brand-level theme controls
- Deployment hardening and observability
