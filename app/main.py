"""
Entry point for the FastAPI application — this is the file uvicorn runs to start the server.

Right now it only proves the app boots and can reach the database. Real endpoints
(appointments, doctors, patients) will be added as their own router files in
app/routers/, then wired in here with app.include_router(...).
"""

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

app = FastAPI(title="Clinic Booking API")


@app.get("/")
def root():
    return {"status": "ok", "service": "clinic-booking-api"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}