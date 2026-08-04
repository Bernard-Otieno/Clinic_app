from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    doctor_id: UUID
    patient_id: UUID
    start_time: datetime


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    cancellation_reason: Optional[str] = None



class AppointmentCancel(BaseModel):
    reason: str


class AppointmentReschedule(BaseModel):
    new_start_time: datetime


###----------------- FRONT END---------------------##
class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    specialty: Optional[str] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str