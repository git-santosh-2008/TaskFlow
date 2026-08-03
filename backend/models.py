"""
SQLAlchemy ORM Models
======================
User -> Project -> Task relationships.
"""


from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship


from database import Base




class User(Base):
    __tablename__ = "users"


    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)


    # Relationship: User -> Projects
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")




class Project(Base):
    __tablename__ = "projects"


    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)


    # Relationships: Project -> User, Project -> Tasks
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")




class Task(Base):
    __tablename__ = "tasks"


    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    priority = Column(String, nullable=False)  # Restricted to "low", "medium", "high"
    due_date = Column(String, nullable=True)   # Plain text raw date (e.g. "next friday")
    status = Column(String, default="pending")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)


    # Relationship: Task -> Project
    project = relationship("Project", back_populates="tasks")


    # DB-level guard (in addition to the Pydantic Field pattern in schemas.py)
    # so the closed set "low"/"medium"/"high" is enforced even on direct DB writes.
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_task_priority_enum"),
    )

