# MboaShield Architecture

## Current state

Today the product is a lightweight monolith:

```text
Browser UI (frontend/)
        |
        v
FastAPI app (backend/app/main.py)
        |
        +-- services/text_check.py
        +-- services/impersonation.py
        +-- services/media_check.py
        +-- services/audio_check.py
        +-- services/ambassadors.py
        |
        +-- SQLite persistence (backend/app/db.py)

Static data (data/*.json)
Demo samples (frontend/static/samples/)
```

This is acceptable for an early product, but not yet a full platform.

## Product-first target

MboaShield should evolve into a trust-and-safety platform with four durable product domains:

1. `verification`
   Text rumours, links, source verification, scam signals.
2. `impersonation`
   Fake account detection, registry matching, institution protection.
3. `synthetic_media`
   Audio, image, and later video risk analysis.
4. `citizenship`
   Mboa Ambassadors, civic education, certificates, awareness programs.

## Target backend shape

```text
backend/app/
  api/
    v1/
      routes/
        verification.py
        impersonation.py
        media.py
        ambassadors.py
        institutions.py
  core/
    config.py
    logging.py
    security.py
  db/
    session.py
    models/
    repositories/
  domains/
    verification/
      service.py
      scoring.py
      schemas.py
    impersonation/
      service.py
      matching.py
      schemas.py
    synthetic_media/
      audio.py
      image.py
      video.py
    citizenship/
      lessons.py
      certificates.py
  services/
    sources.py
    institutions.py
```

## Data architecture

The product should move through three storage stages:

1. `Now`: SQLite for local persistence and product development speed
2. `Next`: PostgreSQL for multi-user production use
3. `Later`: object storage for uploaded files and background processing

### Core entities

- `users`
- `institutions`
- `official_handles`
- `verification_checks`
- `verification_signals`
- `incident_reports`
- `source_registry`
- `lessons`
- `lesson_completions`
- `certificates`

## Guiding engineering rules

- Keep a **modular monolith** before introducing microservices
- Every detection result must return **risk + explanation + next action**
- Prefer **typed schemas** at API boundaries
- Separate **domain logic** from HTTP route handlers
- Build with **auditability** in mind: checks must be stored and traceable
- Optimize for **mobile-first UX** and **low-bandwidth Cameroon realities**

## Immediate roadmap

### Phase 1: Foundation

- Add persistent storage for checks and certificates
- Separate routing, domain logic, and storage concerns
- Add environment-based config
- Expand automated tests

### Phase 2: Trust engine

- Add structured verification signals
- Improve scoring consistency across text, audio, image, and impersonation
- Build a shared explanation layer
- Add institution/source management workflows

### Phase 3: Real product workflows

- User accounts
- Institution dashboard
- Incident review queue
- History, search, and reporting

### Phase 4: Scale

- PostgreSQL migration
- Background jobs
- WhatsApp integration
- Model-backed media analysis

## What was added in this step

- First persistent SQLite layer in `backend/app/db.py`
- Automatic recording of verification checks
- Automatic recording of lesson certificates

This is the first step away from a throwaway demo and toward a real product backbone.
