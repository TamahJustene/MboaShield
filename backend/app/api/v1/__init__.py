from __future__ import annotations

from fastapi import APIRouter

from .analytics import router as analytics_router
from .auth import router as auth_router
from .government import router as government_router
from .intelligence import router as intelligence_router
from .partners import router as partners_router
from .platform import router as platform_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(platform_router)
router.include_router(government_router)
router.include_router(intelligence_router)
router.include_router(analytics_router)
router.include_router(partners_router)
