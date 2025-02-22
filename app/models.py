#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:23:43 2025

@author: rachna
"""
# backend/app/models.py
from sqlalchemy import Column, Integer, String
from .database import Base

class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    collegecode = Column(String, unique=True, index=True)
    college = Column(String, nullable=True)
    location = Column(String, nullable=True)
    city = Column(String, nullable=True)

class SeatAllotment(Base):
    __tablename__ = "kcetcutoff20"
    id = Column(Integer, primary_key=True, index=True)
    cetyear = Column(Integer, index=True)
    cetround = Column(String, nullable=True)
    collegecode = Column(String, nullable=True)
    college = Column(String, nullable=True)
    course = Column(String, nullable=True)
    category = Column(String, nullable=True)
    seatcount = Column(Integer, nullable=True)
    cutoffrank = Column(Integer, nullable=True)
    
    