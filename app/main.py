from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import COOKIE_SECURE, SECRET_KEY
from app.database import Base, SessionLocal, engine
from app.deps import LoginRequired
from app.routers import appointments, auth, doctors, messages
from app.seed import seed_doctors
from app.templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_doctors(db)
    yield


app = FastAPI(title="MedCare", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=COOKIE_SECURE,
    max_age=14 * 24 * 3600,
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(messages.router)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    if request.method == "GET":
        query = f"?{request.url.query}" if request.url.query else ""
        request.session["next"] = request.url.path + query
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    message = "We couldn't find that page." if exc.status_code == 404 else str(exc.detail)
    return render(request, "error.html", status_code=exc.status_code, message=message)


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
