import time
from datetime import datetime, timezone
from apps.api.src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_qr_token_payload,
    verify_qr_token_payload,
    generate_temporary_pin,
    hash_pin,
    verify_pin,
)


def test_argon2id_password_hashing():
    pwd = "ZealSecurePassword2026!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert hashed.startswith("$argon2id$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_access_token():
    payload = {"sub": "user-uuid-1234", "role": "TEACHER", "email": "prof.sharma@zeal.edu.in"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-1234"
    assert decoded["role"] == "TEACHER"
    assert decoded["iss"] == "attendx-ai"


def test_dynamic_qr_token_cryptography():
    session_id = "test-session-001"
    token_str, nonce, expires_at = generate_qr_token_payload(session_id, valid_seconds=30)
    
    # Valid token check
    is_valid, reason = verify_qr_token_payload(token_str, session_id)
    assert is_valid is True
    assert reason == "VALID"

    # Mismatched session check
    is_valid_wrong_sess, reason = verify_qr_token_payload(token_str, "other-session-999")
    assert is_valid_wrong_sess is False
    assert reason == "SESSION_MISMATCH"

    # Tampered signature check
    tampered_token = token_str[:-4] + "ffff"
    is_valid_tampered, reason = verify_qr_token_payload(tampered_token, session_id)
    assert is_valid_tampered is False
    assert "TAMPERED" in reason


def test_qr_token_expiration():
    session_id = "test-session-exp"
    # Create token valid for 0 seconds
    token_str, _, _ = generate_qr_token_payload(session_id, valid_seconds=-10)
    is_valid, reason = verify_qr_token_payload(token_str, session_id)
    assert is_valid is False
    assert reason == "TOKEN_EXPIRED"


def test_temporary_pin_generation_and_verification():
    session_id = "test-session-pin"
    pin = generate_temporary_pin(6)
    assert len(pin) == 6
    assert pin.isdigit()

    stored_hash = hash_pin(pin, session_id)
    assert verify_pin(pin, stored_hash, session_id) is True
    assert verify_pin("999999" if pin != "999999" else "000000", stored_hash, session_id) is False
