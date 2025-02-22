from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine, Base
from .models import College, SeatAllotment
from .schemas import CollegeSchema, SeatAllotmentSchema
from typing import List, Optional
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case

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
def get_seat_allotments(
    db: Session = Depends(get_db),
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
    query = db.query(SeatAllotment)

    #offset = (page - 1) * limit  # Calculate offset

    # Mandatory filters
    if cetround:
        query = query.filter(SeatAllotment.cetround==cetround)    # Apply search filters
     
    if category:
        query = query.filter(SeatAllotment.category == category)
    if collegecode:
        query = query.filter(SeatAllotment.collegecode == collegecode)
    if cetyear:
        query = query.filter(SeatAllotment.cetyear==cetyear)    # Apply search filters
    if course:
        query = query.filter(SeatAllotment.course.ilike(f"%{course}%"))

    # Apply sorting
    if sort_by in ["college", "course", "category", "cutoffrank"]:
        if order == "desc":
            query = query.order_by(getattr(SeatAllotment, sort_by).desc())
        else:
            query = query.order_by(getattr(SeatAllotment, sort_by).asc())

# =============================================================================
#     # Sorting
#     order_func = asc if order == "asc" else desc
#     if hasattr(SeatAllotment, sort_by):
#         query = query.order_by(order_func(getattr(SeatAllotment, sort_by)))
# =============================================================================
        
    results = query.all()
        # Get total count
    total = query.count()
    
    # Apply pagination
    results = query.limit(limit).offset(offset).all()

    db.close()
    if not results:
        raise HTTPException(status_code=404, detail="No seat allotments found")
    return {"total": total, "data": results}

@app.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    college_codes = db.query(SeatAllotment.collegecode).distinct().all()
    categories = db.query(SeatAllotment.category).distinct().all()
    
    return {
        "collegeCodes": [cc[0] for cc in college_codes],
        "categories": [cat[0] for cat in categories]
    }

@app.get("/collegeList")
def get_college_list(
    db: Session = Depends(get_db),
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
    query = db.query(College)
    if collegecode:
        query = query.filter(College.collegecode==collegecode)    # Apply search filters
 
    if city:
        query = query.filter(College.city == city)

    results = query.all()
        # Get total count
    total = query.count()
    
    # Apply pagination
    results = query.limit(limit).offset(offset).all()

    db.close()
    if not results:
        raise HTTPException(status_code=404, detail="No Colleges found")
    return {"total": total, "data": results}

@app.get("/Collegefilters")
def get_filters(db: Session = Depends(get_db)):
    locationcodes = db.query(College.location).distinct().all()
    citycodes = db.query(College.city).distinct().all()
    
    return {
        "locations": [lc[0] for lc in locationcodes],
        "cities": [cc[0] for cc in citycodes]
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