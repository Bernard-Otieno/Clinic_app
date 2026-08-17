from datetime import datetime, timedelta
import uuid

import pytest
from fastapi import HTTPException

from app.services.booking import validate_slot
from app.models import Appointment

#variables form conftest.py


def next_monday_at(hour, minute=0):
    """Always returns a Monday in the future, so tests never start failing just because time passed."""
    today = datetime.now()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target = today + timedelta(days=days_ahead)
    return target.replace(hour=hour, minute=minute, second=0, microsecond=0)


def test_valid_slot_passes(db_session, test_doctor):
    start = next_monday_at(10, 0)
    end_time = validate_slot(db_session, test_doctor.id, start)
    assert end_time == start + timedelta(minutes=30)


def test_rejects_past_date(db_session, test_doctor):
    past = datetime.now() - timedelta(days=1)
    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, past)
    assert exc_info.value.status_code == 400


def test_rejects_outside_working_hours(db_session, test_doctor):
    too_early = next_monday_at(7, 0)  # doctor starts at 9:00
    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, too_early)
    assert exc_info.value.status_code == 400


def test_rejects_unaligned_slot(db_session, test_doctor):
    off_grid = next_monday_at(10, 15)  # not on a 30-minute boundary
    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, off_grid)
    assert exc_info.value.status_code == 400


def test_rejects_day_doctor_does_not_work(db_session, test_doctor):
    # test_doctor's fixture only creates working hours for Monday
    today = datetime.now()
    days_ahead = (5 - today.weekday()) % 7  # next Saturday
    if days_ahead == 0:
        days_ahead = 7
    saturday = (today + timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)

    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, saturday)
    assert exc_info.value.status_code == 400


def test_rejects_double_booking(db_session, test_doctor, test_patient):
    start = next_monday_at(11, 0)
    existing = Appointment(
        doctor_id=test_doctor.id, patient_id=test_patient.id,
        start_time=start, end_time=start + timedelta(minutes=30), status="booked",
    )
    db_session.add(existing)
    db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, start)
    assert exc_info.value.status_code == 409


def test_allows_rebooking_cancelled_slot(db_session, test_doctor, test_patient):
    start = next_monday_at(13, 0)
    cancelled = Appointment(
        doctor_id=test_doctor.id, patient_id=test_patient.id,
        start_time=start, end_time=start + timedelta(minutes=30),
        status="cancelled", cancellation_reason="testing",
    )
    db_session.add(cancelled)
    db_session.flush()

    # Should NOT raise — a cancelled appointment must not block the slot
    end_time = validate_slot(db_session, test_doctor.id, start)
    assert end_time == start + timedelta(minutes=30)


def test_rejects_unknown_doctor(db_session):
    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, uuid.uuid4(), next_monday_at(10, 0))
    assert exc_info.value.status_code == 404

def test_rejects_booking_less_than_one_hour_out(db_session, test_doctor):
    too_soon = datetime.now() + timedelta(minutes=30)
    with pytest.raises(HTTPException) as exc_info:
        validate_slot(db_session, test_doctor.id, too_soon)
    assert exc_info.value.status_code == 400