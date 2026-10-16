import os
from datetime import datetime
from zoneinfo import ZoneInfo
 
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
CLINIC_TZ = ZoneInfo(os.getenv("CLINIC_TZ", "America/Los_Angeles"))
 
 
def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    # Hosts like Neon give "postgres://" or "postgresql://". Pin the driver we install
    # (psycopg2): SQLAlchemy 2.1 would otherwise default to psycopg 3, which isn't installed.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url
 
 
DATABASE_URL = _database_url()
 
 
def clinic_now() -> datetime:
    """Current wall-clock time in the clinic's timezone, as a naive datetime."""
    return datetime.now(CLINIC_TZ).replace(tzinfo=None)
