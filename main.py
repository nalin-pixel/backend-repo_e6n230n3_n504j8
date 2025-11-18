import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import create_document, get_documents
from schemas import Appointment

app = FastAPI(title="Dialsmith API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Dialsmith backend is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Appointment endpoints

class AppointmentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None
    timezone: Optional[str] = None

@app.post("/api/appointments")
def create_appointment(payload: AppointmentCreate):
    try:
        appointment = Appointment(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            preferred_date=payload.preferred_date,
            preferred_time=payload.preferred_time,
            notes=payload.notes,
            timezone=payload.timezone,
            status="new",
            source="website",
        )
        inserted_id = create_document("appointment", appointment)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
def list_appointments(limit: int = 50):
    try:
        docs = get_documents("appointment", limit=limit)
        # Convert ObjectId to string
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return {"ok": True, "items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
