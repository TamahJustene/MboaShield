"""OAuth2 client-credentials token endpoint + client registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ...identity_store import authenticate_oauth_client, create_oauth_client, write_auth_event
from ...repositories import write_audit_log
from ...schemas import OAuthClientCreateIn
from ...services.identity_federation import issue_client_credentials_token
from ..deps import require_permission

router = APIRouter(tags=["oauth"])


async def _read_payload(request: Request) -> dict:
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            data = await request.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    form = await request.form()
    return {key: form.get(key) for key in form.keys()}


@router.post("/oauth/token")
async def oauth_token(request: Request):
    payload = await _read_payload(request)
    grant_type = str(payload.get("grant_type") or "")
    client_id = str(payload.get("client_id") or "")
    client_secret = str(payload.get("client_secret") or "")
    scope = str(payload.get("scope") or "")
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    actor = authenticate_oauth_client(client_id, client_secret)
    if not actor:
        raise HTTPException(status_code=401, detail="invalid_client")
    if scope:
        requested = {item.strip() for item in scope.split() if item.strip()}
        allowed = set(actor.get("scopes") or [])
        if requested - allowed:
            raise HTTPException(status_code=400, detail="invalid_scope")
        actor = dict(actor)
        actor["scopes"] = sorted(requested)
    token = issue_client_credentials_token(actor)
    write_auth_event(
        event_type="oauth.client_credentials",
        details={"client_id": client_id, "scopes": actor.get("scopes")},
    )
    return token


@router.post("/oauth/clients")
def register_oauth_client(
    body: OAuthClientCreateIn,
    request: Request,
    actor: dict | None = Depends(require_permission("partners:manage")),
):
    created = create_oauth_client(
        name=body.name,
        partner_org=body.partner_org,
        scopes=body.scopes,
        created_by_user_id=actor["id"] if actor else None,
    )
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    write_audit_log(
        action="oauth.client_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="oauth_client",
        resource_id=created["client_id"],
        ip_address=ip,
        user_agent=ua,
    )
    return created
