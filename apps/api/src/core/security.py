import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from apps.api.src.core.config import settings

# Initialize Argon2id password hasher (RFC 9106 recommended parameters)
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token with expiry and standard claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "attendx-ai",
        "sub": str(data.get("sub", ""))
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            issuer="attendx-ai"
        )
        return payload
    except JWTError:
        return None


def generate_qr_token_payload(session_id: str, valid_seconds: Optional[int] = None) -> Tuple[str, str, datetime]:
    """
    Generate a dynamic, tamper-evident QR payload.
    Payload incorporates:
    - session_id
    - cryptographically random nonce (32 chars)
    - UTC expiration timestamp
    - HMAC-SHA256 signature
    """
    duration = valid_seconds or settings.QR_REFRESH_INTERVAL_SECONDS
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=duration)
    nonce = secrets.token_hex(16)
    
    # Message to sign: session_id + nonce + iso_expiry
    message = f"{session_id}:{nonce}:{int(expires_at.timestamp())}".encode("utf-8")
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()
    
    # Combined token string for QR display
    token_str = f"ATX1.{session_id}.{nonce}.{int(expires_at.timestamp())}.{signature}"
    return token_str, nonce, expires_at


def verify_qr_token_payload(token_str: str, session_id: str) -> Tuple[bool, str]:
    """
    Validate a scanned dynamic QR token string against session and server clock.
    Returns: (is_valid: bool, reason: str)
    """
    try:
        parts = token_str.split(".")
        if len(parts) != 5 or parts[0] != "ATX1":
            return False, "INVALID_TOKEN_FORMAT"
        
        token_prefix, token_session_id, nonce, exp_str, signature = parts
        
        if token_session_id != session_id:
            return False, "SESSION_MISMATCH"
        
        exp_timestamp = int(exp_str)
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        
        # Check signature first to prevent timing attacks
        expected_message = f"{token_session_id}:{nonce}:{exp_str}".encode("utf-8")
        expected_signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), expected_message, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return False, "TAMPERED_TOKEN_SIGNATURE"
        
        # Check expiration (with a 2-second clock drift allowance)
        if now_timestamp > (exp_timestamp + 2):
            return False, "TOKEN_EXPIRED"
        
        return True, "VALID"
    except Exception as e:
        return False, f"TOKEN_VERIFICATION_ERROR: {str(e)}"


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware in UTC (normalizes SQLite naive timestamps)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def generate_temporary_pin(length: int = 6) -> str:
    """Generate a high-entropy numeric PIN."""
    # Use secrets to avoid predictable PRNG sequences
    digits = [str(secrets.randbelow(10)) for _ in range(length)]
    return "".join(digits)


def hash_pin(pin: str, session_id: str) -> str:
    """Hash PIN using SHA256 keyed with session ID as salt."""
    salted = f"{session_id}:{pin}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_pin(plain_pin: str, stored_hash: str, session_id: str) -> bool:
    """Verify a submitted PIN against stored hash with session salt."""
    candidate_hash = hash_pin(plain_pin, session_id)
    return hmac.compare_digest(candidate_hash, stored_hash)
