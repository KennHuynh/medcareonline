import os
from datetime import datetime
from zoneinfo import ZoneInfo

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
CLINIC_TZ = ZoneInfo(os.getenv("CLINIC_TZ", "America/Los_Angeles"))


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    # Some hosts hand out the legacy "postgres://" scheme, which SQLAlchemy rejects.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _database_url()


def clinic_now() -> datetime:
    """Current wall-clock time in the clinic's timezone, as a naive datetime."""
    return datetime.now(CLINIC_TZ).replace(tzinfo=None)
