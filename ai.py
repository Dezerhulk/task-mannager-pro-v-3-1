"""AI-assisted task and project helpers."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud_pro
from ..auth import get_current_user
from ..database_pro import get_db
from ..permissions import check_project_access
from ..schemas_pro import AIProjectSummaryResponse, TaskCreate, TaskGenerationRequest, TaskGenerationResponse

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/summarize-project/{project_id}", response_model=AIProjectSummaryResponse)
async def summarize_project(
    project_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a lightweight summary for a project."""
    await check_project_access(db, project_id, current_user, permission="project:read")
    tasks, _ = crud_pro.get_project_tasks(db, project_id)
    now = datetime.now(timezone.utc)
    done = sum(1 for task in tasks if task.status.value == "done")
    in_progress = sum(1 for task in tasks if task.status.value == "in_progress")
    overdue = sum(1 for task in tasks if task.deadline and task.deadline < now and task.status.value != "done")

    return {
        "project_id": project_id,
        "total_tasks": len(tasks),
        "done_tasks": done,
        "in_progress_tasks": in_progress,
        "overdue_tasks": overdue,
        "owners": [task.project.owner.username for task in tasks if task.project and task.project.owner][:1] or [],
    }


@router.post("/create-tasks", response_model=TaskGenerationResponse)
async def create_tasks_from_text(
    payload: TaskGenerationRequest,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create tasks from a freeform text description using simple parsing."""
    await check_project_access(db, payload.project_id, current_user, permission="project:read")

    items = [line.strip().lstrip("-*") for line in payload.text.splitlines() if line.strip()]
    created_tasks = []

    for item in items:
        task_create = TaskCreate(
            project_id=payload.project_id,
            title=item[:255],
            description=item,
            assignee_id=payload.assignee_id,
            tag_ids=[],
        )
        task = crud_pro.create_task(db, task_create, current_user)
        if task:
            created_tasks.append(task)

    return {"project_id": payload.project_id, "tasks": created_tasks}
