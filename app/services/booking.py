from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Doctor, WorkingHours, Appointment

SLOT_MINUTES = 30


def validate_slot(db: Session, doctor_id, start_time: datetime, exclude_appointment_id=None) -> datetime:
    """
    Runs every check a slot must pass before it can be booked into — used by both
    fresh bookings and reschedules. Returns the computed end_time if valid;
    raises HTTPException (with the right status code) otherwise.
    """
    if start_time.tzinfo:
        start_time = start_time.replace(tzinfo=None)

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if start_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    day_of_week = start_time.weekday()
    hours = (
        db.query(WorkingHours)
        .filter(WorkingHours.doctor_id == doctor_id, WorkingHours.day_of_week == day_of_week)
        .first()
    )
    if not hours:
        raise HTTPException(status_code=400, detail="Doctor does not work on this day")

    if start_time.time() < hours.start_time or start_time.time() >= hours.end_time:
        raise HTTPException(status_code=400, detail="Requested time is outside doctor's working hours")

    minutes_since_open = (
        (start_time.hour * 60 + start_time.minute)
        - (hours.start_time.hour * 60 + hours.start_time.minute)
    )
    if minutes_since_open % SLOT_MINUTES != 0:
        raise HTTPException(status_code=400, detail=f"Appointments must start on {SLOT_MINUTES}-minute boundaries")

    end_time = start_time + timedelta(minutes=SLOT_MINUTES)

    conflict_query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "booked",
        Appointment.start_time == start_time,
    )
    if exclude_appointment_id:
        conflict_query = conflict_query.filter(Appointment.id != exclude_appointment_id)

    if conflict_query.first():
        raise HTTPException(status_code=409, detail="This slot is already booked")

    return end_time