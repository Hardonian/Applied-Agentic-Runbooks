"""Tests for authentication."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from agent_factory.security.auth import (
    ALGORITHM,
    SECRET_KEY,
    TokenData,
    create_access_token,
    verify_token,
)


@pytest.mark.unit
def test_create_access_token():
    """Test creating an access token."""
    data = {"sub": "user-123", "email": "test@example.com"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)

    # Verify token can be decoded
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"


@pytest.mark.unit
def test_create_access_token_with_expiry():
    """Test creating token with custom expiry."""
    data = {"sub": "user-123"}
    expires_delta = timedelta(minutes=60)
    token = create_access_token(data, expires_delta=expires_delta)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # pyjwt encodes naive datetimes as UTC epoch; compare on the UTC timescale
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert exp_time > datetime.now(timezone.utc) + timedelta(minutes=59)


@pytest.mark.unit
def test_verify_token_valid():
    """Test verifying a valid token."""
    data = {"sub": "user-123", "email": "test@example.com"}
    token = create_access_token(data)

    token_data = verify_token(token)

    assert isinstance(token_data, TokenData)
    assert token_data.user_id == "user-123"
    assert token_data.email == "test@example.com"


@pytest.mark.unit
def test_verify_token_expired():
    """Test verifying an expired token."""
    data = {"sub": "user-123"}
    expires_delta = timedelta(seconds=-1)  # Already expired
    token = create_access_token(data, expires_delta=expires_delta)

    with pytest.raises(HTTPException):
        verify_token(token)


@pytest.mark.unit
def test_verify_token_invalid():
    """Test verifying an invalid token."""
    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException):
        verify_token(invalid_token)


@pytest.mark.unit
def test_verify_token_missing_sub():
    """Test verifying token without subject."""
    data = {"email": "test@example.com"}  # Missing 'sub'
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException):
        verify_token(token)
