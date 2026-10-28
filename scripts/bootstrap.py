"""
AttendX AI — Institutional Demonstration Bootstrap Script
Target: ZEAL College of Engineering & Research, Pune

Initializes demonstration accounts and baseline academic fixtures:
1. Primary Administrator (admin@zeal.attendx.ai / ZealAdmin@2026Secure!)
2. Faculty Member (prof.sharma@zeal.edu.in / TeacherPassword123!)
3. Enrolled Students (aarav.patil@zeal.edu.in & neha.kulkarni@zeal.edu.in / StudentPassword123!)
4. Physical Classroom: Lab 304 (ZEAL Narhe Campus, Building A)
5. Academic Class & Subject: TE-AIDS-DivA -> AIDS-401 Deep Learning
"""

import os
import sys
import json

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.src.core.database import SessionLocal, Base, engine
from apps.api.src.core.security import get_password_hash
from apps.api.src.models.user import User, UserRole, StudentProfile, TeacherProfile
from apps.api.src.models.academic import Classroom, ClassEntity, Subject, ClassEnrollment, TeacherAssignment
from apps.api.src.core.audit import log_audit_event


def bootstrap_demonstration_data():
    print("[AttendX AI] Initializing institutional database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Administrator
        admin = db.query(User).filter(User.email == "admin@zeal.attendx.ai").first()
        if not admin:
            admin = User(
                email="admin@zeal.attendx.ai",
                password_hash=get_password_hash("ZealAdmin@2026Secure!"),
                role=UserRole.ADMIN,
                first_name="Dean",
                last_name="Academics",
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("  [+] Created Administrator: admin@zeal.attendx.ai")

        # 2. Teacher (Prof. Rohit Sharma)
        teacher_user = db.query(User).filter(User.email == "prof.sharma@zeal.edu.in").first()
        if not teacher_user:
            teacher_user = User(
                email="prof.sharma@zeal.edu.in",
                password_hash=get_password_hash("TeacherPassword123!"),
                role=UserRole.TEACHER,
                first_name="Rohit",
                last_name="Sharma",
                is_active=True
            )
            db.add(teacher_user)
            db.flush()
            teacher_profile = TeacherProfile(
                user_id=teacher_user.id,
                employee_id="EMP-AIDS-042",
                department="Artificial Intelligence & Data Science",
                designation="Assistant Professor"
            )
            db.add(teacher_profile)
            db.commit()
            print("  [+] Created Faculty: prof.sharma@zeal.edu.in (EMP-AIDS-042)")

        # 3. Student 1 (Aarav Patil)
        s1 = db.query(User).filter(User.email == "aarav.patil@zeal.edu.in").first()
        if not s1:
            s1 = User(
                email="aarav.patil@zeal.edu.in",
                password_hash=get_password_hash("StudentPassword123!"),
                role=UserRole.STUDENT,
                first_name="Aarav",
                last_name="Patil",
                is_active=True
            )
            db.add(s1)
            db.flush()
            # Reference vector (32-dimensions)
            ref_vector = [0.35, 0.45, 0.55, 0.65] * 8
            sp1 = StudentProfile(
                user_id=s1.id,
                roll_number="AIDS-2026-001",
                prn="PRN7192001",
                department="Artificial Intelligence & Data Science",
                batch_year=2026,
                is_biometric_enrolled=True,
                biometric_reference=json.dumps(ref_vector)
            )
            db.add(sp1)
            db.commit()
            print("  [+] Created Student: aarav.patil@zeal.edu.in (Roll: AIDS-2026-001)")

        # 4. Student 2 (Neha Kulkarni)
        s2 = db.query(User).filter(User.email == "neha.kulkarni@zeal.edu.in").first()
        if not s2:
            s2 = User(
                email="neha.kulkarni@zeal.edu.in",
                password_hash=get_password_hash("StudentPassword123!"),
                role=UserRole.STUDENT,
                first_name="Neha",
                last_name="Kulkarni",
                is_active=True
            )
            db.add(s2)
            db.flush()
            sp2 = StudentProfile(
                user_id=s2.id,
                roll_number="AIDS-2026-002",
                prn="PRN7192002",
                department="Artificial Intelligence & Data Science",
                batch_year=2026,
                is_biometric_enrolled=True,
                biometric_reference=json.dumps([0.35, 0.45, 0.55, 0.65] * 8)
            )
            db.add(sp2)
            db.commit()
            print("  [+] Created Student: neha.kulkarni@zeal.edu.in (Roll: AIDS-2026-002)")

        # 5. Classroom Geofence Anchor (ZEAL Narhe Campus, Building A - Lab 304)
        classroom = db.query(Classroom).filter(Classroom.name == "Lab 304 - High Performance AI Lab").first()
        if not classroom:
            classroom = Classroom(
                name="Lab 304 - High Performance AI Lab",
                building="Building A - ZCOER Narhe",
                latitude=18.4485,
                longitude=73.8245,
                radius_meters=75.0,
                is_active=True
            )
            db.add(classroom)
            db.commit()
            print("  [+] Registered Classroom: Lab 304 (Lat: 18.4485, Lon: 73.8245, Radius: 75m)")

        # 6. Academic Class
        cls_entity = db.query(ClassEntity).filter(ClassEntity.name == "TE-AIDS-DivA").first()
        if not cls_entity:
            cls_entity = ClassEntity(
                name="TE-AIDS-DivA",
                academic_year="2026-2027",
                semester=6
            )
            db.add(cls_entity)
            db.commit()
            print("  [+] Created Academic Class: TE-AIDS-DivA")

        # 7. Subject
        subject = db.query(Subject).filter(Subject.code == "AIDS-401").first()
        if not subject:
            subject = Subject(
                code="AIDS-401",
                title="Deep Learning & Neural Networks",
                class_id=cls_entity.id
            )
            db.add(subject)
            db.commit()
            print("  [+] Created Academic Subject: AIDS-401 Deep Learning & Neural Networks")

        # 8. Enrollments
        sp1 = db.query(StudentProfile).filter(StudentProfile.roll_number == "AIDS-2026-001").first()
        sp2 = db.query(StudentProfile).filter(StudentProfile.roll_number == "AIDS-2026-002").first()
        
        if sp1:
            enr1 = db.query(ClassEnrollment).filter(
                ClassEnrollment.class_id == cls_entity.id,
                ClassEnrollment.student_id == sp1.id
            ).first()
            if not enr1:
                db.add(ClassEnrollment(class_id=cls_entity.id, student_id=sp1.id))

        if sp2:
            enr2 = db.query(ClassEnrollment).filter(
                ClassEnrollment.class_id == cls_entity.id,
                ClassEnrollment.student_id == sp2.id
            ).first()
            if not enr2:
                db.add(ClassEnrollment(class_id=cls_entity.id, student_id=sp2.id))

        db.commit()
        print("  [+] Enrolled Students into TE-AIDS-DivA")

        # 9. Teacher Assignment
        tp = db.query(TeacherProfile).filter(TeacherProfile.employee_id == "EMP-AIDS-042").first()
        if tp:
            assign = db.query(TeacherAssignment).filter(
                TeacherAssignment.subject_id == subject.id,
                TeacherAssignment.teacher_id == tp.id
            ).first()
            if not assign:
                db.add(TeacherAssignment(subject_id=subject.id, teacher_id=tp.id))
                db.commit()
                print("  [+] Assigned Prof. Rohit Sharma to AIDS-401")

        print("\n[AttendX AI] Demonstration accounts successfully initialized!")
        print("=================================================================")
        print("Administrator : admin@zeal.attendx.ai       / ZealAdmin@2026Secure!")
        print("Faculty       : prof.sharma@zeal.edu.in     / TeacherPassword123!")
        print("Student 1     : aarav.patil@zeal.edu.in     / StudentPassword123!")
        print("Student 2     : neha.kulkarni@zeal.edu.in   / StudentPassword123!")
        print("=================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_demonstration_data()
