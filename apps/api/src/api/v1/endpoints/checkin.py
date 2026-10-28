import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_student, get_current_user
from apps.api.src.core.security import verify_qr_token_payload, verify_pin, ensure_utc
from apps.api.src.core.audit import log_audit_event
from apps.api.src.models.user import User, UserRole
from apps.api.src.models.academic import ClassEnrollment
from apps.api.src.models.attendance import (
    AttendanceSession,
    DynamicQRToken,
    AttendanceAttempt,
    VerificationEvidence,
    RiskDecision,
    AttendanceRecord,
    SessionStatus,
    AttendanceStatus,
    DecisionOutcome,
    AttemptMethod,
)
from apps.api.src.schemas.attendance import CheckInSubmission, CheckInResultResponse
from apps.api.src.services.geofence_service import GeofenceService
from apps.api.src.services.biometric_service import BiometricVerificationService
from apps.api.src.services.liveness_service import LivenessDetectionService
from apps.api.src.services.risk_engine import RiskEngine

router = APIRouter(prefix="/checkin", tags=["Student Attendance Check-In"])


@router.post("", response_model=CheckInResultResponse)
def submit_attendance_checkin(
    payload: CheckInSubmission,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """
    Authoritative student attendance submission endpoint.
    Fuses QR/PIN, Geofence GPS, Facial Biometrics, and Liveness evidence
    through the explainable Risk Engine into a persistent ledger record.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")
    student_profile = current_user.student_profile
    if not student_profile:
        raise HTTPException(status_code=400, detail="Student profile is missing from this user account")

    # 1. Fetch Session
    session = db.query(AttendanceSession).filter(AttendanceSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    # 2. Check Session Open Status and Check-in Window
    now = datetime.now(timezone.utc)
    session_is_open = (session.status == SessionStatus.OPEN)
    if session_is_open and session.opened_at:
        opened_at_utc = ensure_utc(session.opened_at)
        window_end = opened_at_utc + timedelta(minutes=session.checkin_window_minutes)
        if now > window_end:
            session.status = SessionStatus.CLOSED
            session.closed_at = now
            db.commit()
            session_is_open = False

    # 3. Check Enrollment
    is_enrolled = False
    if session.subject:
        enrollment = db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == session.subject.class_id,
            ClassEnrollment.student_id == student_profile.id
        ).first()
        is_enrolled = (enrollment is not None)

    # 4. Check Duplicate Record
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == student_profile.id
    ).first()
    already_marked = (existing_record is not None and existing_record.status in [AttendanceStatus.PRESENT, AttendanceStatus.PENDING_REVIEW])

    # 5. Evaluate QR or PIN Evidence
    qr_status = "NOT_PRESENT"
    pin_status = "NOT_USED"

    if payload.method == AttemptMethod.QR_CODE:
        if not payload.qr_token:
            qr_status = "MISSING_TOKEN"
        else:
            is_valid_token, reason = verify_qr_token_payload(payload.qr_token, session.id)
            if is_valid_token:
                qr_status = "PASSED"
            elif reason == "TOKEN_EXPIRED":
                qr_status = "EXPIRED"
            else:
                qr_status = f"FAILED_{reason}"
    else:
        # PIN Fallback
        if not payload.pin:
            pin_status = "MISSING_PIN"
        elif not session.current_pin_hash:
            pin_status = "NO_PIN_CONFIGURED"
        else:
            if verify_pin(payload.pin, session.current_pin_hash, session.id):
                pin_status = "PASSED"
            else:
                pin_status = "FAILED"

    # 6. Evaluate Geofence Spatial Evidence
    geo_status, geo_dist, geo_reason = "UNAVAILABLE", None, "Geofence check not evaluated"
    if session.require_geofence and session.classroom:
        geo_status, geo_dist, geo_reason = GeofenceService.evaluate_location_evidence(
            classroom_lat=session.classroom.latitude,
            classroom_lon=session.classroom.longitude,
            radius_meters=session.classroom.radius_meters,
            student_lat=payload.latitude,
            student_lon=payload.longitude,
            reported_accuracy_meters=payload.accuracy_meters
        )
    else:
        geo_status = "NOT_REQUIRED"

    # 7. Evaluate Face Biometrics Evidence
    face_status, face_sim, face_reason = BiometricVerificationService.evaluate_face_evidence(
        enrolled_reference=student_profile.biometric_reference,
        live_embedding=payload.face_embedding,
        capture_quality=payload.face_capture_quality,
        is_required=session.require_face
    )

    # 8. Evaluate Liveness Anti-Spoofing Evidence
    liveness_status, liveness_score, liveness_reason = LivenessDetectionService.evaluate_liveness(
        liveness_confirmed=payload.liveness_confirmed,
        is_required=session.require_liveness
    )

    # 9. Multi-Factor Risk Engine Evaluation
    decision, risk_level, primary_reason, reason_codes, action_taken = RiskEngine.evaluate_checkin(
        session_is_open=session_is_open,
        is_enrolled=is_enrolled,
        already_marked=already_marked,
        qr_status=qr_status,
        pin_status=pin_status,
        geo_status=geo_status,
        face_status=face_status,
        liveness_status=liveness_status,
        attempt_method=payload.method.value
    )

    # 10. Persist Attendance Attempt
    attempt = AttendanceAttempt(
        session_id=session.id,
        student_id=student_profile.id,
        method=payload.method,
        client_ip=client_ip,
        user_agent=user_agent[:250],
        decision=decision
    )
    db.add(attempt)
    db.flush()

    # Evidence details JSON
    evidence_dict = {
        "qr_status": qr_status,
        "pin_status": pin_status,
        "geo_status": geo_status,
        "geo_distance_meters": geo_dist,
        "geo_accuracy_meters": payload.accuracy_meters,
        "geo_detail": geo_reason,
        "face_status": face_status,
        "face_similarity": face_sim,
        "face_detail": face_reason,
        "liveness_status": liveness_status,
        "liveness_score": liveness_score,
        "liveness_detail": liveness_reason
    }

    # Persist Verification Evidence
    evidence_entry = VerificationEvidence(
        attempt_id=attempt.id,
        qr_status=qr_status,
        pin_status=pin_status,
        geo_status=geo_status,
        geo_distance_meters=geo_dist,
        geo_accuracy_meters=payload.accuracy_meters,
        face_status=face_status,
        face_similarity_score=face_sim,
        liveness_status=liveness_status,
        liveness_score=liveness_score,
        evidence_summary=json.dumps(evidence_dict)
    )
    db.add(evidence_entry)

    # Persist Risk Decision
    risk_entry = RiskDecision(
        attempt_id=attempt.id,
        calculated_risk_level=risk_level,
        primary_reason_code=primary_reason,
        reason_codes=json.dumps(reason_codes),
        action_taken=action_taken
    )
    db.add(risk_entry)

    # 11. Update Official Attendance Record Ledger
    if decision == DecisionOutcome.ACCEPTED:
        official_rec = AttendanceRecord(
            session_id=session.id,
            student_id=student_profile.id,
            status=AttendanceStatus.PRESENT,
            marked_via=f"VERIFIED_{payload.method.value}",
            attempt_id=attempt.id
        )
        db.add(official_rec)
    elif decision == DecisionOutcome.REQUIRES_REVIEW:
        review_rec = AttendanceRecord(
            session_id=session.id,
            student_id=student_profile.id,
            status=AttendanceStatus.PENDING_REVIEW,
            marked_via="QUEUED_FOR_TEACHER_REVIEW",
            attempt_id=attempt.id
        )
        db.add(review_rec)

    db.commit()

    # Audit Logging
    log_audit_event(
        db=db,
        action=f"CHECKIN_{decision.value}",
        actor_id=current_user.id,
        target_type="attendance_attempt",
        target_id=attempt.id,
        details={
            "session_id": session.id,
            "decision": decision.value,
            "risk_level": risk_level.value,
            "primary_reason": primary_reason
        },
        ip_address=client_ip
    )

    return CheckInResultResponse(
        attempt_id=attempt.id,
        session_id=session.id,
        decision=decision,
        status="PRESENT" if decision == DecisionOutcome.ACCEPTED else ("PENDING_REVIEW" if decision == DecisionOutcome.REQUIRES_REVIEW else "REJECTED"),
        risk_level=risk_level,
        primary_reason=primary_reason,
        reason_codes=reason_codes,
        evidence_summary=evidence_dict,
        timestamp=now
    )
