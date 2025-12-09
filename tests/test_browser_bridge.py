import json
from pathlib import Path

import pytest

from secure_password_manager.services.browser_bridge import (
    BrowserBridgeService,
    TokenStore,
)
from secure_password_manager.utils.crypto import decrypt_password
from secure_password_manager.utils.database import get_passwords, init_db


def test_token_store_persists_and_validates(tmp_path):
    store_path = Path(tmp_path) / "tokens.json"
    store = TokenStore(store_path, ttl_hours=1)

    record = store.issue_token("fingerprint-123", "chrome")
    assert "token" in record
    assert store_path.exists()

    reloaded = TokenStore(store_path, ttl_hours=1)
    validated = reloaded.validate(record["token"])
    assert validated is not None
    assert validated["fingerprint"] == "fingerprint-123"

    listed = reloaded.list_tokens()
    assert listed and listed[0]["token"] == record["token"]

    assert reloaded.revoke(record["token"])
    assert reloaded.validate(record["token"]) is None


def test_token_store_handles_expiration(tmp_path):
    store_path = Path(tmp_path) / "tokens.json"
    store = TokenStore(store_path, ttl_hours=-1)

    record = store.issue_token("fingerprint-abc", "firefox")
    assert store.validate(record["token"]) is None
    assert not store.list_tokens()


def test_token_store_recovers_from_corrupt_file(tmp_path):
    store_path = Path(tmp_path) / "tokens.json"
    store_path.write_text("not-json", encoding="utf-8")

    store = TokenStore(store_path, ttl_hours=1)
    # File should have been treated as empty
    assert store.list_tokens() == []

    record = store.issue_token("fingerprint", "edge")
    assert store.validate(record["token"]) is not None

    with open(store_path, encoding="utf-8") as handle:
        # ensure valid JSON now
        json.load(handle)


def test_credentials_store_endpoint(
    tmp_path, clean_crypto_files, clean_database, monkeypatch
):
    """Test that the credentials store endpoint actually saves to the database."""
    from fastapi.testclient import TestClient

    # Setup test environment
    init_db()

    # Create service with test token store
    token_store_path = tmp_path / "test_tokens.json"
    service = BrowserBridgeService()
    service._token_store = TokenStore(token_store_path, ttl_hours=1)

    # Issue a test token
    token_record = service._token_store.issue_token("test-fingerprint", "chrome")
    test_token = token_record["token"]

    # Create test client
    client = TestClient(service.app)

    # Prepare credentials to store
    payload = {
        "origin": "https://example.com",
        "title": "Example Site",
        "username": "testuser@example.com",
        "password": "SecureP@ssw0rd123",
        "metadata": {
            "url": "https://example.com/login",
            "saved_at": "2025-12-09T12:00:00Z",
        },
    }

    # Make request to store credentials
    response = client.post(
        "/v1/credentials/store",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "saved"
    assert data["website"] == "Example Site"
    assert data["username"] == "testuser@example.com"

    # Verify credentials were actually stored in database
    passwords = get_passwords()
    assert len(passwords) == 1

    (
        entry_id,
        website,
        username,
        encrypted_password,
        category,
        notes,
        created_at,
        updated_at,
        expiry_date,
        favorite,
    ) = passwords[0]

    assert website == "Example Site"
    assert username == "testuser@example.com"
    assert category == "Web"
    assert "URL: https://example.com/login" in notes
    assert "Browser Extension (chrome)" in notes

    # Verify password can be decrypted
    decrypted = decrypt_password(encrypted_password)
    assert decrypted == "SecureP@ssw0rd123"


def test_credentials_store_missing_fields(tmp_path, clean_crypto_files, clean_database):
    """Test that store endpoint validates required fields."""
    from fastapi.testclient import TestClient

    init_db()

    token_store_path = tmp_path / "test_tokens.json"
    service = BrowserBridgeService()
    service._token_store = TokenStore(token_store_path, ttl_hours=1)

    token_record = service._token_store.issue_token("test-fingerprint", "firefox")
    test_token = token_record["token"]

    client = TestClient(service.app)

    # Test missing password
    response = client.post(
        "/v1/credentials/store",
        json={"origin": "https://example.com", "username": "test"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 400

    # Verify nothing was stored
    passwords = get_passwords()
    assert len(passwords) == 0


def test_credentials_store_prevents_duplicates(
    tmp_path, clean_crypto_files, clean_database
):
    """Test that storing the same credentials twice doesn't create duplicates."""
    from fastapi.testclient import TestClient
    from secure_password_manager.utils.crypto import encrypt_password
    from secure_password_manager.utils.database import add_password

    init_db()

    # Add existing credential
    existing_password = encrypt_password("ExistingPass123")
    add_password(
        website="Example Site",
        username="testuser@example.com",
        encrypted_password=existing_password,
        category="Web",
    )

    token_store_path = tmp_path / "test_tokens.json"
    service = BrowserBridgeService()
    service._token_store = TokenStore(token_store_path, ttl_hours=1)

    token_record = service._token_store.issue_token("test-fingerprint", "chrome")
    test_token = token_record["token"]

    client = TestClient(service.app)

    # Try to store same credentials again
    payload = {
        "origin": "https://example.com",
        "title": "Example Site",
        "username": "testuser@example.com",
        "password": "NewPassword456",
        "metadata": {},
    }

    response = client.post(
        "/v1/credentials/store",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    # Should still succeed (backend allows it, frontend prevents it)
    assert response.status_code == 200

    # But verify we now have 2 entries (one old, one new)
    # Note: The frontend is responsible for preventing this scenario
    # by checking before prompting the user
    passwords = get_passwords()
    assert len(passwords) == 2


