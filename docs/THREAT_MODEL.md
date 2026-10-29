# ATTENDX AI — Security Threat Model
**Methodology**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)

---

## 1. Threat Matrix & Technical Mitigations

| Threat ID | STRIDE Category | Attack Scenario | Impact | Mitigation Mechanism | Verification Test | Remaining Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TH-01** | Spoofing | Student takes a photo of projected QR code and shares via WhatsApp to absent classmate. | Absent student attempts proxy check-in. | Short-lived QR rotation (30s) signed with HMAC-SHA256. Fused with GPS geofence and live face match. | `test_dynamic_qr_token_cryptography` & `test_qr_token_expiration` | If photo is transmitted and submitted within <30s, GPS or face mismatch blocks the proxy. |
| **TH-02** | Spoofing | Attacker holds up a photo/video on a smartphone to the webcam during check-in. | Biometric identity spoofed. | Anti-spoofing challenge/liveness analysis. Cosine similarity threshold (0.75). | `test_face_mismatch` & `test_liveness_detection_evaluation` | High-quality 3D masks or synthetic deepfakes without specialized IR hardware. |
| **TH-03** | Tampering | Student uses fake GPS apps (Mock Location) to forge coordinates to classroom anchor. | Student bypasses spatial boundary. | Server checks reported GPS accuracy (`accuracy_meters <= 80m`). Re-verified via dynamic QR scanning which requires line-of-sight to classroom screen. | `test_geofence_poor_accuracy` & `test_geofence_outside_boundary` | OS-level kernel-rooted GPS spoofing cannot be completely prevented by web browsers without native MDM hardware checks. |
| **TH-04** | Tampering | Student modifies token payload in transit (alters expiry or session ID). | Extended token lifetime. | HMAC-SHA256 signature verification over all token segments. Any single bit modification invalidates signature. | `test_dynamic_qr_token_cryptography` | None. HMAC is cryptographically secure. |
| **TH-05** | Repudiation | Student claims they were marked absent unfairly or teacher altered records without reason. | Academic disputes. | Tamper-evident `audit_logs` and `attendance_corrections` table recording old status, new status, timestamp, and mandatory teacher explanation. | `test_full_attendance_verification_lifecycle` | Dependent on institutional database administrator integrity. |
| **TH-06** | Denial of Service | Attacker brute-forces temporary 6-digit session PIN. | Proxy check-in or service degradation. | Salted hash verification, 5-attempt lockout, and rate limiting (20 req/min). | `test_temporary_pin_generation_and_verification` | Classroom students must be mindful of session countdown. |
| **TH-07** | Elevation of Privilege | Student attempts to access teacher session creation or administrative user provisioning endpoints. | Unauthorized session or account creation. | Server-side role-based access control (`require_admin`, `require_teacher`) enforced on all API endpoints. | Automated API test suite and unit tests. | None. UI controls never substitute for server authorization. |

