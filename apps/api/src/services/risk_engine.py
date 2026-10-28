import json
from typing import Dict, Any, List, Tuple
from apps.api.src.models.attendance import DecisionOutcome, RiskLevel


class RiskEngine:
    """
    Explainable Multi-Factor Evidence Fusion & Risk Engine.
    
    Translates independent verification factors (Cryptographic QR, PIN, GPS Geofence,
    Face Biometrics, and Liveness Detection) into transparent, auditable outcomes:
    - ACCEPTED: Attendance confirmed and ledger updated.
    - REQUIRES_REVIEW: Check-in queued for authorized teacher review.
    - REJECTED: Attendance denied with explicit reason codes.
    """

    @classmethod
    def evaluate_checkin(
        cls,
        session_is_open: bool,
        is_enrolled: bool,
        already_marked: bool,
        qr_status: str,
        pin_status: str,
        geo_status: str,
        face_status: str,
        liveness_status: str,
        attempt_method: str = "QR_CODE"
    ) -> Tuple[DecisionOutcome, RiskLevel, str, List[str], str]:
        """
        Evaluate full multi-factor evidence matrix.
        Returns:
            - decision: DecisionOutcome (ACCEPTED, REQUIRES_REVIEW, REJECTED)
            - risk_level: RiskLevel (LOW, MEDIUM, HIGH, CRITICAL)
            - primary_reason_code: str
            - all_reason_codes: List[str]
            - action_taken: str (AUTO_ACCEPT, SEND_TO_REVIEW, AUTO_REJECT)
        """
        reason_codes: List[str] = []

        # Invariant 1: Session Status
        if not session_is_open:
            reason_codes.append("ERR_SESSION_CLOSED")
            return DecisionOutcome.REJECTED, RiskLevel.CRITICAL, "SESSION_CLOSED", reason_codes, "AUTO_REJECT"

        # Invariant 2: Enrollment verification
        if not is_enrolled:
            reason_codes.append("ERR_STUDENT_NOT_ENROLLED")
            return DecisionOutcome.REJECTED, RiskLevel.HIGH, "STUDENT_NOT_ENROLLED", reason_codes, "AUTO_REJECT"

        # Invariant 3: Duplicate attendance prevention
        if already_marked:
            reason_codes.append("ERR_DUPLICATE_ATTENDANCE_ATTEMPT")
            return DecisionOutcome.REJECTED, RiskLevel.HIGH, "ALREADY_CHECKED_IN", reason_codes, "AUTO_REJECT"

        # Factor 1: QR or PIN authenticity
        if attempt_method == "QR_CODE":
            if qr_status == "EXPIRED":
                reason_codes.append("ERR_QR_TOKEN_EXPIRED")
                return DecisionOutcome.REJECTED, RiskLevel.MEDIUM, "EXPIRED_QR_TOKEN", reason_codes, "AUTO_REJECT"
            elif qr_status != "PASSED":
                reason_codes.append(f"ERR_QR_{qr_status}")
                return DecisionOutcome.REJECTED, RiskLevel.CRITICAL, "INVALID_QR_TOKEN", reason_codes, "AUTO_REJECT"
            else:
                reason_codes.append("PASS_QR_VALIDATED")
        else:
            # PIN Fallback
            if pin_status == "LOCKED_OUT":
                reason_codes.append("ERR_PIN_MAX_ATTEMPTS_EXCEEDED")
                return DecisionOutcome.REJECTED, RiskLevel.CRITICAL, "PIN_LOCKED_OUT", reason_codes, "AUTO_REJECT"
            elif pin_status != "PASSED":
                reason_codes.append("ERR_PIN_INCORRECT")
                return DecisionOutcome.REJECTED, RiskLevel.HIGH, "INVALID_PIN", reason_codes, "AUTO_REJECT"
            else:
                reason_codes.append("PASS_PIN_VALIDATED")

        # Factor 2: Liveness Spoof Check
        if liveness_status == "FAILED":
            reason_codes.append("ERR_PRESENTATION_ATTACK_DETECTED")
            return DecisionOutcome.REJECTED, RiskLevel.CRITICAL, "LIVENESS_FAILED", reason_codes, "AUTO_REJECT"
        elif liveness_status == "PASSED":
            reason_codes.append("PASS_LIVENESS_CONFIRMED")
        else:
            reason_codes.append(f"INFO_LIVENESS_{liveness_status}")

        # Factor 3: Face Biometrics
        if face_status == "MISMATCH":
            reason_codes.append("ERR_BIOMETRIC_IDENTITY_MISMATCH")
            return DecisionOutcome.REJECTED, RiskLevel.CRITICAL, "FACE_MISMATCH", reason_codes, "AUTO_REJECT"
        elif face_status == "MATCH":
            reason_codes.append("PASS_FACE_MATCHED")
        elif face_status == "NOT_REQUIRED":
            reason_codes.append("INFO_FACE_NOT_REQUIRED")
        else:
            # Inconclusive biometric situations (NOT_ENROLLED, NO_FACE, LOW_QUALITY)
            reason_codes.append(f"WARN_FACE_{face_status}")

        # Factor 4: Geofence Spatial Evidence
        if geo_status == "INSIDE":
            reason_codes.append("PASS_GEOFENCE_INSIDE")
        else:
            reason_codes.append(f"WARN_GEOFENCE_{geo_status}")

        # Review Condition Evaluation
        # If any secondary physical factor is uncertain or missing, route to Teacher Review Queue
        review_triggers = []
        if geo_status in ["OUTSIDE", "PERMISSION_DENIED", "ACCURACY_POOR", "UNAVAILABLE"]:
            review_triggers.append(f"GEOFENCE_{geo_status}")

        if face_status in ["NOT_ENROLLED", "NO_FACE", "LOW_QUALITY", "UNAVAILABLE"]:
            review_triggers.append(f"BIOMETRIC_{face_status}")

        if review_triggers:
            primary_reason = f"REQUIRES_REVIEW_DUE_TO_{review_triggers[0]}"
            risk = RiskLevel.HIGH if "OUTSIDE" in geo_status else RiskLevel.MEDIUM
            return DecisionOutcome.REQUIRES_REVIEW, risk, primary_reason, reason_codes, "SEND_TO_REVIEW"

        # All required factors passed cleanly!
        return DecisionOutcome.ACCEPTED, RiskLevel.LOW, "ALL_EVIDENCE_VERIFIED", reason_codes, "AUTO_ACCEPT"
