# ATTENDX AI — Automated Test Plan & Results Register
**Test Engine**: Pytest 8.x / 9.x  
**Coverage**: Unit tests, Service tests, Security tests, and API Integration tests

---

## 1. Test Suite Summary

Total Executed Tests: **27 passed in 1.96s** (100% pass rate).

### 1.1 Cryptography & Security Tests (`apps/api/tests/test_security.py`)
- `test_argon2id_password_hashing`: Validates password hashing format, salt generation, and verification.
- `test_jwt_access_token`: Validates token claims, subject extraction, and expiry decoding.
- `test_dynamic_qr_token_cryptography`: Proves valid HMAC signature verification, session mismatch detection, and tamper detection.
- `test_qr_token_expiration`: Proves rejection of tokens outside the valid rotation window.
- `test_temporary_pin_generation_and_verification`: Validates 6-digit CSPRNG PIN creation and salted hash verification.

### 1.2 Geofence Spatial Tests (`apps/api/tests/test_geofence.py`)
- `test_haversine_same_point`: Identity distance check ($d = 0.0\text{ m}$).
- `test_haversine_known_distance`: Ground-truth distance verification between ZEAL Narhe Campus and Swargate Pune (~6.9 km).
- `test_geofence_inside_boundary`: Verified inside classroom radius with indoor structure tolerance.
- `test_geofence_outside_boundary`: Verified rejection (>1 km away).
- `test_geofence_poor_accuracy`: Verified handling of inaccurate GPS (>80 m).
- `test_geofence_permission_denied`: Verified handling of denied browser geolocation.

### 1.3 Biometric Verification Tests (`apps/api/tests/test_biometrics.py`)
- `test_cosine_similarity_identical_vectors`: Vectors return similarity = 1.0.
- `test_cosine_similarity_orthogonal_vectors`: Vectors return similarity = 0.0.
- `test_face_match_success`: Matching face embedding vectors yield similarity $\ge 0.75$.
- `test_face_mismatch`: Non-matching face embedding vectors yield similarity $< 0.75$.
- `test_face_not_enrolled`: Catches students without enrolled templates.
- `test_face_low_capture_quality`: Rejects low-quality captures ($< 0.40$).
- `test_liveness_detection_evaluation`: Distinguishes passive anti-spoof checks.

### 1.4 Risk Engine Decision Tests (`apps/api/tests/test_risk_engine.py`)
- `test_risk_engine_all_factors_passed`: Outcomes `ACCEPTED`, Risk `LOW`, Action `AUTO_ACCEPT`.
- `test_risk_engine_closed_session`: Invariant violation returns `REJECTED`, Reason `SESSION_CLOSED`.
- `test_risk_engine_duplicate_checkin`: Duplicate check-in returns `REJECTED`, Reason `ALREADY_CHECKED_IN`.
- `test_risk_engine_expired_qr`: Expired token returns `REJECTED`, Reason `EXPIRED_QR_TOKEN`.
- `test_risk_engine_face_mismatch`: Biometric mismatch returns `REJECTED`, Risk `CRITICAL`.
- `test_risk_engine_requires_review_due_to_gps_drift`: Inconclusive GPS routes to `REQUIRES_REVIEW` and Teacher Review Queue.

### 1.5 Full Lifecycle API Integration Tests (`apps/api/tests/test_attendance_integration.py`)
- Covers complete 18-step workflow from administrator bootstrap, faculty and student provisioning, classroom geofencing, session opening, live dynamic QR rotation, genuine student check-in, duplicate attempt prevention, GPS drift review queue triage, teacher approval, controlled attendance correction, and formula-injection-safe CSV export.
