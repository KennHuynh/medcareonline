import re

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB
from app.models import User
from app.security import MAX_PASSWORD_BYTES, MIN_PASSWORD_LEN, hash_password, verify_password
from app.templating import flash, render

router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _safe_next(path: str | None) -> str:
    if path and path.startswith("/") and not path.startswith("//"):
        return path
    return "/appointments"


@router.get("/")
def index(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/appointments", status_code=303)
    return render(request, "index.html")


@router.get("/register")
def register_form(request: Request):
    return render(request, "register.html", errors=[], name="", email="")


@router.post("/register")
def register(
    request: Request,
    db: DB,
    name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
):
    name, email = name.strip(), email.strip().lower()
    errors = []
    if not name or len(name) > 120:
        errors.append("Enter your name (up to 120 characters).")
    if not EMAIL_RE.match(email) or len(email) > 255:
        errors.append("Enter a valid email address.")
    if not (MIN_PASSWORD_LEN <= len(password) and len(password.encode()) <= MAX_PASSWORD_BYTES):
        errors.append(f"Password must be {MIN_PASSWORD_LEN}–{MAX_PASSWORD_BYTES} characters.")
    if not errors and db.scalar(select(User).where(User.email == email)):
        errors.append("An account with that email already exists.")
    if errors:
        return render(request, "register.html", status_code=400, errors=errors, name=name,
                      email=email)

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two sign-ups with the same email at once
        db.rollback()
        return render(request, "register.html", status_code=400, name=name, email=email,
                      errors=["An account with that email already exists."])

    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Welcome, {user.name}! Find a doctor or book your first appointment.")
    return RedirectResponse("/appointments", status_code=303)


@router.get("/login")
def login_form(request: Request):
    return render(request, "login.html", error=None, email="")


@router.post("/login")
def login(request: Request, db: DB, email: str = Form(""), password: str = Form("")):
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        return render(request, "login.html", status_code=400, email=email,
                      error="Invalid email or password.")

    next_url = _safe_next(request.session.get("next"))
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(next_url, status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
