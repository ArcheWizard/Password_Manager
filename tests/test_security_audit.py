"""Tests for security_audit module."""

import os
import sys
import time
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import security_audit
from secure_password_manager.utils.crypto import encrypt_password
from secure_password_manager.utils.database import add_password, init_db
from secure_password_manager.utils.security_audit import (
    audit_password_strength,
    fix_security_issues,
    get_security_score,
    run_security_audit,
)


@pytest.fixture
def setup_test_passwords(clean_crypto_files, clean_database):
    """Setup test passwords for auditing."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    # Add weak password
    add_password("example.com", "user1", encrypt_password("weak"), "Work")

    # Add reused password (same password for different sites)
    reused_pw = encrypt_password("Reused123!")
    add_password("site1.com", "user1", reused_pw, "Personal")
    add_password("site2.com", "user2", reused_pw, "Personal")

    # Add duplicate entry (same site and username)
    add_password("duplicate.com", "user1", encrypt_password("Pass123!"), "Work")
    add_password("duplicate.com", "user1", encrypt_password("Pass456!"), "Work")

    # Add strong password
    add_password(
        "secure.com", "user1", encrypt_password("vEry$tr0ng!P@ssw0rd123"), "Work"
    )

    # Add expired password
    add_password(
        "expired.com", "user1", encrypt_password("OldPass123!"), "Work", expiry_days=-30
    )  # Expired 30 days ago


def test_audit_password_strength_weak_passwords(setup_test_passwords):
    """Test auditing for weak passwords."""
    audit_results = audit_password_strength()

    assert "weak_passwords" in audit_results
    weak = audit_results["weak_passwords"]

    # Should find at least the "weak" password
    assert len(weak) >= 1
    assert any(p["website"] == "example.com" for p in weak)


def test_audit_password_strength_reused_passwords(setup_test_passwords):
    """Test auditing for reused passwords."""
    audit_results = audit_password_strength()

    assert "reused_passwords" in audit_results
    reused = audit_results["reused_passwords"]

    # Should find the reused password
    assert len(reused) >= 1
    sites = [p["website"] for p in reused]
    assert "site1.com" in sites or "site2.com" in sites


def test_audit_password_strength_duplicate_entries(setup_test_passwords):
    """Test auditing for duplicate entries."""
    audit_results = audit_password_strength()

    assert "duplicate_passwords" in audit_results
    duplicates = audit_results["duplicate_passwords"]

    # Should find the duplicate entry
    assert len(duplicates) >= 1
    assert any(p["website"] == "duplicate.com" for p in duplicates)


def test_audit_password_strength_expired_passwords(setup_test_passwords):
    """Test auditing for expired passwords."""
    audit_results = audit_password_strength()

    assert "expired_passwords" in audit_results
    expired = audit_results["expired_passwords"]

    # Should find the expired password
    assert len(expired) >= 1
    expired_entry = next((p for p in expired if p["website"] == "expired.com"), None)
    assert expired_entry is not None
    assert expired_entry["expired_days"] > 0


def test_audit_password_strength_breached_passwords(setup_test_passwords):
    """Test auditing for breached passwords (with mocked API)."""
    # Mock the analyze_password_security function to simulate a breach
    with patch.object(security_audit, "analyze_password_security") as mock_analyze:
        mock_analyze.return_value = {"breached": True, "breach_count": 12345}

        audit_results = audit_password_strength()

        assert "breached_passwords" in audit_results
        # Breached list might be limited by the 10-entry cap in the code


def test_audit_password_strength_empty_database(clean_crypto_files, clean_database):
    """Test auditing with no passwords."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    audit_results = audit_password_strength()

    assert audit_results["weak_passwords"] == []
    assert audit_results["duplicate_passwords"] == []
    assert audit_results["reused_passwords"] == []
    assert audit_results["expired_passwords"] == []
    assert audit_results["breached_passwords"] == []


def test_get_security_score_perfect_vault(clean_crypto_files, clean_database):
    """Test security score with all strong passwords."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    # Add only strong, unique passwords
    add_password(
        "site1.com", "user1", encrypt_password("vEry$tr0ng!P@ssw0rd123"), "Work"
    )
    add_password(
        "site2.com", "user2", encrypt_password("An0th3r!Str0ng#Pass"), "Personal"
    )

    score = get_security_score()

    # Should be high (close to 100)
    assert score >= 85


def test_get_security_score_weak_vault(setup_test_passwords):
    """Test security score with weak passwords."""
    score = get_security_score()

    # Should be lower due to weak, reused, and expired passwords
    assert score < 100


def test_get_security_score_empty_vault(clean_crypto_files, clean_database):
    """Test security score with empty vault."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    score = get_security_score()

    # Empty vault should return 100
    assert score == 100


def test_get_security_score_range(setup_test_passwords):
    """Test that security score is always between 0 and 100."""
    score = get_security_score()

    assert 0 <= score <= 100
    assert isinstance(score, int)


def test_fix_security_issues():
    """Test fix_security_issues stub."""
    # Currently returns 0 (not implemented)
    fixed = fix_security_issues([])
    assert fixed == 0


def test_run_security_audit(setup_test_passwords):
    """Test running a comprehensive security audit."""
    audit_report = run_security_audit()

    assert "score" in audit_report
    assert "issues" in audit_report
    assert "timestamp" in audit_report

    assert isinstance(audit_report["score"], int)
    assert 0 <= audit_report["score"] <= 100

    issues = audit_report["issues"]
    assert "weak_passwords" in issues
    assert "duplicate_passwords" in issues
    assert "reused_passwords" in issues
    assert "expired_passwords" in issues
    assert "breached_passwords" in issues

    # Timestamp should be recent
    current_time = int(time.time())
    assert abs(audit_report["timestamp"] - current_time) < 5


def test_audit_handles_breach_check_errors(setup_test_passwords):
    """Test that audit handles breach check errors gracefully."""
    # Mock analyze_password_security to raise an exception
    with patch.object(security_audit, "analyze_password_security") as mock_analyze:
        mock_analyze.side_effect = Exception("Network error")

        # Should not raise, just skip breach checking
        audit_results = audit_password_strength()

        assert "breached_passwords" in audit_results
        # Might be empty due to errors


def test_security_score_deductions(clean_crypto_files, clean_database):
    """Test that security score properly deducts for various issues."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    # Add only weak passwords
    for i in range(10):
        add_password(f"site{i}.com", f"user{i}", encrypt_password("weak"), "Work")

    score = get_security_score()

    # Should have significant deduction for all weak passwords
    assert score < 70  # Should lose at least 30 points for all weak
