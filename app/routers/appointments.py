from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Appointment, Patient
from app.schemas import AppointmentCreate, AppointmentOut
from app.services.booking import validate_slot
from app.schemas import AppointmentCreate, AppointmentOut, AppointmentCancel, AppointmentReschedule

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentOut, status_code=201)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    end_time = validate_slot(db, payload.doctor_id, payload.start_time)

    appointment = Appointment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        start_time=payload.start_time,
        end_time=end_time,
        status="booked",
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This slot was just booked by someone else")

    db.refresh(appointment)
    return appointment

#7
@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: str, payload: AppointmentCancel, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == "cancelled":
        raise HTTPException(status_code=400, detail="Appointment is already cancelled")

    appointment.status = "cancelled"
    appointment.cancellation_reason = payload.reason
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(appointment_id: str, payload: AppointmentReschedule, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot reschedule a cancelled appointment")

    end_time = validate_slot(
        db, appointment.doctor_id, payload.new_start_time,
        exclude_appointment_id=appointment.id,
    )

    appointment.start_time = payload.new_start_time
    appointment.end_time = end_time

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This slot was just booked by someone else")

    db.refresh(appointment)
    return appointment