import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.src.core.config import settings
from apps.api.src.core.database import Base, engine, SessionLocal
from apps.api.src.core.security import get_password_hash
from apps.api.src.models.user import User, UserRole
from apps.api.src.api.v1.router import api_v1_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("attendx.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate production settings
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' mode...")
    settings.validate_production_readiness()

    # Ensure tables are created if running local SQLite dev
    Base.metadata.create_all(bind=engine)

    # Initial admin account bootstrap check
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin and settings.INITIAL_ADMIN_EMAIL:
            logger.info(f"No administrator found. Bootstrapping initial admin: {settings.INITIAL_ADMIN_EMAIL}")
            bootstrap_admin = User(
                email=settings.INITIAL_ADMIN_EMAIL.lower().strip(),
                password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                first_name="Primary",
                last_name="Administrator",
                is_active=True
            )
            db.add(bootstrap_admin)
            db.commit()
            logger.info("Primary administrator bootstrapped successfully.")
    except Exception as e:
        logger.error(f"Error during administrator bootstrap check: {str(e)}")
    finally:
        db.close()

    yield
    logger.info("Shutting down AttendX AI API...")


app = FastAPI(
    title="AttendX AI API",
    description="Smart Attendance & Anti-Proxy Verification System for ZEAL College of Engineering & Research, Pune",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Middleware
origins = settings.ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1
app.include_router(api_v1_router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "institution": settings.INSTITUTION_NAME,
        "documentation": "/docs",
        "health": "/api/v1/health"
    }
