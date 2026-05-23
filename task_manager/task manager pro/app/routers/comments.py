"""Comment management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from ..permissions import check_task_access
from .. import crud_pro
from ..schemas_pro import (
    CommentCreate, CommentUpdate, CommentResponse, CommentDetailResponse,
)

router = APIRouter(prefix="/api", tags=["Comments"])


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse)
async def create_comment(
    task_id: int,
    comment_create: CommentCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a comment on a task."""
    await check_task_access(db, task_id, current_user)
    comment = crud_pro.create_comment(db, task_id, current_user, comment_create)
    if not comment:
        raise HTTPException(status_code=400, detail="Failed to create comment")
    return comment


@router.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
async def get_task_comments(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comments for a task."""
    await check_task_access(db, task_id, current_user)
    comments, _ = crud_pro.get_task_comments(db, task_id, skip=skip, limit=limit)
    return comments


@router.get("/comments/{comment_id}", response_model=CommentDetailResponse)
async def get_comment_detail(
    comment_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comment details."""
    comment = crud_pro.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await check_task_access(db, comment.task_id, current_user)
    return comment


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update comment."""
    comment = crud_pro.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.creator_id != current_user:
        raise HTTPException(status_code=403, detail="Can only edit your own comments")

    updated = crud_pro.update_comment(db, comment_id, comment_update, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Comment not found")
    return updated


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete comment."""
    comment = crud_pro.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.creator_id != current_user:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")

    success = crud_pro.delete_comment(db, comment_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"deleted": True}

