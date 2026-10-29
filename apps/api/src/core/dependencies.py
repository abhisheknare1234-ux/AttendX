from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.security import decode_access_token
from apps.api.src.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_token_from_request(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Extract token from Authorization header or HTTP-only cookie."""
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get("attendx_token")
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """Retrieve and validate the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate institutional credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exception

    return user


def require_role(allowed_roles: List[UserRole]):
    """Enforce server-side role-based access control."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role in {[r.value for r in allowed_roles]}, but user has {current_user.role.value}"
            )
        return current_user
    return role_checker


require_admin = require_role([UserRole.ADMIN])
require_teacher = require_role([UserRole.TEACHER, UserRole.ADMIN])
require_student = require_role([UserRole.STUDENT])
require_any_authenticated = require_role([UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT])

