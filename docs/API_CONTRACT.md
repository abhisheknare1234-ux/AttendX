# ATTENDX AI — API Specifications & Contracts
**Base Path**: `/api/v1`  
**Authentication**: HTTP-Only Cookie (`attendx_token`) or Header (`Authorization: Bearer <JWT>`)

---

## 1. System & Authentication Endpoints

### `GET /api/v1/health`
Checks sub-service availability (PostgreSQL/SQLite, QR Crypto Validator, Geofence Engine, Biometrics, Liveness).
- **Response 200**:
```json
{
  "status": "healthy",
  "app_name": "AttendX AI",
  "version": "1.0.0",
  "institution": "ZEAL College of Engineering & Research, Pune",
  "services": {
    "database": { "status": "healthy", "engine": "PostgreSQL/SQLite" },
    "qr_crypto_validator": { "status": "operational", "algorithm": "HMAC-SHA256" },
    "geofence_engine": { "status": "operational", "formula": "WGS-84 Haversine Spherical" },
    "biometric_verifier": { "status": "operational", "threshold": 0.75 }
  }
}
```

### `POST /api/v1/auth/login`
- **Request**:
```json
{
  "email": "aarav.patil@zeal.edu.in",
  "password": "StudentPassword123!"
}
```
- **Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-...",
    "email": "aarav.patil@zeal.edu.in",
    "role": "STUDENT",
    "roll_number": "AIDS-2026-001"
  }
}
```

### `POST /api/v1/auth/logout`
Clears HTTP-only cookie and writes `AUTH_LOGOUT` audit log.

### `POST /api/v1/auth/bootstrap-admin`
Provisions the initial institutional administrator. Rejects repeated calls once an administrator exists.

---

## 2. Attendance Sessions & Verification Streams

### `POST /api/v1/sessions`
- **Role**: `TEACHER` or `ADMIN`
- **Request**:
```json
{
  "subject_id": "uuid-...",
  "classroom_id": "uuid-...",
  "checkin_window_minutes": 5,
  "qr_refresh_seconds": 30,
  "require_face": true,
  "require_geofence": true,
  "require_liveness": false
}
```

### `POST /api/v1/sessions/{id}/open`
Opens session, transitions state from `DRAFT` to `OPEN`, starts window timer.

### `GET /api/v1/sessions/{id}/qr-token`
- **Role**: `TEACHER`
- Returns dynamic HMAC-signed token refreshed every 30s:
```json
{
  "session_id": "uuid-...",
  "token_str": "ATX1.<session_id>.<nonce>.<exp>.<hmac_signature>",
  "nonce": "a4f89d3...",
  "expires_at": "2026-10-28T18:30:00Z",
  "valid_seconds": 30
}
```

### `POST /api/v1/checkin`
- **Role**: `STUDENT`
- **Request**:
```json
{
  "session_id": "uuid-...",
  "method": "QR_CODE",
  "qr_token": "ATX1.<session_id>.<nonce>.<exp>.<hmac>",
  "latitude": 18.44855,
  "longitude": 73.82452,
  "accuracy_meters": 12.0,
  "face_embedding": [0.34, 0.46, 0.54, 0.66, ...],
  "face_capture_quality": 0.88,
  "liveness_confirmed": true
}
```
- **Response 200**:
```json
{
  "attempt_id": "uuid-...",
  "session_id": "uuid-...",
  "decision": "ACCEPTED",
  "status": "PRESENT",
  "risk_level": "LOW",
  "primary_reason": "ALL_EVIDENCE_VERIFIED",
  "reason_codes": ["PASS_QR_VALIDATED", "PASS_GEOFENCE_INSIDE", "PASS_FACE_MATCHED"]
}
```

---

## 3. Teacher Review, Corrections & Reports

### `GET /api/v1/review/queue`
Returns check-ins flagged as `REQUIRES_REVIEW` (e.g. GPS multipath drift or poor lighting).

### `POST /api/v1/review/{attempt_id}/action`
- **Request**:
```json
{
  "action": "APPROVE",
  "reason": "Student confirmed physically in classroom corner with weak GPS reception"
}
```

### `POST /api/v1/corrections/sessions/{session_id}`
- **Request**:
```json
{
  "student_id": "uuid-...",
  "new_status": "EXCUSED",
  "reason": "Represented college at Smart India Hackathon"
}
```

### `GET /api/v1/reports/session/{id}/export-csv`
Exports CSV roster with spreadsheet formula injection sanitization.
