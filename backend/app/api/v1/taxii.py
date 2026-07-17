"""TAXII 2.1 read-only pilot (CI-1) - discovery, collections, STIX objects."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...core.openapi_pillars import PILLAR_INTEL
from ...services.interop.stix_export import build_stix_bundle

router = APIRouter(tags=[PILLAR_INTEL])

TAXII_MEDIA = "application/taxii+json;version=2.1"
STIX_MEDIA = "application/stix+json;version=2.1"
COLLECTION_ID = "mboashield-intel"


def _taxii(payload: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        content=payload,
        status_code=status_code,
        media_type=TAXII_MEDIA,
        headers={"X-MboaShield-Taxii": "read-only-pilot"},
    )


@router.get("/taxii2/")
def taxii_discovery():
    return _taxii(
        {
            "title": "MboaShield TAXII 2.1",
            "description": "Read-only threat intel pilot (CI-1). Not a full TAXII server.",
            "default": "/taxii2/collections/",
            "api_roots": ["/taxii2/"],
            "versions": ["application/taxii+json;version=2.1"],
        }
    )


@router.get("/taxii2/collections/")
def taxii_collections():
    return _taxii(
        {
            "collections": [
                {
                    "id": COLLECTION_ID,
                    "title": "MboaShield Intel Indicators",
                    "description": "STIX indicators derived from compliant intel items",
                    "can_read": True,
                    "can_write": False,
                    "media_types": [STIX_MEDIA],
                }
            ]
        }
    )


@router.get(f"/taxii2/collections/{COLLECTION_ID}/")
def taxii_collection_detail():
    return _taxii(
        {
            "id": COLLECTION_ID,
            "title": "MboaShield Intel Indicators",
            "description": "STIX indicators derived from compliant intel items",
            "can_read": True,
            "can_write": False,
            "media_types": [STIX_MEDIA],
        }
    )


@router.get(f"/taxii2/collections/{COLLECTION_ID}/objects/")
def taxii_collection_objects(limit: int = Query(50, ge=1, le=200), q: str | None = None):
    bundle = build_stix_bundle(limit=limit, query=q)
    objects = bundle.get("objects") or []
    return _taxii(
        {
            "objects": objects,
            "more": False,
            "x_mboashield": {
                "bundle_id": bundle.get("id"),
                "count": len(objects),
                "note": "Read-only TAXII objects endpoint wrapping STIX pilot export",
            },
        }
    )
