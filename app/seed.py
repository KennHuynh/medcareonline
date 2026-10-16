from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Doctor

# Entirely fictional demo data.
DOCTORS = [
    ("Dr. Maya Okafor", "Primary Care", "Pasadena, CA",
     "Family medicine focused on preventive care and managing long-term conditions."),
    ("Dr. Daniel Reyes", "Primary Care", "Glendale, CA",
     "Internal medicine for adults, with a special interest in diabetes and blood pressure."),
    ("Dr. Priya Nair", "Cardiology", "Los Angeles, CA",
     "Heart health, cholesterol management, and post-surgery follow-up."),
    ("Dr. Samuel Whitfield", "Dermatology", "Pasadena, CA",
     "Skin checks, acne, eczema, and cosmetic dermatology."),
    ("Dr. Lena Park", "Pediatrics", "Burbank, CA",
     "Well-child visits, vaccinations, and care from newborn through adolescence."),
    ("Dr. Marcus Bell", "Orthopedics", "Los Angeles, CA",
     "Sports injuries, joint pain, and fracture care."),
    ("Dr. Aisha Rahman", "Neurology", "Glendale, CA",
     "Migraines, sleep disorders, and movement conditions."),
    ("Dr. Tomás Alvarez", "Psychiatry", "Pasadena, CA",
     "Anxiety, depression, ADHD, and medication management."),
    ("Dr. Hannah Cho", "Ophthalmology", "Burbank, CA",
     "Eye exams, glaucoma screening, and cataract care."),
    ("Dr. Victor Lindqvist", "Endocrinology", "Los Angeles, CA",
     "Thyroid disorders, diabetes, and hormone health."),
    ("Dr. Grace Mwangi", "Gynecology", "Pasadena, CA",
     "Routine exams, family planning, and women's health."),
    ("Dr. Owen Fitzgerald", "ENT", "Glendale, CA",
     "Ear, nose, and throat conditions, allergies, and hearing."),
]


def seed_doctors(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Doctor)):
        return
    db.add_all(
        Doctor(name=n, specialty=s, location=loc, bio=bio) for n, s, loc, bio in DOCTORS
    )
    db.commit()
