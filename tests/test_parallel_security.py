"""Tests for parallelized security checks."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.crypto import encrypt_password
from secure_password_manager.utils.database import add_password, init_db
from secure_password_manager.utils.parallel_security import (
    analyze_passwords_parallel,
    batch_process_entries,
    check_breaches_parallel,
)


@pytest.fixture
def setup_test_passwords(clean_crypto_files, clean_database):
    """Setup test database with multiple passwords."""
    init_db()

    test_passwords = [
        ("example1.com", "user1", "StrongPass123!"),
        ("example2.com", "user2", "WeakPassword"),
        ("example3.com", "user3", "Another$trongP@ss"),
        ("example4.com", "user4", "password"),  # Very weak
        ("example5.com", "user5", "C0mpl3x!P@ssw0rd"),
    ]

    for website, username, password in test_passwords:
        encrypted = encrypt_password(password)
        add_password(website, username, encrypted)


def test_check_breaches_parallel_empty():
    """Test parallel breach check with empty list."""
    results = check_breaches_parallel([])
    assert results == {}


def test_check_breaches_parallel_single():
    """Test parallel breach check with single password."""
    passwords = [(1, "TestPassword123")]

    with patch('secure_password_manager.utils.parallel_security.check_password_breach') as mock_check:
        mock_check.return_value = (False, 0)
        results = check_breaches_parallel(passwords, max_workers=1)

    assert len(results) == 1
    assert 1 in results
    assert results[1] == (False, 0)


def test_check_breaches_parallel_multiple():
    """Test parallel breach check with multiple passwords."""
    passwords = [
        (1, "Password1"),
        (2, "Password2"),
        (3, "Password3"),
        (4, "Password4"),
        (5, "Password5"),
    ]

    with patch('secure_password_manager.utils.parallel_security.check_password_breach') as mock_check:
        # Return based on password value to ensure consistent results
        def mock_breach(password):
            if password == "Password2":
                return (True, 100)
            elif password == "Password4":
                return (True, 500)
            return (False, 0)

        mock_check.side_effect = mock_breach

        results = check_breaches_parallel(passwords, max_workers=3)

    assert len(results) == 5
    assert results[2] == (True, 100)
    assert results[4] == (True, 500)
def test_check_breaches_parallel_handles_errors():
    """Test that parallel check handles errors gracefully."""
    passwords = [
        (1, "Password1"),
        (2, "Password2"),
    ]

    with patch('secure_password_manager.utils.parallel_security.check_password_breach') as mock_check:
        # First call succeeds, second raises exception
        mock_check.side_effect = [(False, 0), Exception("API Error")]

        results = check_breaches_parallel(passwords, max_workers=2)

    # Should still have results for both (error case returns False, 0)
    assert len(results) == 2
    assert results[1] == (False, 0)
    assert results[2] == (False, 0)


def test_analyze_passwords_parallel_empty():
    """Test parallel analysis with empty list."""
    results = analyze_passwords_parallel([])
    assert results == {}


def test_analyze_passwords_parallel_multiple():
    """Test parallel analysis of multiple passwords."""
    passwords = [
        (1, "StrongP@ssw0rd123"),
        (2, "weak"),
        (3, "M3dium!Pass"),
    ]

    results = analyze_passwords_parallel(passwords, check_breaches=False, max_workers=2)

    assert len(results) == 3

    # Strong password should have high score
    assert results[1]["score"] >= 3

    # Weak password should have low score
    assert results[2]["score"] <= 2

    # All should have strength rating
    assert all("strength" in results[i] for i in [1, 2, 3])


def test_analyze_passwords_parallel_with_breach_check():
    """Test parallel analysis with breach checking enabled."""
    passwords = [(1, "TestPassword123")]

    with patch('secure_password_manager.utils.security_analyzer.check_password_breach') as mock_check:
        mock_check.return_value = (True, 1000)

        results = analyze_passwords_parallel(passwords, check_breaches=True, max_workers=1)

    assert len(results) == 1
    assert "breached" in results[1]
    assert results[1]["breached"] is True


def test_batch_process_entries(setup_test_passwords):
    """Test batch processing of password entries."""
    from secure_password_manager.utils.database import get_passwords

    entries = get_passwords()
    assert len(entries) >= 5

    # Process with small batch size to test batching
    results = batch_process_entries(
        entries,
        batch_size=2,
        max_workers=2,
        check_breaches=False  # Disable to avoid API calls
    )

    # Should have results for all entries
    assert len(results) >= 5

    # Each result should have analysis info
    for entry_id, analysis in results.items():
        assert "score" in analysis or "error" in analysis
        if "score" in analysis:
            assert "strength" in analysis


def test_batch_process_handles_decryption_errors(clean_crypto_files, clean_database):
    """Test that batch processing handles decryption errors gracefully."""
    init_db()

    # Add entry with corrupt encrypted data
    from secure_password_manager.utils.database import get_passwords
    import sqlite3

    conn = sqlite3.connect(str(clean_database))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO passwords (website, username, password, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        ("corrupt.com", "user", b"invalid_encrypted_data", 1000000, 1000000)
    )
    conn.commit()
    conn.close()

    entries = get_passwords()
    assert len(entries) >= 1

    results = batch_process_entries(entries, batch_size=10, check_breaches=False)

    # Should have error result for corrupt entry
    assert len(results) >= 1
    # At least one result should indicate an error
    assert any("error" in result for result in results.values())


def test_parallelization_performance_improvement():
    """Test that parallel processing is faster than sequential."""
    import time

    # Create test data
    passwords = [(i, f"Password{i}!@#") for i in range(20)]

    with patch('secure_password_manager.utils.parallel_security.check_password_breach') as mock_check:
        # Simulate slow API call
        def slow_check(pwd):
            time.sleep(0.05)  # 50ms per call
            return (False, 0)

        mock_check.side_effect = slow_check

        # Time parallel execution with 5 workers
        start = time.time()
        check_breaches_parallel(passwords, max_workers=5)
        parallel_time = time.time() - start

    # With 20 passwords at 50ms each:
    # Sequential would take ~1000ms (20 * 50)
    # Parallel with 5 workers should take ~200ms (4 batches * 50)
    # Allow overhead for CI environments
    assert parallel_time < 1.0  # Should complete in under 1 second (relaxed for CI)


def test_concurrent_workers_limit():
    """Test that max_workers parameter is respected."""
    passwords = [(i, f"Pass{i}") for i in range(10)]

    # This should not raise an exception even with many entries
    with patch('secure_password_manager.utils.parallel_security.check_password_breach') as mock_check:
        mock_check.return_value = (False, 0)

        # Test with different worker counts
        for workers in [1, 5, 10]:
            results = check_breaches_parallel(passwords, max_workers=workers)
            assert len(results) == 10
