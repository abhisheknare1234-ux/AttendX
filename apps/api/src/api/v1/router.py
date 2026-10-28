from fastapi import APIRouter
from apps.api.src.api.v1.endpoints.health import router as health_router
from apps.api.src.api.v1.endpoints.auth import router as auth_router
from apps.api.src.api.v1.endpoints.users import router as users_router
from apps.api.src.api.v1.endpoints.academic import router as academic_router
from apps.api.src.api.v1.endpoints.sessions import router as sessions_router
from apps.api.src.api.v1.endpoints.checkin import router as checkin_router
from apps.api.src.api.v1.endpoints.review import router as review_router
from apps.api.src.api.v1.endpoints.corrections import router as corrections_router
from apps.api.src.api.v1.endpoints.reports import router as reports_router
from apps.api.src.api.v1.endpoints.audit import router as audit_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(academic_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(checkin_router)
api_v1_router.include_router(review_router)
api_v1_router.include_router(corrections_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(audit_router)
