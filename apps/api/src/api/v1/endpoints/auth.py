from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.security import verify_password, get_password_hash, create_access_token
from apps.api.src.core.audit import log_audit_event
from apps.api.src.core.dependencies import get_current_user
from apps.api.src.models.user import User, UserRole, StudentProfile, TeacherProfile
from apps.api.src.schemas.auth import LoginRequest, TokenResponse, UserResponse, AdminBootstrapRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and Argon2id hashed password."""
    client_ip = request.client.host if request.client else None
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    
    if not user or not verify_password(payload.password, user.password_hash):
        log_audit_event(
            db=db,
            action="AUTH_LOGIN_FAILED",
            target_type="user",
            target_id=payload.email,
            details={"reason": "Invalid credentials"},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect institutional email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institutional account has been suspended. Contact administration."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "email": user.email}
    )

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="attendx_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        max_age=8 * 3600
    )

    log_audit_event(
        db=db,
        action="AUTH_LOGIN_SUCCESS",
        actor_id=user.id,
        target_type="user",
        target_id=user.id,
        ip_address=client_ip
    )

    # Construct user response
    user_res = UserResponse(
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

    return TokenResponse(access_token=access_token, user=user_res)


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear session cookie and register logout audit event."""
    response.delete_cookie(key="attendx_token")
    log_audit_event(
        db=db,
        action="AUTH_LOGOUT",
        actor_id=current_user.id,
        target_type="user",
        target_id=current_user.id
    )
    return {"message": "Successfully logged out from AttendX AI"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile and active roles."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        roll_number=current_user.student_profile.roll_number if current_user.student_profile else None,
        prn=current_user.student_profile.prn if current_user.student_profile else None,
        employee_id=current_user.teacher_profile.employee_id if current_user.teacher_profile else None,
        department=current_user.student_profile.department if current_user.student_profile else (current_user.teacher_profile.department if current_user.teacher_profile else None),
        is_biometric_enrolled=current_user.student_profile.is_biometric_enrolled if current_user.student_profile else None
    )


@router.post("/bootstrap-admin", response_model=UserResponse)
def bootstrap_admin(payload: AdminBootstrapRequest, db: Session = Depends(get_db)):
    """
    Secure Initial Administrator Bootstrap.
    Rejects repeated initialization if an administrator account already exists.
    """
    existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator already initialized. Unsafe repeated initialization rejected."
        )

    admin_user = User(
        email=payload.email.lower().strip(),
        password_hash=get_password_hash(payload.password),
        role=UserRole.ADMIN,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    log_audit_event(
        db=db,
        action="ADMIN_BOOTSTRAP_INITIALIZED",
        actor_id=admin_user.id,
        target_type="user",
        target_id=admin_user.id,
        details={"email": admin_user.email}
    )

    return UserResponse(
        id=admin_user.id,
        email=admin_user.email,
        first_name=admin_user.first_name,
        last_name=admin_user.last_name,
        role=admin_user.role,
        is_active=admin_user.is_active
    )

