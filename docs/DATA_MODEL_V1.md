# MboaShield Data Model v1

## Purpose

This document defines the first real product data model for MboaShield.
The goal is to persist user activity, enable future dashboards, and prepare for PostgreSQL later.

## v1 entities

### `verification_checks`

Stores each analysis request across text, impersonation, audio, and image.

Fields:
- `id`
- `check_type`
- `input_text`
- `input_handle`
- `input_filename`
- `input_lang`
- `risk_score`
- `risk_band`
- `result_json`
- `created_at`

Why it matters:
- gives history
- enables analytics
- supports review workflows later
- creates audit trails for detections

### `lesson_certificates`

Stores each generated Mboa Ambassadors certificate.

Fields:
- `id`
- `certificate_id`
- `learner_name`
- `lesson_id`
- `lesson_title_en`
- `lesson_title_fr`
- `issued_on`
- `issuer`
- `founder`
- `created_at`

Why it matters:
- supports learner history
- allows future certificate lookup
- prepares for school/community dashboards

## Next entities after v1

### `users`
- identity
- role
- contact details
- account status

### `institutions`
- name
- short name
- category
- website
- verification status

### `official_handles`
- institution_id
- platform
- handle
- profile URL
- verification status

### `verification_signals`

Normalized detection signals linked to each check.

Fields:
- `id`
- `verification_check_id`
- `signal_type`
- `signal_label`
- `signal_score`
- `created_at`

Why it matters:
- supports analyst review
- enables future model feedback loops
- separates raw result blobs from structured evidence

### `incident_reports`
- user_id
- verification_check_id
- report_type
- description
- status

### `source_registry`
- title
- url
- institution_id
- topic tags
- trust level

## Migration path

1. Start with SQLite
2. Keep storage logic isolated
3. Move schema into migrations later
4. Promote to PostgreSQL without changing route contracts

## v1 implementation decision

For now, the app stores a full JSON result in `result_json`.
That keeps iteration fast while still preserving history.

Later, we should normalize repeated detection signals into:
- `verification_checks`
- `verification_signals`
- `incident_reports`

