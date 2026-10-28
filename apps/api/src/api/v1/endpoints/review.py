import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_teacher
from apps.api.src.core.audit import log_audit_event
from apps.api.src.models.user import User, UserRole
from apps.api.src.models.attendance import (
    AttendanceAttempt,
    AttendanceRecord,
    AttendanceSession,
    AttendanceCorrection,
    AttendanceStatus,
    DecisionOutcome,
)
from apps.api.src.schemas.attendance import ReviewItemResponse, ReviewActionRequest

router = APIRouter(prefix="/review", tags=["Teacher Review Queue"])


@router.get("/queue", response_model=List[ReviewItemResponse])
def get_teacher_review_queue(
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Retrieve check-ins flagged for manual teacher inspection."""
    query = db.query(AttendanceAttempt).join(AttendanceSession).filter(
        AttendanceAttempt.decision == DecisionOutcome.REQUIRES_REVIEW
    )

    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        query = query.filter(AttendanceSession.teacher_id == current_user.teacher_profile.id)

    if session_id:
        query = query.filter(AttendanceAttempt.session_id == session_id)

    attempts = query.order_by(AttendanceAttempt.submitted_at.desc()).all()
    results = []
    for att in attempts:
        student = att.student
        user = student.user if student else None
        student_name = f"{user.first_name} {user.last_name}" if user else "Unknown Student"
        roll_no = student.roll_number if student else "N/A"
        subject_title = att.session.subject.title if att.session and att.session.subject else "N/A"

        reason_list = []
        primary_reason = "UNCERTAIN_VERIFICATION"
        risk_lvl = "MEDIUM"
        if att.risk_decision:
            primary_reason = att.risk_decision.primary_reason_code
            risk_lvl = att.risk_decision.calculated_risk_level.value
            try:
                reason_list = json.loads(att.risk_decision.reason_codes)
            except Exception:
                reason_list = [att.risk_decision.reason_codes]

        ev = att.evidence
        results.append(
            ReviewItemResponse(
                attempt_id=att.id,
                session_id=att.session_id,
                student_id=att.student_id,
                student_name=student_name,
                roll_number=roll_no,
                subject_title=subject_title,
                submitted_at=att.submitted_at,
                method=att.method.value,
                risk_level=risk_lvl,
                primary_reason=primary_reason,
                reason_codes=reason_list,
                geo_status=ev.geo_status if ev else "UNAVAILABLE",
                geo_distance_meters=ev.geo_distance_meters if ev else None,
                geo_accuracy_meters=ev.geo_accuracy_meters if ev else None,
                face_status=ev.face_status if ev else "UNAVAILABLE",
                face_similarity_score=ev.face_similarity_score if ev else None,
                liveness_status=ev.liveness_status if ev else "UNAVAILABLE"
            )
        )
    return results


@router.post("/{attempt_id}/action")
def process_review_action(
    attempt_id: str,
    payload: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    Teacher action on queued attendance check-in.
    Actions:
    - APPROVE: sets official attendance to PRESENT
    - REJECT: sets official attendance to ABSENT
    Mandatory reason justification is audited.
    """
    attempt = db.query(AttendanceAttempt).filter(AttendanceAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attendance attempt not found")

    action_upper = payload.action.upper().strip()
    if action_upper not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == attempt.session_id,
        AttendanceRecord.student_id == attempt.student_id
    ).first()

    teacher_id = current_user.teacher_profile.id if current_user.teacher_profile else None
    if not teacher_id:
        raise HTTPException(status_code=400, detail="User has no associated teacher profile")

    previous_status = record.status.value if record else "NONE"
    new_status = AttendanceStatus.PRESENT if action_upper == "APPROVE" else AttendanceStatus.ABSENT

    if not record:
        record = AttendanceRecord(
            session_id=attempt.session_id,
            student_id=attempt.student_id,
            status=new_status,
            marked_via=f"TEACHER_REVIEW_{action_upper}",
            attempt_id=attempt.id
        )
        db.add(record)
        db.flush()
    else:
        record.status = new_status
        record.marked_via = f"TEACHER_REVIEW_{action_upper}"

    # Log manual correction / review ledger
    correction = AttendanceCorrection(
        record_id=record.id,
        teacher_id=teacher_id,
        previous_status=previous_status,
        new_status=new_status.value,
        reason=payload.reason
    )
    db.add(correction)
    db.commit()

    log_audit_event(
        db=db,
        action=f"TEACHER_REVIEW_{action_upper}",
        actor_id=current_user.id,
        target_type="attendance_record",
        target_id=record.id,
        details={
            "attempt_id": attempt.id,
            "previous_status": previous_status,
            "new_status": new_status.value,
            "reason": payload.reason
        }
    )

    return {
        "message": f"Check-in successfully processed with action {action_upper}",
        "record_id": record.id,
        "final_status": new_status.value
    }
