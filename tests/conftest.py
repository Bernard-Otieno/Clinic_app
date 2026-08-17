import pytest
from datetime import time

from app.database import engine, SessionLocal
from app.models import Doctor, WorkingHours, Patient
#setup for test_booking

@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session #17

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def test_doctor(db_session):
    doctor = Doctor(name="Dr. Test Subject", specialty="Testing")
    db_session.add(doctor)
    db_session.flush()

    db_session.add(WorkingHours(
        doctor_id=doctor.id,
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        end_time=time(17, 0),
    ))
    db_session.flush()

    return doctor


@pytest.fixture()
def test_patient(db_session):
    patient = Patient(name="Test Patient", email="test.patient@example.com")
    db_session.add(patient)
    db_session.flush()
    return patient