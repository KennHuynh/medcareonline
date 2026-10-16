from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.deps import DB, CurrentUser
from app.models import Doctor, Message
from app.templating import flash, render

router = APIRouter(prefix="/messages")

MAX_BODY = 2000


@router.get("")
def inbox(request: Request, db: DB, user: CurrentUser):
    msgs = db.scalars(
        select(Message)
        .where(Message.user_id == user.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
    ).all()
    latest = {}
    for m in msgs:  # newest first, so the first one seen per doctor is the latest
        latest.setdefault(m.doctor_id, m)
    others = [
        d for d in db.scalars(select(Doctor).order_by(Doctor.name)).all() if d.id not in latest
    ]
    return render(request, "messages.html", user=user, conversations=list(latest.values()),
                  others=others)


@router.get("/{doctor_id}")
def thread(request: Request, db: DB, user: CurrentUser, doctor_id: int):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404)
    msgs = db.scalars(
        select(Message)
        .where(Message.user_id == user.id, Message.doctor_id == doctor_id)
        .order_by(Message.created_at, Message.id)
    ).all()
    return render(request, "thread.html", user=user, doctor=doctor, messages=msgs)


@router.post("/{doctor_id}")
def send(request: Request, db: DB, user: CurrentUser, doctor_id: int, body: str = Form("")):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404)

    body = body.strip()
    if not body or len(body) > MAX_BODY:
        flash(request, f"Write a message of up to {MAX_BODY} characters.", "error")
        return RedirectResponse(f"/messages/{doctor_id}", status_code=303)

    is_first = (
        db.scalar(
            select(Message.id).where(Message.user_id == user.id, Message.doctor_id == doctor_id)
        )
        is None
    )
    db.add(Message(user_id=user.id, doctor_id=doctor_id, sender="patient", body=body))
    if is_first:
        db.flush()
        db.add(
            Message(
                user_id=user.id,
                doctor_id=doctor_id,
                sender="system",
                body=(
                    f"Automated reply: your message was received. {doctor.name}'s office "
                    "typically responds within one business day. For emergencies, call 911."
                ),
            )
        )
    db.commit()
    return RedirectResponse(f"/messages/{doctor_id}", status_code=303)
