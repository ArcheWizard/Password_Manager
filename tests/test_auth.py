import hashlib
import json

from secure_password_manager.utils.auth import authenticate, set_master_password
from secure_password_manager.utils.paths import get_auth_json_path


def test_set_master_password_stores_pbkdf2_record(test_env):
    password = "StrongerPass!2025"
    set_master_password(password)

    auth_path = get_auth_json_path()
    assert auth_path.exists()

    with open(auth_path, "r", encoding="utf-8") as handle:
        record = json.load(handle)

    assert record["kdf"]["algorithm"] == "PBKDF2-HMAC-SHA256"
    assert "hash" in record
    assert authenticate(password) is True
    assert authenticate("wrongpass") is False


def test_authenticate_upgrades_legacy_hash(test_env):
    legacy_password = "LegacyPass123!"
    auth_path = get_auth_json_path()
    legacy_hash = hashlib.sha256(legacy_password.encode("utf-8")).hexdigest()

    with open(auth_path, "w", encoding="utf-8") as handle:
        json.dump({"master_hash": legacy_hash}, handle)

    assert authenticate(legacy_password) is True

    # After successful authentication the file should be upgraded
    with open(auth_path, "r", encoding="utf-8") as handle:
        record = json.load(handle)
    assert "hash" in record and "kdf" in record
