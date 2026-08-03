from datetime import time

from app.database import SessionLocal
from app.models import Doctor, WorkingHours, Patient

db = SessionLocal()

existing = db.query(Doctor).count()
if existing > 0:
    print(f"Database already has {existing} doctor(s) — skipping seed. Clear the tables manually first if you want to reseed.")
    db.close()
    exit()

doctors_data = [
    {"name": "Dr. Amina Yusuf", "specialty": "General Practice"},
    {"name": "Dr. Brian Otieno", "specialty": "Pediatrics"},
    {"name": "Dr. Grace Wanjiru", "specialty": "Dermatology"},
    {"name": "Dr. Samuel Kiprop", "specialty": "Cardiology"},
    {"name": "Dr. Fatima Hassan", "specialty": "General Practice"},
]

for doc_data in doctors_data:
    doctor = Doctor(**doc_data)
    db.add(doctor)
    db.flush()  # sends the INSERT now so doctor.id is available, without fully committing yet

    for day in range(0, 5):  # Monday(0) through Friday(4) — matches our scenario's "set working hours"
        db.add(WorkingHours(
            doctor_id=doctor.id,
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(17, 0),
        ))

patients_data = [
    {"name": "John Mwangi", "email": "john.mwangi@example.com"},
    {"name": "Wanjiku Kamau", "email": "wanjiku.kamau@example.com"},
]
for pat_data in patients_data:
    db.add(Patient(**pat_data))

db.commit()
print("Seeded 5 doctors (Mon–Fri, 9am–5pm each) and 2 patients.")

db.close()