#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:50:26 2025

@author: rachna
"""
# backend/app/main.py
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine, Base
from .models import College, SeatAllotment
from .schemas import CollegeSchema, SeatAllotmentSchema
from typing import List, Optional
from sqlalchemy import desc, asc

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/colleges", response_model=List[CollegeSchema])
def get_colleges(db: Session = Depends(get_db)):
    return db.query(College).all()

@app.get("/seat_allotments", response_model=List[SeatAllotmentSchema])
def get_seat_allotments(
    db: Session = Depends(get_db),
    cetyear: Optional[int] = Query(None),
    cetround: Optional[str] = Query(None),
    collegecode: Optional[str] = Query(None),
    course: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    # search_term: Optional[str] = Query(None),
    # sort_by: Optional[str] = Query("cutoffrank"),  # Default sorting by rank
    # order: Optional[str] = Query("asc"),  # Default ascending order
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = db.query(SeatAllotment)
    if cetyear:
        query = query.filter(SeatAllotment.cetyear == cetyear)
    if cetround:
        query = query.filter(SeatAllotment.cetround == cetround)
    if collegecode:
        query = query.filter(SeatAllotment.collegecode == collegecode)
    if course:
        query = query.filter(SeatAllotment.course == course)
    if category:
        query = query.filter(SeatAllotment.category == category)
    
# =============================================================================
#  # Search filter (checks in college name and course)
#     if search_term:
#         query = query.filter(
#             (SeatAllotment.college.ilike(f"%{search_term}%")) |
#             (SeatAllotment.course.ilike(f"%{search_term}%"))
#         )
# 
#     # Sorting
#     order_func = asc if order == "asc" else desc
#     if hasattr(SeatAllotment, sort_by):
#         query = query.order_by(order_func(getattr(SeatAllotment, sort_by)))
# 
#     # Get total count
#     total = query.count()
# =============================================================================

    # Apply pagination
    #results = query.limit(limit).offset(offset).all()
    return query.limit(limit).offset(offset).all()
    #return {"total": total, "data": results}
    #return { "data": results}


@app.get("/health")
def health_check():
    return {"status": "ok"}