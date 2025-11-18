import json
from pathlib import Path

from secure_password_manager.services.browser_bridge import TokenStore


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

    with open(store_path, "r", encoding="utf-8") as handle:
        # ensure valid JSON now
        json.load(handle)
