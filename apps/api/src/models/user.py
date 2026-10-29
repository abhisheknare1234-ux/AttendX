import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from apps.api.src.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    roll_number = Column(String(50), unique=True, nullable=False, index=True)
    prn = Column(String(50), unique=True, nullable=False, index=True)  # Permanent Registration Number
    department = Column(String(100), nullable=False, default="Artificial Intelligence & Data Science")
    batch_year = Column(Integer, nullable=False, default=2026)
    is_biometric_enrolled = Column(Boolean, default=False, nullable=False)
    biometric_reference = Column(String(2048), nullable=True)  # JSON-serialized feature vector / reference embedding

    # Relationships
    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("ClassEnrollment", back_populates="student", cascade="all, delete-orphan")
    attendance_attempts = relationship("AttendanceAttempt", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False, default="Artificial Intelligence & Data Science")
    designation = Column(String(100), nullable=False, default="Assistant Professor")

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    assignments = relationship("TeacherAssignment", back_populates="teacher", cascade="all, delete-orphan")
    sessions = relationship("AttendanceSession", back_populates="teacher")
    corrections = relationship("AttendanceCorrection", back_populates="teacher")

