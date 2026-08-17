import os
from datetime import datetime, date as date_type, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, WorkingHours, Appointment

router = APIRouter(prefix="/doctors", tags=["doctors"])

SLOT_MINUTES = 30

#6
@router.get("/{doctor_id}/availability") #15
def get_availability(
    doctor_id: str,
    date: date_type = Query(..., description="Date to check, e.g. 2026-08-10"),
    db: Session = Depends(get_db),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    day_of_week = date.weekday()  # Monday=0 ... Sunday=6 — matches how we stored working_hours

    hours = (
        db.query(WorkingHours)
        .filter(WorkingHours.doctor_id == doctor_id, WorkingHours.day_of_week == day_of_week)
        .first()
    )
    if not hours:
        return {"doctor_id": doctor_id, "date": str(date), "available_slots": []}

    all_slots = []
    current = datetime.combine(date, hours.start_time)
    end = datetime.combine(date, hours.end_time)
    while current + timedelta(minutes=SLOT_MINUTES) <= end:
        all_slots.append(current)
        current += timedelta(minutes=SLOT_MINUTES)

    day_start = datetime.combine(date, time.min)
    day_end = datetime.combine(date, time.max)
    booked = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "booked",
            Appointment.start_time >= day_start,
            Appointment.start_time <= day_end,
        )
        .all()
    )
    booked_times = {appt.start_time.time() for appt in booked} 

    available = [slot for slot in all_slots if slot.time() not in booked_times] #9- booked times - all slots

    return {
        "doctor_id": doctor_id,
        "date": str(date),
        "available_slots": [slot.strftime("%H:%M") for slot in available],
    }



#------------------------------------------------fornt end--------------------------------------------------------#
from app.schemas import DoctorOut

@router.get("", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()