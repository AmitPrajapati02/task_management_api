"""Task HTTP routes: create, list (filters + sort), update status, delete."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.task import Task, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskOut,
    TaskStatusSchema,
    TaskStatusUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _map_status(s: TaskStatusSchema) -> TaskStatus:
    return TaskStatus(s.value)


def _to_task_out(row: Task) -> TaskOut:
    return TaskOut(
        id=row.id,
        title=row.title,
        description=row.description,
        status=TaskStatusSchema(row.status.value),
        created_at=row.created_at,
    )


@router.post(
    "",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Duplicate title within 5 seconds"},
        422: {"description": "Validation error"},
    },
)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    """Create a task; status defaults to pending. Enforces 5s duplicate title rule."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=5)
    dup = db.execute(
        select(Task.id).where(Task.title == payload.title, Task.created_at >= cutoff).limit(1)
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "duplicate_title",
                "message": "A task with this title was created within the last 5 seconds.",
            },
        )

    task = Task(
        title=payload.title,
        description=payload.description,
        status=TaskStatus.pending,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_task_out(task)


@router.get(
    "",
    response_model=TaskListResponse,
)
def list_tasks(
    db: Session = Depends(get_db),
    task_status: Optional[TaskStatusSchema] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> TaskListResponse:
    """List tasks, optional filters; latest first."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_date_range",
                "message": "start_date must be before or equal to end_date.",
            },
        )

    stmt = select(Task)
    if task_status is not None:
        stmt = stmt.where(Task.status == _map_status(task_status))
    if start_date is not None:
        stmt = stmt.where(Task.created_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(Task.created_at <= end_date)

    stmt = stmt.order_by(Task.created_at.desc())
    rows = db.scalars(stmt).all()
    items = [_to_task_out(r) for r in rows]
    return TaskListResponse(items=items, count=len(items))


@router.put(
    "/{task_id}",
    response_model=TaskOut,
    responses={
        404: {},
        422: {"description": "Validation error"},
    },
)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
) -> TaskOut:
    """Update only the task status."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Task with id {task_id} was not found.",
            },
        )

    task.status = _map_status(payload.status)
    db.commit()
    db.refresh(task)
    return _to_task_out(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {}},
)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Task with id {task_id} was not found.",
            },
        )

    db.delete(task)
    db.commit()
    return None
