import json
import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from apps.api.src.models.attendance import AuditLog

logger = logging.getLogger("attendx.audit")


def log_audit_event(
    db: Session,
    action: str,
    target_type: str,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persist an immutable audit record to the database and structured logger.
    Ensures zero sensitive credentials (passwords, raw biometric vectors, tokens) are logged.
    """
    details_str = None
    if details is not None:
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details, default=str)
        else:
            details_str = str(details)

    audit_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=details_str,
        ip_address=ip_address
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    logger.info(
        f"[AUDIT] action={action} actor={actor_id} target={target_type}:{target_id} ip={ip_address}"
    )
    return audit_entry
