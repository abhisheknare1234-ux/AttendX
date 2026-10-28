from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from apps.api.src.models.attendance import (
    SessionStatus,
    AttendanceStatus,
    DecisionOutcome,
    RiskLevel,
    AttemptMethod,
)


class SessionCreateRequest(BaseModel):
    subject_id: str
    classroom_id: str
    checkin_window_minutes: int = Field(default=5, ge=1, le=60)
    qr_refresh_seconds: int = Field(default=30, ge=10, le=120)
    require_face: bool = True
    require_geofence: bool = True
    require_liveness: bool = False


class SessionResponse(BaseModel):
    id: str
    subject_id: str
    subject_code: Optional[str] = None
    subject_title: Optional[str] = None
    classroom_name: Optional[str] = None
    classroom_building: Optional[str] = None
    teacher_name: Optional[str] = None
    status: SessionStatus
    checkin_window_minutes: int
    qr_refresh_seconds: int
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    require_face: bool
    require_geofence: bool
    require_liveness: bool
    total_enrolled: Optional[int] = 0
    total_present: Optional[int] = 0
    total_pending_review: Optional[int] = 0

    class Config:
        from_attributes = True


class QRTokenResponse(BaseModel):
    session_id: str
    token_str: str
    nonce: str
    expires_at: datetime
    valid_seconds: int
    server_time: datetime


class SessionPINResponse(BaseModel):
    session_id: str
    pin: str
    expires_in_minutes: int


class CheckInSubmission(BaseModel):
    session_id: str
    method: AttemptMethod = AttemptMethod.QR_CODE
    qr_token: Optional[str] = None
    pin: Optional[str] = None
    # Geolocation Evidence
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_meters: Optional[float] = None
    # Biometric Evidence
    face_embedding: Optional[List[float]] = None
    face_capture_quality: Optional[float] = None
    liveness_confirmed: Optional[bool] = None


class CheckInResultResponse(BaseModel):
    attempt_id: str
    session_id: str
    decision: DecisionOutcome
    status: str
    risk_level: RiskLevel
    primary_reason: str
    reason_codes: List[str]
    evidence_summary: dict
    timestamp: datetime


class ReviewItemResponse(BaseModel):
    attempt_id: str
    session_id: str
    student_id: str
    student_name: str
    roll_number: str
    subject_title: str
    submitted_at: datetime
    method: str
    risk_level: str
    primary_reason: str
    reason_codes: List[str]
    geo_status: str
    geo_distance_meters: Optional[float] = None
    geo_accuracy_meters: Optional[float] = None
    face_status: str
    face_similarity_score: Optional[float] = None
    liveness_status: str


class ReviewActionRequest(BaseModel):
    action: str = Field(..., example="APPROVE", description="APPROVE or REJECT")
    reason: str = Field(..., min_length=3, description="Justification for decision")


class CorrectionRequest(BaseModel):
    student_id: str
    new_status: AttendanceStatus
    reason: str = Field(..., min_length=4, description="Mandatory reason for manual correction")


class CorrectionResponse(BaseModel):
    record_id: str
    student_id: str
    previous_status: str
    new_status: str
    teacher_name: str
    reason: str
    timestamp: datetime


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    roll_number: str
    session_id: str
    subject_title: str
    status: AttendanceStatus
    marked_via: str
    created_at: datetime


class StudentAttendanceSummary(BaseModel):
    total_sessions: int
    attended_sessions: int
    pending_reviews: int
    attendance_percentage: float
    shortage_alert: bool  # True if below 75%
    subject_wise: List[dict]
