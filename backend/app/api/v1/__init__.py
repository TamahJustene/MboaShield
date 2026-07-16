from __future__ import annotations

from fastapi import APIRouter

from .admin_users import router as admin_users_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .cases import router as cases_router
from .evidence import router as evidence_router
from .government import router as government_router
from .intel import router as intel_router
from .intelligence import router as intelligence_router
from .institution_portal import router as institution_portal_router
from .ntoc import router as ntoc_router
from .oauth import router as oauth_router
from .partners import router as partners_router
from .platform import router as platform_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(platform_router)
router.include_router(government_router)
router.include_router(intelligence_router)
router.include_router(analytics_router)
router.include_router(partners_router)
router.include_router(admin_users_router)
router.include_router(oauth_router)
router.include_router(cases_router)
router.include_router(ntoc_router)
router.include_router(intel_router)
router.include_router(evidence_router)
router.include_router(institution_portal_router)
