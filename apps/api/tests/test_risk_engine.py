from apps.api.src.services.risk_engine import RiskEngine
from apps.api.src.models.attendance import DecisionOutcome, RiskLevel


def test_risk_engine_all_factors_passed():
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=True,
        is_enrolled=True,
        already_marked=False,
        qr_status="PASSED",
        pin_status="NOT_USED",
        geo_status="INSIDE",
        face_status="MATCH",
        liveness_status="PASSED",
        attempt_method="QR_CODE"
    )
    assert decision == DecisionOutcome.ACCEPTED
    assert risk == RiskLevel.LOW
    assert action == "AUTO_ACCEPT"
    assert "PASS_QR_VALIDATED" in codes
    assert "PASS_FACE_MATCHED" in codes
    assert "PASS_GEOFENCE_INSIDE" in codes


def test_risk_engine_closed_session():
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=False,
        is_enrolled=True,
        already_marked=False,
        qr_status="PASSED",
        pin_status="NOT_USED",
        geo_status="INSIDE",
        face_status="MATCH",
        liveness_status="PASSED"
    )
    assert decision == DecisionOutcome.REJECTED
    assert primary_reason == "SESSION_CLOSED"
    assert action == "AUTO_REJECT"


def test_risk_engine_duplicate_checkin():
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=True,
        is_enrolled=True,
        already_marked=True,
        qr_status="PASSED",
        pin_status="NOT_USED",
        geo_status="INSIDE",
        face_status="MATCH",
        liveness_status="PASSED"
    )
    assert decision == DecisionOutcome.REJECTED
    assert primary_reason == "ALREADY_CHECKED_IN"


def test_risk_engine_expired_qr():
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=True,
        is_enrolled=True,
        already_marked=False,
        qr_status="EXPIRED",
        pin_status="NOT_USED",
        geo_status="INSIDE",
        face_status="MATCH",
        liveness_status="PASSED"
    )
    assert decision == DecisionOutcome.REJECTED
    assert primary_reason == "EXPIRED_QR_TOKEN"


def test_risk_engine_face_mismatch():
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=True,
        is_enrolled=True,
        already_marked=False,
        qr_status="PASSED",
        pin_status="NOT_USED",
        geo_status="INSIDE",
        face_status="MISMATCH",
        liveness_status="PASSED"
    )
    assert decision == DecisionOutcome.REJECTED
    assert primary_reason == "FACE_MISMATCH"
    assert risk == RiskLevel.CRITICAL


def test_risk_engine_requires_review_due_to_gps_drift():
    # Valid token, enrolled student, but indoor GPS reported slightly outside or poor accuracy
    decision, risk, primary_reason, codes, action = RiskEngine.evaluate_checkin(
        session_is_open=True,
        is_enrolled=True,
        already_marked=False,
        qr_status="PASSED",
        pin_status="NOT_USED",
        geo_status="OUTSIDE",
        face_status="MATCH",
        liveness_status="PASSED"
    )
    assert decision == DecisionOutcome.REQUIRES_REVIEW
    assert "REQUIRES_REVIEW" in primary_reason
    assert action == "SEND_TO_REVIEW"
