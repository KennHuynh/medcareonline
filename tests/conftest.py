import os
import tempfile
import uuid
from datetime import datetime, time, timedelta

# Must be set before the app is imported so it picks up the throwaway database.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SECRET_KEY"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import clinic_now  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Appointment, User  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        yield c


def new_client():
    return TestClient(app)


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def register(c, email=None, name="Test Patient", password=PASSWORD):
    email = email or unique_email()
    r = c.post("/register", data={"name": name, "email": email, "password": password})
    return email, r


def slot(offset_days=7, hour=10, minute=0) -> str:
    """A valid future weekday slot string, as submitted by a datetime-local input."""
    day = clinic_now().date() + timedelta(days=offset_days)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return datetime.combine(day, time(hour, minute)).strftime("%Y-%m-%dT%H:%M")


def appointments_for(email):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        return db.scalars(select(Appointment).where(Appointment.user_id == user.id)).all()
