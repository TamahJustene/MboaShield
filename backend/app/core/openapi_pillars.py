"""National platform taxonomy for OpenAPI (MboaShield 2030 T0)."""

from __future__ import annotations

PILLAR_TRUST = "pillar-trust"
PILLAR_IDENTITY = "pillar-identity"
PILLAR_INTEL = "pillar-intel"
PILLAR_INVESTIGATION = "pillar-investigation"
PILLAR_EVIDENCE = "pillar-evidence"
PILLAR_COMMS = "pillar-comms"
PILLAR_ANALYTICS = "pillar-analytics"
PILLAR_AI = "pillar-ai"
PILLAR_GOVERNANCE = "pillar-governance"
PILLAR_PARTNER = "pillar-partner"
PILLAR_INFRA = "pillar-infrastructure"

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": PILLAR_TRUST,
        "description": "National Trust Platform - checks, multimodal analysis, trust fusion",
    },
    {
        "name": PILLAR_IDENTITY,
        "description": "National Identity Platform - auth, MFA, federation, admin users",
    },
    {
        "name": PILLAR_INTEL,
        "description": "National Threat Intelligence Platform - sources, ingest, NTOC",
    },
    {
        "name": PILLAR_INVESTIGATION,
        "description": "National Investigation Platform - cases, incidents, workflow",
    },
    {
        "name": PILLAR_EVIDENCE,
        "description": "National Evidence Platform - vault, custody, retention",
    },
    {
        "name": PILLAR_COMMS,
        "description": "National Government Communications Platform - signed announcements, verify",
    },
    {
        "name": PILLAR_ANALYTICS,
        "description": "National Analytics Platform - national aggregates and feedback",
    },
    {
        "name": PILLAR_AI,
        "description": "National AI Platform - registry, evaluation, calibration",
    },
    {
        "name": PILLAR_GOVERNANCE,
        "description": "National Governance Platform - consent, risks, model cards",
    },
    {
        "name": PILLAR_PARTNER,
        "description": "National Partner Platform - API keys, OAuth2 clients",
    },
    {
        "name": PILLAR_INFRA,
        "description": "Infrastructure - metrics, workers, deployment status",
    },
]

PILLAR_CATALOG: list[dict[str, str]] = [
    {"id": PILLAR_TRUST, "name": "National Trust Platform"},
    {"id": PILLAR_IDENTITY, "name": "National Identity Platform"},
    {"id": PILLAR_INTEL, "name": "National Threat Intelligence Platform"},
    {"id": PILLAR_INVESTIGATION, "name": "National Investigation Platform"},
    {"id": PILLAR_EVIDENCE, "name": "National Evidence Platform"},
    {"id": PILLAR_COMMS, "name": "National Government Communications Platform"},
    {"id": PILLAR_ANALYTICS, "name": "National Analytics Platform"},
    {"id": PILLAR_AI, "name": "National AI Platform"},
    {"id": PILLAR_GOVERNANCE, "name": "National Governance Platform"},
    {"id": PILLAR_PARTNER, "name": "National Partner Platform"},
    {"id": PILLAR_INFRA, "name": "Infrastructure"},
]

PROGRAM_ID = "mboashield-2030"
TRANSFORMATION_PHASE = "T7"
