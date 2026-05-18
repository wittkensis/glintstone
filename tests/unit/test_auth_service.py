"""Unit tests for auth_service — no DB, no network."""

import hashlib

import pytest
from itsdangerous import BadSignature, SignatureExpired

from api.services.auth_service import (
    generate_api_key,
    generate_session_token,
    hash_token,
    sign_magic_link,
    verify_magic_link,
)

SECRET = "test-secret-key"


def test_hash_token_is_sha256():
    raw = "hello"
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert hash_token(raw) == expected


def test_hash_token_consistent():
    assert hash_token("abc") == hash_token("abc")


def test_hash_token_differs():
    assert hash_token("a") != hash_token("b")


def test_generate_session_token_urlsafe():
    token = generate_session_token()
    assert len(token) > 20
    # url-safe base64 characters only
    import re

    assert re.fullmatch(r"[A-Za-z0-9_\-]+", token)


def test_generate_api_key_prefix():
    raw, key_hash = generate_api_key()
    assert raw.startswith("glst_")
    assert key_hash == hash_token(raw)


def test_generate_api_key_unique():
    keys = {generate_api_key()[0] for _ in range(20)}
    assert len(keys) == 20


def test_magic_link_round_trip():
    email = "test@example.com"
    token = sign_magic_link(email, SECRET)
    recovered = verify_magic_link(token, SECRET, max_age_seconds=60)
    assert recovered == email


def test_magic_link_tampered():
    token = sign_magic_link("test@example.com", SECRET)
    tampered = token[:-4] + "xxxx"
    with pytest.raises(BadSignature):
        verify_magic_link(tampered, SECRET, max_age_seconds=60)


def test_magic_link_wrong_secret():
    token = sign_magic_link("test@example.com", SECRET)
    with pytest.raises(BadSignature):
        verify_magic_link(token, "wrong-secret", max_age_seconds=60)


def test_magic_link_expired():
    token = sign_magic_link("test@example.com", SECRET)
    # max_age=-1 means any age > -1, which is always true — forces SignatureExpired
    with pytest.raises(SignatureExpired):
        verify_magic_link(token, SECRET, max_age_seconds=-1)
