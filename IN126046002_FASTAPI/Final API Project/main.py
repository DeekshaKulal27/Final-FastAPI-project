import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

app = FastAPI()

# ------------------ DATA ------------------
doctors = [
    {"id": 1, "name": "Dr. Smith", "specialization": "Cardiology", "is_available": True},
    {"id": 2, "name": "Dr. John", "specialization": "Dermatology", "is_available": True},
    {"id": 3, "name": "Dr. Alice", "specialization": "Neurology", "is_available": False},
]

appointments = []
appointment_counter = 1

# ------------------ HELPERS ------------------
def find_doctor(doctor_id):
    for doc in doctors:
        if doc["id"] == doctor_id:
            return doc
    return None

def find_appointment(appointment_id):
    for appt in appointments:
        if appt["appointment_id"] == appointment_id:
            return appt
    return None

def calculate_fee():
    return 500


# ------------------ DAY 1 (GET APIs) ------------------

@app.get("/")
def home():
    return {"message": "Welcome to Medical Appointment System"}


@app.get("/doctors")
def get_doctors():
    return {"total": len(doctors), "data": doctors}


@app.get("/doctors/summary")
def summary():
    available = [d for d in doctors if d["is_available"]]
    return {
        "total": len(doctors),
        "available": len(available),
        "unavailable": len(doctors) - len(available)
    }


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)
    if not doc:
        return {"error": "Doctor not found"}
    return doc


@app.get("/appointments")
def get_appointments():
    return {"total": len(appointments), "data": appointments}


# ------------------ DAY 2 (Pydantic) ------------------

class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    symptoms: str = Field(..., min_length=5)


# ------------------ DAY 3 (POST + Helpers) ------------------

@app.post("/appointments")
def book_appointment(req: AppointmentRequest):
    global appointment_counter

    doctor = find_doctor(req.doctor_id)

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor["is_available"]:
        raise HTTPException(status_code=400, detail="Doctor not available")

    appointment = {
        "appointment_id": appointment_counter,
        "patient_name": req.patient_name,
        "doctor_id": req.doctor_id,
        "symptoms": req.symptoms,
        "fee": calculate_fee(),
        "status": "booked"
    }

    appointments.append(appointment)
    appointment_counter += 1

    return appointment


# ------------------ DAY 4 (CRUD) ------------------

@app.post("/doctors")
def add_doctor(doc: dict, response: Response):
    doc["id"] = len(doctors) + 1
    doctors.append(doc)
    response.status_code = 201
    return doc


@app.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    is_available: Optional[bool] = None
):
    doc = find_doctor(doctor_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if is_available is not None:
        doc["is_available"] = is_available

    return doc


@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctors.remove(doc)
    return {"message": "Doctor deleted successfully"}


# ------------------ DAY 5 (WORKFLOW) ------------------

@app.post("/appointments/checkin/{appointment_id}")
def checkin(appointment_id: int):
    appt = find_appointment(appointment_id)

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "checked_in"
    return appt


@app.post("/appointments/complete/{appointment_id}")
def complete(appointment_id: int):
    appt = find_appointment(appointment_id)

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "completed"
    return appt


@app.post("/appointments/cancel/{appointment_id}")
def cancel(appointment_id: int):
    appt = find_appointment(appointment_id)

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "cancelled"
    return appt


# ------------------ DAY 6 (ADVANCED APIs) ------------------

@app.get("/appointments/search")
def search(patient_name: str):
    result = [
        a for a in appointments
        if patient_name.lower() in a["patient_name"].lower()
    ]

    if not result:
        return {"message": "No matching records"}

    return {"total_found": len(result), "data": result}


@app.get("/appointments/sort")
def sort(order: str = "asc"):
    return sorted(
        appointments,
        key=lambda x: x["fee"],
        reverse=(order == "desc")
    )


@app.get("/appointments/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": len(appointments),
        "data": appointments[start:end]
    }


@app.get("/appointments/browse")
def browse(
    keyword: Optional[str] = None,
    page: int = 1,
    limit: int = 2
):
    data = appointments

    if keyword:
        data = [
            a for a in data
            if keyword.lower() in a["patient_name"].lower()
        ]

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(data),
        "page": page,
        "data": data[start:end]
    }
