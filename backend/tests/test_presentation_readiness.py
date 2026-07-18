"""Presentation and deployment artifact regression checks."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]


def test_presentation_assets_are_present_and_nonempty():
    expected = [
        ROOT / "frontend/static/samples/minister_voice_clone.wav",
        ROOT / "frontend/static/samples/synthetic_smooth_face.jpg",
        ROOT / "frontend/static/samples/tiny_sticker.jpg",
        ROOT / "frontend/static/presentations/MboaShield_SIN2026.pptx",
        ROOT / "frontend/static/icon.svg",
    ]
    for path in expected:
        assert path.is_file(), path
        assert path.stat().st_size > 100, path


def test_grand_jury_demo_fails_visibly_and_recovers():
    script = (ROOT / "frontend/static/app.js").read_text(encoding="utf-8")
    assert "if (!response.ok)" in script
    assert "No assessment was produced" in script
    assert "Assessment response is incomplete" in script
    assert "Demo sample is unavailable" in script
    assert "finally {" in script
    assert "setDemoRunning(false)" in script


def test_alembic_revision_chain_has_one_resolvable_head():
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/alembic"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["0017_t4_interop"]
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 15


def test_national_templates_are_fail_closed():
    compose = (ROOT / "docker-compose.gov.yml").read_text(encoding="utf-8")
    assert 'AUTH_ENFORCE: "true"' in compose
    assert 'MFA_ENFORCE: "true"' in compose
    assert "change-me-gov-mboashield" not in compose
    assert 'CORS_ORIGINS: "*"' not in compose

    rls = (ROOT / "deploy/sql/rls_tenant.sql").read_text(encoding="utf-8")
    assert "OR true" not in rls
    assert "RLS activation refused" in rls
    assert "WITH CHECK (tenant_id =" in rls
