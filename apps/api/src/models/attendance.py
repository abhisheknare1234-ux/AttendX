import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from apps.api.src.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    PENDING_REVIEW = "PENDING_REVIEW"
    EXCUSED = "EXCUSED"


class AttemptMethod(str, enum.Enum):
    QR_CODE = "QR_CODE"
    PIN_FALLBACK = "PIN_FALLBACK"


class DecisionOutcome(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.DRAFT, nullable=False, index=True)
    checkin_window_minutes = Column(Integer, default=5, nullable=False)
    qr_refresh_seconds = Column(Integer, default=30, nullable=False)
    current_pin_hash = Column(String(255), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    require_face = Column(Boolean, default=True, nullable=False)
    require_geofence = Column(Boolean, default=True, nullable=False)
    require_liveness = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="sessions")
    teacher = relationship("TeacherProfile", back_populates="sessions")
    classroom = relationship("Classroom", back_populates="sessions")
    qr_tokens = relationship("DynamicQRToken", back_populates="session", cascade="all, delete-orphan")
    attempts = relationship("AttendanceAttempt", back_populates="session", cascade="all, delete-orphan")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class DynamicQRToken(Base):
    __tablename__ = "dynamic_qr_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    token_nonce = Column(String(64), unique=True, nullable=False, index=True)
    hmac_signature = Column(String(128), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="qr_tokens")


class AttendanceAttempt(Base):
    __tablename__ = "attendance_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    method = Column(Enum(AttemptMethod), default=AttemptMethod.QR_CODE, nullable=False)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    decision = Column(Enum(DecisionOutcome), nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="attempts")
    student = relationship("StudentProfile", back_populates="attendance_attempts")
    evidence = relationship("VerificationEvidence", back_populates="attempt", uselist=False, cascade="all, delete-orphan")
    risk_decision = relationship("RiskDecision", back_populates="attempt", uselist=False, cascade="all, delete-orphan")


class VerificationEvidence(Base):
    __tablename__ = "verification_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("attendance_attempts.id", ondelete="CASCADE"), unique=True, nullable=False)
    qr_status = Column(String(50), nullable=False)  # PASSED, FAILED, EXPIRED, NOT_PRESENT
    pin_status = Column(String(50), nullable=False)  # PASSED, FAILED, LOCKED_OUT, NOT_USED
    geo_status = Column(String(50), nullable=False)  # INSIDE, OUTSIDE, PERMISSION_DENIED, UNAVAILABLE, ACCURACY_POOR
    geo_distance_meters = Column(Float, nullable=True)
    geo_accuracy_meters = Column(Float, nullable=True)
    face_status = Column(String(50), nullable=False)  # MATCH, MISMATCH, NO_FACE, NOT_ENROLLED, UNAVAILABLE, NOT_REQUIRED
    face_similarity_score = Column(Float, nullable=True)
    liveness_status = Column(String(50), nullable=False)  # PASSED, FAILED, NOT_CONFIGURED, UNAVAILABLE, NOT_REQUIRED
    liveness_score = Column(Float, nullable=True)
    evidence_summary = Column(Text, nullable=True)  # JSON-encoded summary

    # Relationships
    attempt = relationship("AttendanceAttempt", back_populates="evidence")


class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("attendance_attempts.id", ondelete="CASCADE"), unique=True, nullable=False)
    calculated_risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    primary_reason_code = Column(String(50), nullable=False)
    reason_codes = Column(Text, nullable=False)  # JSON-encoded array of reason codes
    action_taken = Column(String(50), nullable=False)  # AUTO_ACCEPT, SEND_TO_REVIEW, AUTO_REJECT
    decided_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    attempt = relationship("AttendanceAttempt", back_populates="risk_decision")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False)
    marked_via = Column(String(50), default="VERIFIED_CHECKIN", nullable=False)
    attempt_id = Column(String(36), ForeignKey("attendance_attempts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("StudentProfile", back_populates="attendance_records")
    corrections = relationship("AttendanceCorrection", back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student_record"),
    )


class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    record_id = Column(String(36), ForeignKey("attendance_records.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)  # Mandatory reason for manual correction
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    record = relationship("AttendanceRecord", back_populates="corrections")
    teacher = relationship("TeacherProfile", back_populates="corrections")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")

