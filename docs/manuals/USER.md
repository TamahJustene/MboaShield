# User manual

**Version:** 1.9.0 � **UI:** http://127.0.0.1:8000 (or live Render URL)

## What MboaShield is

A national digital trust platform for Cameroon: check rumours, impersonation, and media risk signals; learn digital patriotism; escalate incidents for human review. AI scores are **decision support only** (`certainty: none`).

## Common actions

| Goal | Where |
|---|---|
| Check a text claim | Home ? text check |
| Check impersonation | Home ? impersonation |
| Upload image/audio | Home ? media / audio |
| Complete a lesson | Ambassadors module |
| Verify a government announcement | `/verify/a/{id}` or Verify announcement UI |
| See national analytics | `/static/national.html` |

## Trust score honesty

- Scores and bands help prioritize attention.
- They are **not** legal proof and never claim absolute certainty.
- High risk should be escalated; humans decide public advisories.

## Optional privacy features

Some features need explicit consent (Phase 14):

- `analytics_share`
- `feedback_learning`
- `partner_notify`

Grant/revoke via Governance console (`/static/governance.html`) or `POST /api/v1/governance/consent`.

## Accessibility notes

- Prefer keyboard-reachable primary buttons on demo pages.
- High-contrast text on dark panels; avoid relying on colour alone for risk bands.
- Screen-reader: risk explanations are plain text in the report panel.

## Getting help

- Pitch / jury walkthrough: download PPT at `/static/presentations.html`; script in [`../PRESENTER_GUIDE.md`](../PRESENTER_GUIDE.md)
- Product brief: [`../PRODUCT_STATUS.md`](../PRODUCT_STATUS.md)
