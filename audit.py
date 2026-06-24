"""Audit log API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from .. import crud_pro
from ..schemas_pro import AuditLogResponse

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=list[AuditLogResponse])
async def get_audit_logs(
    entity_type: str = Query(None),
    entity_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs. Only admins can view all logs."""
    logs, _ = crud_pro.get_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )
    return logs


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogResponse])
async def get_entity_audit_logs(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a specific entity."""
    logs, _ = crud_pro.get_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )
    return logs
