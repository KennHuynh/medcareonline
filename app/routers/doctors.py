from fastapi import APIRouter, Request
from sqlalchemy import or_, select

from app.deps import DB
from app.models import Doctor
from app.templating import render

router = APIRouter()


@router.get("/doctors")
def doctors(request: Request, db: DB, q: str = "", specialty: str = ""):
    stmt = select(Doctor).order_by(Doctor.name)
    q = q.strip()[:100]
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                Doctor.name.ilike(like, escape="\\"),
                Doctor.specialty.ilike(like, escape="\\"),
                Doctor.location.ilike(like, escape="\\"),
                Doctor.bio.ilike(like, escape="\\"),
            )
        )
    if specialty:
        stmt = stmt.where(Doctor.specialty == specialty)

    specialties = db.scalars(select(Doctor.specialty).distinct().order_by(Doctor.specialty)).all()
    return render(
        request,
        "doctors.html",
        doctors=db.scalars(stmt).all(),
        specialties=specialties,
        q=q,
        specialty=specialty,
    )
