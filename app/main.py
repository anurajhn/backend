#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:47:57 2025

@author: rachna
"""
# backend/app/main.py
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine, Base
from .models import College, SeatAllotment
from .schemas import CollegeSchema, SeatAllotmentSchema
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy import func, case
import asyncio

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing; restrict in production # allow_origins=["http://localhost:5173"],
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
async def get_seat_allotments(
    db: AsyncSession = Depends(get_db),
    cetyear : Optional[int] = Query(None),
    cetround: Optional[str] = Query(None),
    collegecode: Optional[str] = Query(None),
    course: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query("asc"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = select(SeatAllotment)

    #offset = (page - 1) * limit  # Calculate offset

    # Mandatory wheres
    if cetround:
        query = query.where(SeatAllotment.cetround==cetround)    # Apply search wheres
     
    if category:
        query = query.where(SeatAllotment.category == category)
    if collegecode:
        query = query.where(SeatAllotment.collegecode == collegecode)
    if cetyear:
        query = query.where(SeatAllotment.cetyear==cetyear)    # Apply search wheres
    if course:
        query = query.where(SeatAllotment.course.ilike(f"%{course}%"))

    # Apply sorting
    if sort_by in ["college", "course", "category", "cutoffrank"]:
        if order == "desc":
            query = query.order_by(getattr(SeatAllotment, sort_by).desc())
        else:
            query = query.order_by(getattr(SeatAllotment, sort_by).asc())

    if sort_by:
        order_func = getattr(SeatAllotment, sort_by).desc() if order == "desc" else getattr(SeatAllotment, sort_by).asc()
        query = query.order_by(order_func)
        
# =============================================================================
#     # Sorting
#     order_func = asc if order == "asc" else desc
#     if hasattr(SeatAllotment, sort_by):
#         query = query.order_by(order_func(getattr(SeatAllotment, sort_by)))
# =============================================================================
        
    results = await db.execute(query.limit(limit).offset(offset))
    results = results.scalars().all()
    total = len(results)
    
    #db.close()
    if not results:
        raise HTTPException(status_code=404, detail="No seat allotments found")
    return {"total": total, "data": results}

@app.get("/filters")
async def get_filters(db: AsyncSession = Depends(get_db)):
    college_codes_query = await db.execute(select(SeatAllotment.collegecode).distinct())
    categories_query = await db.execute(select(SeatAllotment.category).distinct())
    
    return {
        "collegeCodes": [cc[0] for cc in college_codes_query.fetchall()],
        "categories": [cat[0] for cat in categories_query.fetchall()]
    }

@app.get("/collegeList")
async def get_college_list(
    db: AsyncSession = Depends(get_db),
    collegecode: Optional[str] = Query(None),
    college: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    
    search_term: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    #order: Optional[str] = Query("asc"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
        
):
    query = select(College)
    #query = select(SeatAllotment)

    if collegecode:
        query = query.where(College.collegecode==collegecode)    # Apply search filters
 
    if city:
        query = query.where(College.city == city)

    results = await db.execute(query.limit(limit).offset(offset))
    results = results.scalars().all()
    total = len(results)

    if not results:
        raise HTTPException(status_code=404, detail="No Colleges found")
    return {"total": total, "data": results}

@app.get("/Collegefilters")
async def get_filters(db: AsyncSession = Depends(get_db)):
    locationcodes_query = await db.execute(select(College.location).distinct())
    citycodes_query = await db.execute(select(College.city).distinct())

    return {
        "locations": [lc for lc in locationcodes_query.scalars().all()],
        "cities": [cc for cc in citycodes_query.scalars().all()]
    }


@app.get("/topColleges")
def get_top_colleges(
    cetyear: int = Query(..., description="Select Year"),
    category: str = Query(..., description="Select Category"),
    db: Session = Depends(get_db),
):
    # Subquery to get the lowest cutoff rank and corresponding CET round for each college-course-category
    subquery = (
        db.query(
            SeatAllotment.collegecode,
            SeatAllotment.course,
            SeatAllotment.category,
            func.min(
                case((SeatAllotment.cutoffrank.isnot(None), SeatAllotment.cutoffrank))
            ).label("min_cutoff"),
            func.min(SeatAllotment.cetround).label("min_round"),  # Get lowest CET round
        )
        .filter(
            SeatAllotment.cetyear == cetyear,
            SeatAllotment.category == category,
            SeatAllotment.cutoffrank.isnot(None),  # Ignore null cutoff ranks
        )
        .group_by(SeatAllotment.collegecode, SeatAllotment.course, SeatAllotment.category)
        .subquery()
    )

    # Get top 10 colleges based on the lowest cutoff rank
    top_colleges_subquery = (
        db.query(
            subquery.c.collegecode,
            func.min(subquery.c.min_cutoff).label("top_cutoff")
        )
        .group_by(subquery.c.collegecode)
        .order_by("top_cutoff")
        .limit(10)
        .subquery()
    )

    # Get top 5 courses for each of the top 10 colleges
    query = (
        db.query(
            SeatAllotment.cetyear,
            SeatAllotment.collegecode,
            College.college,
            SeatAllotment.course,
            SeatAllotment.category,
            SeatAllotment.cutoffrank,
            SeatAllotment.cetround,
        )
        .join(College, SeatAllotment.collegecode == College.collegecode)
        .join(
            subquery,
            (SeatAllotment.collegecode == subquery.c.collegecode) &
            (SeatAllotment.course == subquery.c.course) &
            (SeatAllotment.category == subquery.c.category) &
            (SeatAllotment.cetround == subquery.c.min_round)  # Ensure it's the lowest CET round
        )
        .join(
            top_colleges_subquery,
            SeatAllotment.collegecode == top_colleges_subquery.c.collegecode
        )
        .filter(
            SeatAllotment.cetyear == cetyear,
            SeatAllotment.category == category,
            SeatAllotment.cutoffrank.isnot(None),  # Ignore null cutoff ranks
        )
        .order_by(SeatAllotment.collegecode, SeatAllotment.cutoffrank.asc())
        .limit(50)  # 10 colleges × 5 courses each
    )

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found")

    # Convert results to JSON format
    formatted_results = [
        {
            "cetyear": row.cetyear,
            "collegecode": row.collegecode,
            "college": row.college,
            "course": row.course,
            "category": row.category,
            "cutoffrank": row.cutoffrank,
            "cetround": row.cetround,
        }
        for row in results
    ]

    return {"total": len(formatted_results), "data": formatted_results}