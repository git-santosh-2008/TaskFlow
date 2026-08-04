"""
TaskFlow Backend API - Application Entry Point
=================================================
Wires together the database, middleware, CORS and routers.
Run with:  uvicorn main:app --reload
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from middleware import log_requests
from routers import users, projects, tasks

# =========================================================
# Logging Setup
# =========================================================
logging.basicConfig(level=logging.INFO)

# =========================================================
# Create Database Tables
# =========================================================
Base.metadata.create_all(bind=engine)


# =========================================================
# FastAPI App Initialization
# =========================================================
app = FastAPI(title="TaskFlow Backend API")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)


# Custom Request Logging Middleware
app.middleware("http")(log_requests)


# =========================================================
# Register Routers
# =========================================================
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)




@app.get("/")
def read_root():
    return {"message": "TaskFlow Backend API is running successfully!"}

