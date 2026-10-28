import json
from apps.api.src.services.biometric_service import BiometricVerificationService
from apps.api.src.services.liveness_service import LivenessDetectionService


def test_cosine_similarity_identical_vectors():
    vec = [0.12, 0.45, 0.78, 0.33, 0.91]
    sim = BiometricVerificationService.compute_cosine_similarity(vec, vec)
    assert round(sim, 4) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    sim = BiometricVerificationService.compute_cosine_similarity(vec1, vec2)
    assert sim == 0.0


def test_face_match_success():
    # Enrolled template
    template = [0.2, 0.4, 0.6, 0.8] * 8  # 32-dim vector
    template_json = json.dumps(template)

    # Live capture with slight natural variation (high similarity ~0.99)
    live = [0.21, 0.39, 0.61, 0.79] * 8

    status, score, reason = BiometricVerificationService.evaluate_face_evidence(
        enrolled_reference=template_json,
        live_embedding=live,
        capture_quality=0.85,
        is_required=True
    )
    assert status == "MATCH"
    assert score is not None
    assert score >= 0.75


def test_face_mismatch():
    template = [0.5, 0.5, 0.5, 0.5] * 8
    template_json = json.dumps(template)

    # Completely different face vector
    live = [-0.5, -0.5, 0.5, 0.5] * 8

    status, score, reason = BiometricVerificationService.evaluate_face_evidence(
        enrolled_reference=template_json,
        live_embedding=live,
        capture_quality=0.80,
        is_required=True
    )
    assert status == "MISMATCH"
    assert score < 0.75


def test_face_not_enrolled():
    status, score, reason = BiometricVerificationService.evaluate_face_evidence(
        enrolled_reference=None,
        live_embedding=[0.1] * 32,
        is_required=True
    )
    assert status == "NOT_ENROLLED"


def test_face_low_capture_quality():
    template = json.dumps([0.5] * 32)
    status, score, reason = BiometricVerificationService.evaluate_face_evidence(
        enrolled_reference=template,
        live_embedding=[0.5] * 32,
        capture_quality=0.25,  # Very blurry / low light
        is_required=True
    )
    assert status == "LOW_QUALITY"


def test_liveness_detection_evaluation():
    # When not required
    status, score, _ = LivenessDetectionService.evaluate_liveness(None, is_required=False)
    assert status == "NOT_REQUIRED"

    # When presentation attack occurs
    status, score, _ = LivenessDetectionService.evaluate_liveness(False, is_required=True)
    # If not configured by default in settings, returns NOT_CONFIGURED, or FAILED if active
    assert status in ["FAILED", "NOT_CONFIGURED"]
