from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select

from app.config import clinic_now
from app.deps import DB, CurrentUser
from app.models import Appointment, Doctor
from app.templating import flash, render

router = APIRouter(prefix="/appointments")

SLOT_FORMAT = "%Y-%m-%dT%H:%M"
MAX_NOTES = 2000


def parse_slot(raw: str) -> tuple[datetime | None, str | None]:
    """Validate a requested appointment time (clinic-local)."""
    try:
        dt = datetime.strptime(raw, SLOT_FORMAT)
    except ValueError:
        return None, "Choose a valid date and time."
    if dt <= clinic_now():
        return None, "Pick a time in the future."
    if dt.weekday() >= 5:
        return None, "Appointments are available Monday through Friday."
    if not 9 <= dt.hour < 17 or dt.minute not in (0, 30):
        return None, "Appointments run 9:00 AM to 5:00 PM, on the hour or half hour."
    return dt, None


def find_conflict(db, doctor_id: int, user_id: int, dt: datetime, exclude_id: int | None = None):
    stmt = select(Appointment).where(
        Appointment.status == "scheduled",
        Appointment.starts_at == dt,
        or_(Appointment.doctor_id == doctor_id, Appointment.user_id == user_id),
    )
    if exclude_id is not None:
        stmt = stmt.where(Appointment.id != exclude_id)
    clash = db.scalars(stmt).first()
    if clash is None:
        return None
    if clash.doctor_id == doctor_id:
        return "That time is already booked with this doctor. Please pick another."
    return "You already have another appointment at that time."


def get_owned(db, user, appointment_id: int) -> Appointment:
    appt = db.scalar(
        select(Appointment).where(Appointment.id == appointment_id, Appointment.user_id == user.id)
    )
    if appt is None:
        raise HTTPException(status_code=404)
    return appt


@router.get("")
def list_appointments(request: Request, db: DB, user: CurrentUser):
    now = clinic_now()
    appts = db.scalars(select(Appointment).where(Appointment.user_id == user.id)).all()
    upcoming = sorted(
        (a for a in appts if a.status == "scheduled" and a.starts_at >= now),
        key=lambda a: a.starts_at,
    )
    past = sorted(
        (a for a in appts if not (a.status == "scheduled" and a.starts_at >= now)),
        key=lambda a: a.starts_at,
        reverse=True,
    )
    return render(request, "appointments.html", user=user, upcoming=upcoming, past=past)


@router.get("/new")
def new_form(request: Request, db: DB, user: CurrentUser, doctor_id: int = 0):
    doctors = db.scalars(select(Doctor).order_by(Doctor.name)).all()
    return render(request, "new_appointment.html", user=user, doctors=doctors,
                  doctor_id=doctor_id, starts_at="", reason="", errors=[])


@router.post("")
def create(
    request: Request,
    db: DB,
    user: CurrentUser,
    doctor_id: int = Form(0),
    starts_at: str = Form(""),
    reason: str = Form(""),
):
    reason = reason.strip()
    errors = []
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        errors.append("Choose a doctor.")
    if not reason or len(reason) > 255:
        errors.append("Enter a reason for the visit (up to 255 characters).")
    dt, slot_error = parse_slot(starts_at)
    if slot_error:
        errors.append(slot_error)
    if not errors:
        conflict = find_conflict(db, doctor_id, user.id, dt)
        if conflict:
            errors.append(conflict)

    if errors:
        doctors = db.scalars(select(Doctor).order_by(Doctor.name)).all()
        return render(request, "new_appointment.html", status_code=400, user=user,
                      doctors=doctors, doctor_id=doctor_id, starts_at=starts_at,
                      reason=reason, errors=errors)

    db.add(Appointment(user_id=user.id, doctor_id=doctor_id, starts_at=dt, reason=reason))
    db.commit()
    flash(request, f"Appointment booked with {doctor.name}.")
    return RedirectResponse("/appointments", status_code=303)


@router.post("/{appointment_id}/reschedule")
def reschedule(
    request: Request, db: DB, user: CurrentUser, appointment_id: int, starts_at: str = Form("")
):
    appt = get_owned(db, user, appointment_id)
    if appt.status != "scheduled" or appt.starts_at < clinic_now():
        flash(request, "Only upcoming appointments can be rescheduled.", "error")
        return RedirectResponse("/appointments", status_code=303)

    dt, error = parse_slot(starts_at)
    error = error or find_conflict(db, appt.doctor_id, user.id, dt, exclude_id=appt.id)
    if error:
        flash(request, error, "error")
        return RedirectResponse("/appointments", status_code=303)

    appt.starts_at = dt
    db.commit()
    flash(request, "Appointment rescheduled.")
    return RedirectResponse("/appointments", status_code=303)


@router.post("/{appointment_id}/cancel")
def cancel(request: Request, db: DB, user: CurrentUser, appointment_id: int):
    appt = get_owned(db, user, appointment_id)
    if appt.status == "scheduled":
        appt.status = "cancelled"
        db.commit()
        flash(request, "Appointment cancelled.")
    return RedirectResponse("/appointments", status_code=303)


@router.post("/{appointment_id}/notes")
def save_notes(
    request: Request, db: DB, user: CurrentUser, appointment_id: int, notes: str = Form("")
):
    appt = get_owned(db, user, appointment_id)
    if len(notes) > MAX_NOTES:
        flash(request, f"Notes can be up to {MAX_NOTES} characters.", "error")
    else:
        appt.notes = notes.strip()
        db.commit()
        flash(request, "Notes saved.")
    return RedirectResponse("/appointments", status_code=303)
