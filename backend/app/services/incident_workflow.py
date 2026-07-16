"""National incident workflow - states, transitions, and audit events.

Backward compatible with legacy statuses: open, reviewing, resolved, dismissed.
"""

from __future__ import annotations

from typing import Any

# Canonical national workflow statuses
WORKFLOW_STATES: list[dict[str, str]] = [
    {"id": "open", "label": "Citizen Report", "role": "citizen"},
    {"id": "ai_analysis", "label": "AI Analysis", "role": "system"},
    {"id": "analyst_review", "label": "Analyst Review", "role": "analyst"},
    {"id": "institution_review", "label": "Institution Review", "role": "institution_admin"},
    {"id": "decision", "label": "Decision", "role": "analyst"},
    {"id": "public_advisory", "label": "Public Advisory", "role": "analyst"},
    {"id": "resolved", "label": "Resolved", "role": "analyst"},
    {"id": "archived", "label": "Archived", "role": "admin"},
    {"id": "dismissed", "label": "Dismissed", "role": "analyst"},
    {"id": "reviewing", "label": "Analyst Review (legacy)", "role": "analyst"},
]

ALLOWED_STATUSES = {item["id"] for item in WORKFLOW_STATES}

# Normalize legacy aliases to canonical ids for transition rules
STATUS_ALIASES = {
    "reviewing": "analyst_review",
}

# Allowed forward (and terminal) transitions using canonical status ids
TRANSITIONS: dict[str, set[str]] = {
    "open": {"ai_analysis", "analyst_review", "dismissed"},
    "ai_analysis": {"analyst_review", "dismissed"},
    "analyst_review": {"institution_review", "decision", "dismissed"},
    "institution_review": {"decision", "dismissed"},
    "decision": {"public_advisory", "resolved", "dismissed"},
    "public_advisory": {"resolved"},
    "resolved": {"archived"},
    "archived": set(),
    "dismissed": {"archived"},
}


def canonicalize(status: str) -> str:
    status = (status or "").strip().lower()
    return STATUS_ALIASES.get(status, status)


def validate_status(status: str) -> str:
    raw = (status or "").strip().lower()
    if raw not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")
    return raw


def assert_transition(from_status: str, to_status: str) -> tuple[str, str]:
    """Validate transition. Returns (canonical_from, status_to_persist)."""
    from_raw = validate_status(from_status)
    to_raw = validate_status(to_status)
    source = canonicalize(from_raw)
    target = canonicalize(to_raw)
    allowed = TRANSITIONS.get(source, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid workflow transition: {from_status} -> {to_status}. "
            f"Allowed from {source}: {', '.join(sorted(allowed)) or '(none)'}"
        )
    return source, to_raw


def next_actions(status: str) -> list[str]:
    canonical = canonicalize(status)
    return sorted(TRANSITIONS.get(canonical, set()))


def workflow_blueprint() -> dict[str, Any]:
    return {
        "states": WORKFLOW_STATES,
        "transitions": {key: sorted(values) for key, values in TRANSITIONS.items()},
        "legacy_aliases": STATUS_ALIASES,
        "pipeline": [
            "open",
            "ai_analysis",
            "analyst_review",
            "institution_review",
            "decision",
            "public_advisory",
            "resolved",
            "archived",
        ],
    }
