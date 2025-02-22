#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:49:43 2025

@author: rachna
"""
# backend/app/schemas.py
from pydantic import BaseModel
from typing import Optional

class CollegeSchema(BaseModel):
    id: int
    collegecode: str
    college: str
    location: str
    city: str

    class Config:
        from_attributes = True

class SeatAllotmentSchema(BaseModel):
    id: int
    cetyear: int
    cetround: Optional[str]
    collegecode: Optional[str]
    college: Optional[str]
    course: Optional[str]
    category: Optional[str]
    seatcount: Optional[int]
    cutoffrank: Optional[int]

    class Config:
        from_attributes = True
        