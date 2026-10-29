import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import get_current_user, require_teacher, require_admin, require_any_authenticated
from apps.api.src.models.user import User, UserRole, StudentProfile
from apps.api.src.models.academic import Subject, ClassEntity, ClassEnrollment
from apps.api.src.models.attendance import (
    AttendanceRecord,
    AttendanceSession,
    AttendanceAttempt,
    AttendanceStatus,
    SessionStatus,
)
from apps.api.src.schemas.attendance import StudentAttendanceSummary, AttendanceRecordResponse

router = APIRouter(prefix="/reports", tags=["Attendance Reports & Analytics"])


def sanitize_csv_field(val: Any) -> str:
    """
    Prevents CSV Spreadsheet Formula Injection (CWE-1236).
    If a cell value starts with '=', '+', '-', '@', tab, or carriage return,
    prefix with single quote to force spreadsheet programs to treat as literal text.
    """
    text = str(val or "")
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(require_any_authenticated)):
    """
    Real-time database-backed dashboard metrics.
    Zero hardcoded values.
    """
    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()
    total_teachers = db.query(User).filter(User.role == UserRole.TEACHER).count()
    active_sessions = db.query(AttendanceSession).filter(AttendanceSession.status == SessionStatus.OPEN).count()
    total_sessions = db.query(AttendanceSession).count()

    total_records = db.query(AttendanceRecord).count()
    total_present = db.query(AttendanceRecord).filter(AttendanceRecord.status == AttendanceStatus.PRESENT).count()
    total_pending_review = db.query(AttendanceRecord).filter(AttendanceRecord.status == AttendanceStatus.PENDING_REVIEW).count()

    avg_attendance_pct = round((total_present / total_records * 100.0), 1) if total_records > 0 else 0.0

    teacher_assigned_classes = 0
    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        from apps.api.src.models.academic import TeacherAssignment
        teacher_assigned_classes = db.query(TeacherAssignment).filter(
            TeacherAssignment.teacher_id == current_user.teacher_profile.id
        ).count()

    return {
        "user_role": current_user.role.value,
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "active_sessions": active_sessions,
        "total_sessions": total_sessions,
        "total_attendance_records": total_records,
        "total_present": total_present,
        "total_pending_review": total_pending_review,
        "average_attendance_percentage": avg_attendance_pct,
        "teacher_assigned_classes": teacher_assigned_classes
    }


@router.get("/student/{student_id}", response_model=StudentAttendanceSummary)
def get_student_attendance_summary(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve personalized attendance analytics for a student.
    Authorization: A student can only view their own records; teachers and admins can view any.
    """
    if current_user.role == UserRole.STUDENT and current_user.student_profile:
        if current_user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="Unauthorized to view other students' records")

    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Get all enrollments for student
    enrollments = db.query(ClassEnrollment).filter(ClassEnrollment.student_id == student_id).all()
    class_ids = [e.class_id for e in enrollments]

    # Subjects for these classes
    subjects = db.query(Subject).filter(Subject.class_id.in_(class_ids)).all() if class_ids else []

    subject_wise = []
    overall_total_sessions = 0
    overall_attended_sessions = 0
    overall_pending_reviews = 0

    for subj in subjects:
        # All finalized or open sessions for this subject
        sessions = db.query(AttendanceSession).filter(AttendanceSession.subject_id == subj.id).all()
        sess_ids = [s.id for s in sessions]
        sess_count = len(sess_ids)

        if sess_count > 0:
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.session_id.in_(sess_ids),
                AttendanceRecord.student_id == student_id
            ).all()

            present_cnt = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
            pending_cnt = sum(1 for r in records if r.status == AttendanceStatus.PENDING_REVIEW)
            pct = round((present_cnt / sess_count) * 100.0, 1)

            overall_total_sessions += sess_count
            overall_attended_sessions += present_cnt
            overall_pending_reviews += pending_cnt

            subject_wise.append({
                "subject_id": subj.id,
                "subject_code": subj.code,
                "subject_title": subj.title,
                "total_sessions": sess_count,
                "attended": present_cnt,
                "pending_review": pending_cnt,
                "percentage": pct,
                "is_shortage": pct < 75.0
            })
        else:
            subject_wise.append({
                "subject_id": subj.id,
                "subject_code": subj.code,
                "subject_title": subj.title,
                "total_sessions": 0,
                "attended": 0,
                "pending_review": 0,
                "percentage": 100.0,
                "is_shortage": False
            })

    overall_percentage = (
        round((overall_attended_sessions / overall_total_sessions) * 100.0, 1)
        if overall_total_sessions > 0
        else 100.0
    )

    return StudentAttendanceSummary(
        total_sessions=overall_total_sessions,
        attended_sessions=overall_attended_sessions,
        pending_reviews=overall_pending_reviews,
        attendance_percentage=overall_percentage,
        shortage_alert=overall_percentage < 75.0,
        subject_wise=subject_wise
    )


@router.get("/session/{session_id}", response_model=List[AttendanceRecordResponse])
def get_session_attendance_roster(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Retrieve full attendance roster for a given session."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()
    results = []
    for r in records:
        student = r.student
        user = student.user if student else None
        student_name = f"{user.first_name} {user.last_name}" if user else "Student"
        results.append(
            AttendanceRecordResponse(
                id=r.id,
                student_id=r.student_id,
                student_name=student_name,
                roll_number=student.roll_number if student else "N/A",
                session_id=r.session_id,
                subject_title=session.subject.title if session.subject else "N/A",
                status=r.status,
                marked_via=r.marked_via,
                created_at=r.created_at
            )
        )
    return results


@router.get("/session/{session_id}/export-csv")
def export_session_csv(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    Secure CSV export with active spreadsheet formula-injection defenses.
    """
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Roll Number",
        "Student Name",
        "PRN",
        "Subject Code",
        "Subject Title",
        "Attendance Status",
        "Verification Method",
        "Marked Timestamp UTC"
    ])

    for r in records:
        student = r.student
        user = student.user if student else None
        student_name = f"{user.first_name} {user.last_name}" if user else "N/A"
        writer.writerow([
            sanitize_csv_field(student.roll_number if student else "N/A"),
            sanitize_csv_field(student_name),
            sanitize_csv_field(student.prn if student else "N/A"),
            sanitize_csv_field(session.subject.code if session.subject else "N/A"),
            sanitize_csv_field(session.subject.title if session.subject else "N/A"),
            sanitize_csv_field(r.status.value),
            sanitize_csv_field(r.marked_via),
            sanitize_csv_field(r.created_at.isoformat())
        ])

    csv_data = output.getvalue()
    filename = f"attendx_{session.subject.code if session.subject else 'session'}_{session_id[:8]}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

