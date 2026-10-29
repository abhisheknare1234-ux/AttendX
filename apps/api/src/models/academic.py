import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from apps.api.src.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)  # e.g. "Room 304 - Central AI Lab"
    building = Column(String(100), nullable=False, default="Building A - ZCOER Narhe")
    latitude = Column(Float, nullable=False, default=18.4485)
    longitude = Column(Float, nullable=False, default=73.8245)
    radius_meters = Column(Float, nullable=False, default=100.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    sessions = relationship("AttendanceSession", back_populates="classroom")


class ClassEntity(Base):
    __tablename__ = "classes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)  # e.g. "TE-AIDS-DivA"
    academic_year = Column(String(20), nullable=False, default="2026-2027")
    semester = Column(Integer, nullable=False, default=6)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    subjects = relationship("Subject", back_populates="class_entity", cascade="all, delete-orphan")
    enrollments = relationship("ClassEnrollment", back_populates="class_entity", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(20), nullable=False, index=True)  # e.g. "AIDS-401"
    title = Column(String(150), nullable=False)  # e.g. "Deep Learning & Neural Networks"
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    class_entity = relationship("ClassEntity", back_populates="subjects")
    assignments = relationship("TeacherAssignment", back_populates="subject", cascade="all, delete-orphan")
    sessions = relationship("AttendanceSession", back_populates="subject")

    __table_args__ = (
        UniqueConstraint("code", "class_id", name="uq_subject_code_class"),
    )


class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    class_entity = relationship("ClassEntity", back_populates="enrollments")
    student = relationship("StudentProfile", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student_enrollment"),
    )


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="assignments")
    teacher = relationship("TeacherProfile", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("subject_id", "teacher_id", name="uq_subject_teacher_assignment"),
    )

