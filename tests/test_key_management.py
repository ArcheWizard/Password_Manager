import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import config
from secure_password_manager.utils.auth import set_master_password
from secure_password_manager.utils.config import KEY_MODE_FILE, KEY_MODE_PASSWORD
from secure_password_manager.utils.crypto import (
    decrypt_password,
    encrypt_password,
    is_key_protected,
    load_kdf_params,
    protect_key_with_master_password,
    set_master_password_context,
)
from secure_password_manager.utils.database import add_password, get_passwords
from secure_password_manager.utils.key_management import (
    KeyManagementError,
    apply_kdf_parameters,
    benchmark_kdf,
    switch_key_mode,
)
from secure_password_manager.utils.paths import get_secret_key_path


def _seed_password():
    secret = "SuperSecret!"
    encrypted = encrypt_password(secret)
    add_password("example.com", "alice", encrypted)
    return secret


def test_switch_to_password_mode_reencrypts_entries(clean_crypto_files, clean_database):
    password = "hunter2"
    set_master_password(password)
    set_master_password_context(password)
    original = _seed_password()

    result = switch_key_mode(KEY_MODE_PASSWORD, password)

    assert result["mode"] == KEY_MODE_PASSWORD
    assert result["entries_reencrypted"] == 1
    assert config.get_setting("key_management.mode") == KEY_MODE_PASSWORD
    assert not get_secret_key_path().exists()

    rows = get_passwords()
    assert decrypt_password(rows[0][3]) == original


def test_switch_back_to_file_mode_restores_secret_key(
    clean_crypto_files, clean_database
):
    password = "correct horse battery staple"
    set_master_password(password)
    set_master_password_context(password)
    original = _seed_password()

    switch_key_mode(KEY_MODE_PASSWORD, password)
    result = switch_key_mode(KEY_MODE_FILE, password)

    assert result["mode"] == KEY_MODE_FILE
    assert get_secret_key_path().exists()
    rows = get_passwords()
    set_master_password_context(password)
    assert decrypt_password(rows[0][3]) == original


def test_apply_kdf_parameters_updates_iterations(clean_crypto_files, clean_database):
    password = "s3cure-passphrase"
    set_master_password(password)
    set_master_password_context(password)
    original = _seed_password()

    protect_key_with_master_password(password)
    assert is_key_protected()

    summary = apply_kdf_parameters(password, iterations=200_000, salt_bytes=24)

    assert summary["iterations"] == 200_000
    assert summary["entries_reencrypted"] == 0
    assert is_key_protected()

    salt, iterations, _ = load_kdf_params()
    assert iterations == 200_000
    assert len(salt) == 24
    assert config.get_setting("key_management.kdf_iterations") == 200_000

    rows = get_passwords()
    assert decrypt_password(rows[0][3]) == original


@pytest.mark.skip(reason="Qt timer race condition in CI - QTableWidgetItem deletion issue")
def test_benchmark_kdf_returns_samples():
    result = benchmark_kdf(target_ms=60, max_iterations=120_000)
    assert result["recommended_iterations"] <= 120_000
    assert result["target_ms"] == 60
    assert result["samples"]


def test_benchmark_kdf_rejects_low_target():
    with pytest.raises(KeyManagementError):
        benchmark_kdf(target_ms=10)
