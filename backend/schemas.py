"""
Pydantic Schemas & Custom Validators
=====================================
Request/response models for Users, Projects and Tasks.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


# --- USER SCHEMAS ---
class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


# --- PROJECT SCHEMAS ---
class ProjectBase(BaseModel):
    title: str
    owner_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int

    class Config:
        from_attributes = True


# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(low|medium|high)$")
    due_date: Optional[str] = None
    status: Optional[str] = "pending"
    project_id: int

    # Custom Validator: Blank or whitespace-only check
    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Task title cannot be blank or contain only whitespace")
        return trimmed


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    due_date: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: int

    class Config:
        from_attributes = True


# --- SECTION 3: QUICK-ADD SCHEMA ---
class QuickAddRequest(BaseModel):
    """POST /tasks/quick-add request body."""
    description: str = Field(..., min_length=1)
    project_id: int