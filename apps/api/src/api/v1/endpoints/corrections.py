from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_teacher
from apps.api.src.core.audit import log_audit_event
from apps.api.src.models.user import User
from apps.api.src.models.attendance import (
    AttendanceRecord,
    AttendanceSession,
    AttendanceCorrection,
    AttendanceStatus,
)
from apps.api.src.schemas.attendance import CorrectionRequest, CorrectionResponse

router = APIRouter(prefix="/corrections", tags=["Attendance Corrections & Overrides"])


@router.post("/sessions/{session_id}", response_model=CorrectionResponse)
def apply_attendance_correction(
    session_id: str,
    payload: CorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    Apply a controlled manual attendance correction with mandatory audit justification.
    Never silently overwrites records.
    """
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    teacher_id = current_user.teacher_profile.id if current_user.teacher_profile else None
    if not teacher_id:
        raise HTTPException(status_code=400, detail="User lacks teacher profile")

    # Fetch or initialize record
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id,
        AttendanceRecord.student_id == payload.student_id
    ).first()

    previous_status = record.status.value if record else "ABSENT"

    if not record:
        record = AttendanceRecord(
            session_id=session_id,
            student_id=payload.student_id,
            status=payload.new_status,
            marked_via="TEACHER_MANUAL_CORRECTION"
        )
        db.add(record)
        db.flush()
    else:
        record.status = payload.new_status
        record.marked_via = "TEACHER_MANUAL_CORRECTION"

    correction = AttendanceCorrection(
        record_id=record.id,
        teacher_id=teacher_id,
        previous_status=previous_status,
        new_status=payload.new_status.value,
        reason=payload.reason
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)

    log_audit_event(
        db=db,
        action="ATTENDANCE_MANUALLY_CORRECTED",
        actor_id=current_user.id,
        target_type="attendance_record",
        target_id=record.id,
        details={
            "student_id": payload.student_id,
            "previous_status": previous_status,
            "new_status": payload.new_status.value,
            "reason": payload.reason
        }
    )

    teacher_name = f"{current_user.first_name} {current_user.last_name}"
    return CorrectionResponse(
        record_id=record.id,
        student_id=payload.student_id,
        previous_status=previous_status,
        new_status=payload.new_status.value,
        teacher_name=teacher_name,
        reason=payload.reason,
        timestamp=correction.timestamp
    )


@router.get("/sessions/{session_id}", response_model=List[CorrectionResponse])
def list_session_corrections(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Retrieve full history of manual corrections made for a session."""
    corrections = db.query(AttendanceCorrection).join(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id
    ).order_by(AttendanceCorrection.timestamp.desc()).all()

    results = []
    for c in corrections:
        teacher_name = f"{c.teacher.user.first_name} {c.teacher.user.last_name}" if c.teacher and c.teacher.user else "Teacher"
        results.append(
            CorrectionResponse(
                record_id=c.record_id,
                student_id=c.record.student_id if c.record else "",
                previous_status=c.previous_status,
                new_status=c.new_status,
                teacher_name=teacher_name,
                reason=c.reason,
                timestamp=c.timestamp
            )
        )
    return results

