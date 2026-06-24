"""Tag management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from .. import crud_pro
from ..schemas_pro import TagCreate, TagUpdate, TagResponse

router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.post("", response_model=TagResponse)
async def create_tag(
    tag_create: TagCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tag."""
    try:
        return crud_pro.create_tag(db, tag_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag_detail(
    tag_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tag details."""
    tag = crud_pro.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.get("", response_model=list[TagResponse])
async def get_tags_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of tags."""
    tags, _ = crud_pro.get_tags(db, skip=skip, limit=limit)
    return tags


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tag."""
    tag = crud_pro.update_tag(db, tag_id, tag_update)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete tag."""
    success = crud_pro.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}
