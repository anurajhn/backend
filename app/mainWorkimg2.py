from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine, Base
from .models import College, SeatAllotment
from .schemas import CollegeSchema, SeatAllotmentSchema
from typing import List, Optional
from sqlalchemy import desc, asc

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/seat_allotments")
def get_seat_allotments(
    db: Session = Depends(get_db),
    collegecode: Optional[str] = Query(None),
    course: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query("asc")
):
    query = db.query(SeatAllotment)


    # Apply search filters
    if collegecode:
        query = query.filter(SeatAllotment.collegecode.ilike(f"%{collegecode}%"))
    if course:
        query = query.filter(SeatAllotment.course.ilike(f"%{course}%"))
    if category:
        query = query.filter(SeatAllotment.category.ilike(f"%{category}%"))

    # Apply sorting
    if sort_by in ["college", "course", "category", "cutoffrank"]:
        if order == "desc":
            query = query.order_by(getattr(SeatAllotment, sort_by).desc())
        else:
            query = query.order_by(getattr(SeatAllotment, sort_by).asc())

    results = query.all()
    db.close()

    return results
