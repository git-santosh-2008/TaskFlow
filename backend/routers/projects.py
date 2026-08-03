"""
Project Endpoints
====================
Includes the SQL aggregation statistics endpoint.
"""


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session


from dependencies import get_db
from models import Project, Task, User
from schemas import ProjectCreate, ProjectResponse


router = APIRouter(prefix="/projects", tags=["Projects"])




@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    owner = db.query(User).filter(User.id == project.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="User/Owner not found")


    db_project = Project(title=project.title, owner_id=project.owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

