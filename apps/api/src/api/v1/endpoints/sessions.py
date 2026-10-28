from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_teacher, get_current_user
from apps.api.src.core.security import (
    generate_qr_token_payload,
    generate_temporary_pin,
    hash_pin,
    ensure_utc,
)
from apps.api.src.core.audit import log_audit_event
from apps.api.src.models.user import User, UserRole
from apps.api.src.models.academic import Subject, Classroom, ClassEnrollment
from apps.api.src.models.attendance import (
    AttendanceSession,
    DynamicQRToken,
    AttendanceRecord,
    AttendanceAttempt,
    SessionStatus,
    AttendanceStatus,
)
from apps.api.src.schemas.attendance import (
    SessionCreateRequest,
    SessionResponse,
    QRTokenResponse,
    SessionPINResponse,
)

router = APIRouter(prefix="/sessions", tags=["Attendance Sessions"])


@router.post("", response_model=SessionResponse)
def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Create a new attendance verification session in DRAFT state."""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Verify classroom exists
    classroom = db.query(Classroom).filter(Classroom.id == payload.classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # If teacher role, verify teacher profile
    teacher_id = current_user.teacher_profile.id if current_user.teacher_profile else None
    if not teacher_id and current_user.role == UserRole.ADMIN:
        # Admin can select or create session
        first_teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
        if first_teacher and first_teacher.teacher_profile:
            teacher_id = first_teacher.teacher_profile.id
        else:
            raise HTTPException(status_code=400, detail="No teacher profile available to bind session.")

    session = AttendanceSession(
        subject_id=payload.subject_id,
        teacher_id=teacher_id,
        classroom_id=payload.classroom_id,
        status=SessionStatus.DRAFT,
        checkin_window_minutes=payload.checkin_window_minutes,
        qr_refresh_seconds=payload.qr_refresh_seconds,
        require_face=payload.require_face,
        require_geofence=payload.require_geofence,
        require_liveness=payload.require_liveness
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    log_audit_event(
        db=db,
        action="SESSION_CREATED",
        actor_id=current_user.id,
        target_type="attendance_session",
        target_id=session.id,
        details={"subject": subject.title, "classroom": classroom.name}
    )

    return SessionResponse(
        id=session.id,
        subject_id=session.subject_id,
        subject_code=subject.code,
        subject_title=subject.title,
        classroom_name=classroom.name,
        classroom_building=classroom.building,
        teacher_name=f"{current_user.first_name} {current_user.last_name}",
        status=session.status,
        checkin_window_minutes=session.checkin_window_minutes,
        qr_refresh_seconds=session.qr_refresh_seconds,
        require_face=session.require_face,
        require_geofence=session.require_geofence,
        require_liveness=session.require_liveness
    )


@router.post("/{session_id}/open", response_model=SessionResponse)
def open_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Open an attendance session and start the check-in window."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot open session in '{session.status.value}' state. Must be DRAFT."
        )

    # Generate initial high-entropy 6-digit PIN and store hashed with session salt
    pin = generate_temporary_pin()
    session.current_pin_hash = hash_pin(pin, session.id)
    session.status = SessionStatus.OPEN
    session.opened_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)

    # Attach plaintext PIN to temporary attribute for returning in response if needed
    setattr(session, "_active_plain_pin", pin)

    log_audit_event(
        db=db,
        action="SESSION_OPENED",
        actor_id=current_user.id,
        target_type="attendance_session",
        target_id=session.id,
        details={"window_minutes": session.checkin_window_minutes}
    )

    return SessionResponse(
        id=session.id,
        subject_id=session.subject_id,
        subject_code=session.subject.code if session.subject else None,
        subject_title=session.subject.title if session.subject else None,
        classroom_name=session.classroom.name if session.classroom else None,
        classroom_building=session.classroom.building if session.classroom else None,
        teacher_name=f"{session.teacher.user.first_name} {session.teacher.user.last_name}" if session.teacher and session.teacher.user else None,
        status=session.status,
        checkin_window_minutes=session.checkin_window_minutes,
        qr_refresh_seconds=session.qr_refresh_seconds,
        opened_at=session.opened_at,
        require_face=session.require_face,
        require_geofence=session.require_geofence,
        require_liveness=session.require_liveness
    )


@router.post("/{session_id}/close", response_model=SessionResponse)
def close_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Close an attendance session. Prevents any further check-ins."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail=f"Cannot close session in state '{session.status.value}'")

    session.status = SessionStatus.CLOSED
    session.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)

    log_audit_event(
        db=db,
        action="SESSION_CLOSED",
        actor_id=current_user.id,
        target_type="attendance_session",
        target_id=session.id
    )

    return SessionResponse(
        id=session.id,
        subject_id=session.subject_id,
        subject_code=session.subject.code if session.subject else None,
        subject_title=session.subject.title if session.subject else None,
        classroom_name=session.classroom.name if session.classroom else None,
        classroom_building=session.classroom.building if session.classroom else None,
        teacher_name=f"{session.teacher.user.first_name} {session.teacher.user.last_name}" if session.teacher and session.teacher.user else None,
        status=session.status,
        checkin_window_minutes=session.checkin_window_minutes,
        qr_refresh_seconds=session.qr_refresh_seconds,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        require_face=session.require_face,
        require_geofence=session.require_geofence,
        require_liveness=session.require_liveness
    )


@router.get("/{session_id}/qr-token", response_model=QRTokenResponse)
def get_fresh_qr_token(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    Generate a dynamic cryptographically signed short-lived QR token for live display.
    Teacher-only authoritative stream.
    """
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.OPEN:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not OPEN (current status: {session.status.value}). Cannot generate live QR."
        )

    # Check window expiration
    now = datetime.now(timezone.utc)
    if session.opened_at:
        opened_at_utc = ensure_utc(session.opened_at)
        window_end = opened_at_utc + timedelta(minutes=session.checkin_window_minutes)
        if now > window_end:
            session.status = SessionStatus.CLOSED
            session.closed_at = now
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Attendance check-in window has expired. Session automatically closed."
            )

    token_str, nonce, expires_at = generate_qr_token_payload(
        session_id=session.id,
        valid_seconds=session.qr_refresh_seconds
    )

    # Record token in dynamic_qr_tokens table for server-side replay defense
    db_token = DynamicQRToken(
        session_id=session.id,
        token_nonce=nonce,
        hmac_signature=token_str.split(".")[-1],
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()

    return QRTokenResponse(
        session_id=session.id,
        token_str=token_str,
        nonce=nonce,
        expires_at=expires_at,
        valid_seconds=session.qr_refresh_seconds,
        server_time=now
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_details(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch session status, configured verification factors, and live counts."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Count enrolled students
    total_enrolled = db.query(ClassEnrollment).filter(ClassEnrollment.class_id == session.subject.class_id).count() if session.subject else 0
    total_present = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.status == AttendanceStatus.PRESENT
    ).count()
    total_pending = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.status == AttendanceStatus.PENDING_REVIEW
    ).count()

    return SessionResponse(
        id=session.id,
        subject_id=session.subject_id,
        subject_code=session.subject.code if session.subject else None,
        subject_title=session.subject.title if session.subject else None,
        classroom_name=session.classroom.name if session.classroom else None,
        classroom_building=session.classroom.building if session.classroom else None,
        teacher_name=f"{session.teacher.user.first_name} {session.teacher.user.last_name}" if session.teacher and session.teacher.user else None,
        status=session.status,
        checkin_window_minutes=session.checkin_window_minutes,
        qr_refresh_seconds=session.qr_refresh_seconds,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        require_face=session.require_face,
        require_geofence=session.require_geofence,
        require_liveness=session.require_liveness,
        total_enrolled=total_enrolled,
        total_present=total_present,
        total_pending_review=total_pending
    )


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    status: Optional[SessionStatus] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sessions relevant to current user role."""
    query = db.query(AttendanceSession)
    if status:
        query = query.filter(AttendanceSession.status == status)

    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        query = query.filter(AttendanceSession.teacher_id == current_user.teacher_profile.id)

    sessions = query.order_by(AttendanceSession.created_at.desc()).limit(limit).all()
    results = []
    for s in sessions:
        present_cnt = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == s.id,
            AttendanceRecord.status == AttendanceStatus.PRESENT
        ).count()
        pending_cnt = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == s.id,
            AttendanceRecord.status == AttendanceStatus.PENDING_REVIEW
        ).count()
        results.append(
            SessionResponse(
                id=s.id,
                subject_id=s.subject_id,
                subject_code=s.subject.code if s.subject else None,
                subject_title=s.subject.title if s.subject else None,
                classroom_name=s.classroom.name if s.classroom else None,
                classroom_building=s.classroom.building if s.classroom else None,
                teacher_name=f"{s.teacher.user.first_name} {s.teacher.user.last_name}" if s.teacher and s.teacher.user else None,
                status=s.status,
                checkin_window_minutes=s.checkin_window_minutes,
                qr_refresh_seconds=s.qr_refresh_seconds,
                opened_at=s.opened_at,
                closed_at=s.closed_at,
                require_face=s.require_face,
                require_geofence=s.require_geofence,
                require_liveness=s.require_liveness,
                total_present=present_cnt,
                total_pending_review=pending_cnt
            )
        )
    return results
