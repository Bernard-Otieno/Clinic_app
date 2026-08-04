"""
Entry point for the FastAPI application — this is the file uvicorn runs to start the server.


"""
from fastapi import FastAPI, Depends
from sqlalchemy import text
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.routers import doctors
from app.database import get_db
from app.routers import appointments
#------------------------------------------------fornt end--------------------------------------------------------#
from fastapi.staticfiles import StaticFiles
from app.routers import patients
#------------------------------------------------fornt end--------------------------------------------------------#

app = FastAPI(title="Clinic Booking API")
app.include_router(doctors.router)
app.include_router(appointments.router)


#------------------------------------------------fornt end--------------------------------------------------------#

app.include_router(patients.router)
app.mount("/app", StaticFiles(directory="static", html=True), name="frontend")
#------------------------------------------------fornt end--------------------------------------------------------#

@app.get("/")
def root():
    return RedirectResponse(url="/app/")


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}