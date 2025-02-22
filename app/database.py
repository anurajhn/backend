#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:47:57 2025

@author: rachna
"""
# backend/app/database.py
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#DATABASE="sqlite"
#DATABASE="postgress"

DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")

if DATABASE_TYPE == "sqlite":
    DATABASE_URL = os.getenv("SQLITE_URL")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    DATABASE_URL = os.getenv("POSTGRES_URL")
    engine = create_async_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    Base = declarative_base()



