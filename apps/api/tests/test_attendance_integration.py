import json
import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app
from apps.api.src.models.user import StudentProfile


def test_full_attendance_verification_lifecycle(client, db_session):
    # 1. Bootstrap Admin
    res = client.post("/api/v1/auth/bootstrap-admin", json={
        "email": "admin@zeal.edu.in",
        "password": "AdminPassword123!",
        "first_name": "Dean",
        "last_name": "Academics"
    })
    assert res.status_code == 200

    # 2. Login as Admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@zeal.edu.in",
        "password": "AdminPassword123!"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin Provisions Teacher
    teach_res = client.post("/api/v1/users", headers=admin_headers, json={
        "email": "prof.sharma@zeal.edu.in",
        "password": "TeacherPassword123!",
        "first_name": "Rohit",
        "last_name": "Sharma",
        "role": "TEACHER",
        "employee_id": "EMP-AIDS-042",
        "department": "Artificial Intelligence & Data Science"
    })
    assert teach_res.status_code == 200

    # 4. Admin Provisions Student 1 & Student 2
    stud1_res = client.post("/api/v1/users", headers=admin_headers, json={
        "email": "aarav.patil@zeal.edu.in",
        "password": "StudentPassword123!",
        "first_name": "Aarav",
        "last_name": "Patil",
        "role": "STUDENT",
        "roll_number": "AIDS-2026-001",
        "prn": "PRN7192001",
        "department": "Artificial Intelligence & Data Science"
    })
    assert stud1_res.status_code == 200
    stud1_id = stud1_res.json()["id"]

    stud2_res = client.post("/api/v1/users", headers=admin_headers, json={
        "email": "neha.kulkarni@zeal.edu.in",
        "password": "StudentPassword123!",
        "first_name": "Neha",
        "last_name": "Kulkarni",
        "role": "STUDENT",
        "roll_number": "AIDS-2026-002",
        "prn": "PRN7192002",
        "department": "Artificial Intelligence & Data Science"
    })
    assert stud2_res.status_code == 200
    stud2_id = stud2_res.json()["id"]

    # 5. Admin Creates Classroom (ZEAL Narhe Lab 304)
    room_res = client.post("/api/v1/academic/classrooms", headers=admin_headers, json={
        "name": "Lab 304 - High Performance AI Lab",
        "building": "Building A - ZCOER",
        "latitude": 18.4485,
        "longitude": 73.8245,
        "radius_meters": 75.0,
        "is_active": True
    })
    assert room_res.status_code == 200
    room_id = room_res.json()["id"]

    # 6. Admin Creates Class, Subject & Enrolls Students
    cls_res = client.post("/api/v1/academic/classes", headers=admin_headers, json={
        "name": "TE-AIDS-DivA",
        "academic_year": "2026-2027",
        "semester": 6
    })
    assert cls_res.status_code == 200
    class_id = cls_res.json()["id"]

    subj_res = client.post("/api/v1/academic/subjects", headers=admin_headers, json={
        "code": "AIDS-401",
        "title": "Deep Learning & Neural Networks",
        "class_id": class_id
    })
    assert subj_res.status_code == 200
    subj_id = subj_res.json()["id"]

    # Enroll Students
    # Get student profile IDs
    stud1_user = client.get("/api/v1/users", headers=admin_headers).json()
    p1_id = [u["id"] for u in stud1_user if u["email"] == "aarav.patil@zeal.edu.in"][0]
    p2_id = [u["id"] for u in stud1_user if u["email"] == "neha.kulkarni@zeal.edu.in"][0]

    # Find student profile ID from database/user
    # Enroll both in class
    sp1 = db_session.query(StudentProfile).filter(StudentProfile.user_id == p1_id).first()
    sp2 = db_session.query(StudentProfile).filter(StudentProfile.user_id == p2_id).first()
    sp1_id = sp1.id
    sp2_id = sp2.id

    client.post("/api/v1/academic/enrollments", headers=admin_headers, json={"class_id": class_id, "student_id": sp1_id})
    client.post("/api/v1/academic/enrollments", headers=admin_headers, json={"class_id": class_id, "student_id": sp2_id})

    # 7. Student 1 Enrolls Face Reference Embedding
    stud1_login = client.post("/api/v1/auth/login", json={"email": "aarav.patil@zeal.edu.in", "password": "StudentPassword123!"})
    stud1_token = stud1_login.json()["access_token"]
    stud1_headers = {"Authorization": f"Bearer {stud1_token}"}

    sample_embedding = [0.35, 0.45, 0.55, 0.65] * 8  # 32 dimensions
    enroll_res = client.post(f"/api/v1/users/{sp1_id}/enroll-biometric", headers=stud1_headers, json={
        "reference_embedding": sample_embedding
    })
    assert enroll_res.status_code == 200

    # 8. Teacher Logs in and Creates Session
    t_login = client.post("/api/v1/auth/login", json={"email": "prof.sharma@zeal.edu.in", "password": "TeacherPassword123!"})
    t_token = t_login.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}

    sess_res = client.post("/api/v1/sessions", headers=t_headers, json={
        "subject_id": subj_id,
        "classroom_id": room_id,
        "checkin_window_minutes": 10,
        "qr_refresh_seconds": 30,
        "require_face": True,
        "require_geofence": True,
        "require_liveness": False
    })
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    # 9. Teacher Opens Session
    open_res = client.post(f"/api/v1/sessions/{session_id}/open", headers=t_headers)
    assert open_res.status_code == 200
    assert open_res.json()["status"] == "OPEN"

    # 10. Teacher Fetches Live Dynamic QR Token
    qr_res = client.get(f"/api/v1/sessions/{session_id}/qr-token", headers=t_headers)
    assert qr_res.status_code == 200
    qr_token_str = qr_res.json()["token_str"]

    # 11. Student 1 Submits Genuine Attendance (Matches Face + Inside Geofence + Valid QR)
    live_face_vector = [0.34, 0.46, 0.54, 0.66] * 8  # High similarity (~0.99)
    checkin_res = client.post("/api/v1/checkin", headers=stud1_headers, json={
        "session_id": session_id,
        "method": "QR_CODE",
        "qr_token": qr_token_str,
        "latitude": 18.44855,   # ~5 meters from classroom center
        "longitude": 73.82452,
        "accuracy_meters": 12.0,
        "face_embedding": live_face_vector,
        "face_capture_quality": 0.88
    })
    assert checkin_res.status_code == 200
    checkin_data = checkin_res.json()
    assert checkin_data["decision"] == "ACCEPTED"
    assert checkin_data["status"] == "PRESENT"
    assert checkin_data["risk_level"] == "LOW"

    # 12. Student 1 Attempts Duplicate Check-in -> REJECTED
    dup_res = client.post("/api/v1/checkin", headers=stud1_headers, json={
        "session_id": session_id,
        "method": "QR_CODE",
        "qr_token": qr_token_str,
        "latitude": 18.44855,
        "longitude": 73.82452,
        "accuracy_meters": 12.0,
        "face_embedding": live_face_vector,
        "face_capture_quality": 0.88
    })
    assert dup_res.status_code == 200
    assert dup_res.json()["decision"] == "REJECTED"
    assert dup_res.json()["primary_reason"] == "ALREADY_CHECKED_IN"

    # 13. Student 2 Checks In with GPS Out of Bounds -> Flagged as REQUIRES_REVIEW
    stud2_login = client.post("/api/v1/auth/login", json={"email": "neha.kulkarni@zeal.edu.in", "password": "StudentPassword123!"})
    stud2_headers = {"Authorization": f"Bearer {stud2_login.json()['access_token']}"}

    # Student 2 enrolls biometric first
    client.post(f"/api/v1/users/{sp2_id}/enroll-biometric", headers=stud2_headers, json={
        "reference_embedding": sample_embedding
    })

    stud2_checkin = client.post("/api/v1/checkin", headers=stud2_headers, json={
        "session_id": session_id,
        "method": "QR_CODE",
        "qr_token": qr_token_str,
        "latitude": 18.47000,   # ~2.5 km away from college campus
        "longitude": 73.84000,
        "accuracy_meters": 15.0,
        "face_embedding": sample_embedding,
        "face_capture_quality": 0.85
    })
    assert stud2_checkin.status_code == 200
    stud2_data = stud2_checkin.json()
    assert stud2_data["decision"] == "REQUIRES_REVIEW"
    assert stud2_data["status"] == "PENDING_REVIEW"
    attempt2_id = stud2_data["attempt_id"]

    # 14. Teacher Checks Review Queue
    queue_res = client.get("/api/v1/review/queue", headers=t_headers)
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert len(queue) == 1
    assert queue[0]["student_name"] == "Neha Kulkarni"

    # 15. Teacher Approves Student 2 Check-in
    action_res = client.post(f"/api/v1/review/{attempt2_id}/action", headers=t_headers, json={
        "action": "APPROVE",
        "reason": "Student verified sitting in Lab 304 corner with poor GPS indoor reception"
    })
    assert action_res.status_code == 200
    assert action_res.json()["final_status"] == "PRESENT"

    # 16. Teacher Performs Controlled Attendance Correction
    corr_res = client.post(f"/api/v1/corrections/sessions/{session_id}", headers=t_headers, json={
        "student_id": sp1_id,
        "new_status": "EXCUSED",
        "reason": "Student represented college at Smart India Hackathon zonal round"
    })
    assert corr_res.status_code == 200
    assert corr_res.json()["new_status"] == "EXCUSED"

    # 17. CSV Export Verification (Formula Injection Defense)
    csv_res = client.get(f"/api/v1/reports/session/{session_id}/export-csv", headers=t_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text
    assert "Roll Number,Student Name" in csv_text
    assert "Aarav Patil" in csv_text
    assert "Neha Kulkarni" in csv_text

    # 18. Real-time Dashboard Stats
    stats_res = client.get("/api/v1/reports/dashboard-stats", headers=t_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_users"] >= 3
    assert stats["active_sessions"] == 1

