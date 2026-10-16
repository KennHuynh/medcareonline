from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import CLINIC_TZ
from app.database import SessionLocal
from app.models import User

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def pretty_dt(dt: datetime) -> str:
    hour12 = dt.hour % 12 or 12
    suffix = "AM" if dt.hour < 12 else "PM"
    return f"{dt:%a, %b} {dt.day} · {hour12}:{dt:%M} {suffix}"


def msg_time(dt: datetime) -> str:
    local = dt.replace(tzinfo=timezone.utc).astimezone(CLINIC_TZ).replace(tzinfo=None)
    return pretty_dt(local)


templates.env.filters["pretty_dt"] = pretty_dt
templates.env.filters["msg_time"] = msg_time


def flash(request: Request, text: str, kind: str = "ok") -> None:
    request.session["flash"] = {"text": text, "kind": kind}


def _session_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with SessionLocal() as db:
        return db.get(User, user_id)


def render(request: Request, template: str, status_code: int = 200, **context):
    context.setdefault("user", _session_user(request))
    context["flash"] = request.session.pop("flash", None)
    return templates.TemplateResponse(request, template, context, status_code=status_code)
