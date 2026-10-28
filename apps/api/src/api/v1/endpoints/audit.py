from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_admin
from apps.api.src.models.attendance import AuditLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/audit", tags=["Security Audit Trail"])


class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[AuditLogResponse])
def list_audit_events(
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    """Retrieve security audit ledger events (Admin only)."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
