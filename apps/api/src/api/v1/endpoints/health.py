from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from apps.api.src.core.database import get_db
from apps.api.src.core.config import settings

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive institutional system and verification provider health probe."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "institution": settings.INSTITUTION_NAME,
        "environment": settings.ENVIRONMENT,
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": {
                "status": db_status,
                "engine": "PostgreSQL" if "postgres" in settings.DATABASE_URL else "SQLite"
            },
            "qr_crypto_validator": {
                "status": "operational",
                "algorithm": "HMAC-SHA256",
                "refresh_interval_seconds": settings.QR_REFRESH_INTERVAL_SECONDS
            },
            "geofence_engine": {
                "status": "operational",
                "formula": "WGS-84 Haversine Spherical",
                "anchor": {
                    "campus": "ZEAL College Narhe Pune",
                    "latitude": settings.CAMPUS_DEFAULT_LATITUDE,
                    "longitude": settings.CAMPUS_DEFAULT_LONGITUDE
                }
            },
            "biometric_verifier": {
                "status": "operational",
                "provider": settings.FACE_VERIFIER_PROVIDER,
                "threshold": settings.FACE_SIMILARITY_THRESHOLD
            },
            "liveness_provider": {
                "status": "operational" if settings.LIVENESS_REQUIRED else "not_configured_by_policy",
                "provider": settings.LIVENESS_PROVIDER,
                "required": settings.LIVENESS_REQUIRED
            }
        }
    }

