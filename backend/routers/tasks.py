"""
Task CRUD Endpoints + Section 2 sort/search endpoints
========================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Project, Task
from schemas import TaskCreate, TaskResponse, TaskUpdate, QuickAddRequest
from algorithms import insertion_sort, binary_search, linear_search
from quick_add import parse_task_description, build_parse_prompt

router = APIRouter(prefix="/tasks", tags=["Tasks"])

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


def _task_to_dict(task: Task) -> dict:
    """Plain dict view of a Task row — what the hand-rolled algorithms operate on."""
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "due_date": task.due_date,
        "status": task.status,
        "project_id": task.project_id,
    }


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
def list_tasks(
    sort: Optional[str] = Query(
        None,
        pattern="^(priority|due_date)$",
        description="Optional: 'priority' or 'due_date'. Ordering is produced by our own insertion_sort(), not the DB or Python's built-in sort.",
    ),
    db: Session = Depends(get_db),
):
    """
    Section 2, Task 4: fetches real rows from the database, then — when
    ?sort= is given — sorts them with our own insertion_sort() before
    returning JSON. Never db.order_by() and never sorted()/list.sort().
    """
    db_tasks = db.query(Task).all()
    records = [_task_to_dict(t) for t in db_tasks]

    if sort == "priority":
        for record in records:
            record["_priority_rank"] = PRIORITY_RANK.get(record["priority"], 0)
        insertion_sort(records, "_priority_rank")
        for record in records:
            del record["_priority_rank"]

    elif sort == "due_date":
        # due_date is nullable raw text; treat missing due dates as ""
        # so they sort first rather than crashing on a None comparison.
        for record in records:
            record["_due_date_sort_key"] = record["due_date"] or ""
        insertion_sort(records, "_due_date_sort_key")
        for record in records:
            del record["_due_date_sort_key"]

    return records


@router.get("/search", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def search_task_by_title(
    title: str = Query(..., min_length=1, description="Exact task title to find"),
    algo: str = Query("binary", pattern="^(binary|linear)$"),
    db: Session = Depends(get_db),
):
    """
    Section 2, Task 4: builds an in-memory {"id","title"} index from the
    real tasks table, then locates the exact-title match with our own
    binary_search (after sorting the index with our own insertion_sort)
    or linear_search over the unsorted index — never a dict/db lookup.

    NOTE: this route is declared before GET /{task_id} so "/tasks/search"
    is matched here and not swallowed by the {task_id}: int path param.
    """
    db_tasks = db.query(Task).all()
    tasks_by_id = {t.id: t for t in db_tasks}
    index = [{"id": t.id, "title": t.title} for t in db_tasks]

    if algo == "binary":
        insertion_sort(index, "title")
        position = binary_search(index, title, "title")
    else:
        position = linear_search(index, title, "title")

    if position is None:
        raise HTTPException(status_code=404, detail="No task with that exact title")

    matched_id = index[position]["id"]
    return tasks_by_id[matched_id]


@router.post("/quick-add", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def quick_add_task(payload: QuickAddRequest, db: Session = Depends(get_db)):
    """
    Section 3: create a task from one free-text sentence.

    - Builds a role-based (system + user) prompt via
      build_quick_add_messages() for structural parity with a real LLM
      call, then parses the description with parse_task_description()
      — the deterministic mock by default, always with zero API keys.
    - A project_id that doesn't exist is a 422 (not 404, unlike
      create_task above) per the Section 3 spec, shaped like a Pydantic
      validation error.
    - The parsed fields are validated through TaskCreate before any row
      is written — a validation failure is also a 422, and no row is
      created.

    NOTE: this route is declared before GET/PUT/DELETE /{task_id} so
    "/tasks/quick-add" is matched here and not swallowed by the
    {task_id}: int path param.
    """
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=422,
            detail=[{
                "loc": ["body", "project_id"],
                "msg": f"project_id {payload.project_id} does not reference an existing project",
                "type": "value_error.project_not_found",
            }],
        )

    # Role-based prompt (system + user messages) — built the same way
    # whether the mock or a real model ultimately answers it.
    messages = build_parse_prompt(payload.description)

    # Uses the mock by default; only tries a real LLM call when
    # USE_REAL_LLM=true AND a key is present, with automatic fallback.
    parsed = parse_task_description(payload.description, messages)

    try:
        validated = TaskCreate(
            title=parsed["title"],
            priority=parsed["priority"],
            due_date=parsed["due_date_hint"],
            status="pending",
            project_id=payload.project_id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    db_task = Task(**validated.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}