"""
User Endpoints
================
"""


from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session


from dependencies import get_db
from models import User
from schemas import UserCreate, UserResponse


router = APIRouter(prefix="/users", tags=["Users"])




@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




@router.get("", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

