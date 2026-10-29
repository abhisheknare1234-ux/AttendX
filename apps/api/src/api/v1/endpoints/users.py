import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.security import get_password_hash
from apps.api.src.core.audit import log_audit_event
from apps.api.src.core.dependencies import require_admin, get_current_user
from apps.api.src.models.user import User, UserRole, StudentProfile, TeacherProfile
from apps.api.src.schemas.auth import UserCreate, UserResponse
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["User Management"])


class BiometricEnrollRequest(BaseModel):
    reference_embedding: List[float]


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List provisioned users with their institutional profiles."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.offset(offset).limit(limit).all()

    results = []
    for u in users:
        results.append(
            UserResponse(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                is_active=u.is_active,
                roll_number=u.student_profile.roll_number if u.student_profile else None,
                prn=u.student_profile.prn if u.student_profile else None,
                employee_id=u.teacher_profile.employee_id if u.teacher_profile else None,
                department=u.student_profile.department if u.student_profile else (u.teacher_profile.department if u.teacher_profile else None),
                is_biometric_enrolled=u.student_profile.is_biometric_enrolled if u.student_profile else None
            )
        )
    return results


@router.post("", response_model=UserResponse)
def provision_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Provision a new user account with role-specific profile (Admin only)."""
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {payload.email} already exists."
        )

    user = User(
        email=payload.email.lower().strip(),
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True
    )
    db.add(user)
    db.flush()  # Allocate user.id

    if payload.role == UserRole.STUDENT:
        if not payload.roll_number or not payload.prn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Students require roll_number and prn."
            )
        student_profile = StudentProfile(
            user_id=user.id,
            roll_number=payload.roll_number,
            prn=payload.prn,
            department=payload.department or "Artificial Intelligence & Data Science",
            batch_year=2026,
            is_biometric_enrolled=False
        )
        db.add(student_profile)

    elif payload.role == UserRole.TEACHER:
        if not payload.employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teachers require employee_id."
            )
        teacher_profile = TeacherProfile(
            user_id=user.id,
            employee_id=payload.employee_id,
            department=payload.department or "Artificial Intelligence & Data Science",
            designation="Assistant Professor"
        )
        db.add(teacher_profile)

    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_PROVISIONED",
        actor_id=admin.id,
        target_type="user",
        target_id=user.id,
        details={"email": user.email, "role": user.role.value}
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        roll_number=user.student_profile.roll_number if user.student_profile else None,
        prn=user.student_profile.prn if user.student_profile else None,
        employee_id=user.teacher_profile.employee_id if user.teacher_profile else None,
        department=user.student_profile.department if user.student_profile else (user.teacher_profile.department if user.teacher_profile else None),
        is_biometric_enrolled=user.student_profile.is_biometric_enrolled if user.student_profile else None
    )


@router.post("/{student_id}/enroll-biometric")
def enroll_student_biometrics(
    student_id: str,
    payload: BiometricEnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll a student's facial reference vector.
    Can be performed by the student themselves or an administrator.
    """
    # Permission check: student can enroll own reference; admin can enroll any
    if current_user.role == UserRole.STUDENT and current_user.student_profile.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students may only enroll their own biometric credentials"
        )

    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    if len(payload.reference_embedding) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Biometric reference vector must contain at least 16 dimensions"
        )

    profile.biometric_reference = json.dumps(payload.reference_embedding)
    profile.is_biometric_enrolled = True
    db.commit()

    log_audit_event(
        db=db,
        action="BIOMETRIC_ENROLLED",
        actor_id=current_user.id,
        target_type="student_profile",
        target_id=profile.id,
        details={"dimension": len(payload.reference_embedding)}
    )

    return {"message": "Biometric reference template securely registered", "student_id": profile.id}

