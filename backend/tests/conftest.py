from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AUTH_ENFORCE", "false")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "10000")
    monkeypatch.setenv("JWT_SECRET", "test-secret-mboashield")
    monkeypatch.setenv("VAULT_LOCAL_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("VAULT_SIGNING_KEY", "test-vault-signing-key")

    from backend.app.core.config import get_settings
    from backend.app.db.session import reset_engine
    from backend.app.main import create_app

    reset_engine()
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client, db_path
