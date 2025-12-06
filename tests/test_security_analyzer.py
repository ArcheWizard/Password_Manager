"""Tests for security_analyzer module."""

import hashlib
import json
import os
import sys
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import security_analyzer
from secure_password_manager.utils.security_analyzer import (
    analyze_password_security,
    check_password_breach,
    hash_password_for_breach_check,
)


@pytest.fixture
def temp_breach_cache(tmp_path, monkeypatch):
    """Create a temporary breach cache directory."""
    cache_file = tmp_path / "breach_cache.json"

    # Import paths module directly
    from secure_password_manager.utils import paths

    monkeypatch.setattr(security_analyzer, "BREACH_CACHE_FILE", str(cache_file))
    monkeypatch.setattr(paths, "get_breach_cache_path", lambda: cache_file)
    return cache_file


def test_hash_password_for_breach_check():
    """Test password hashing for breach checking."""
    prefix, suffix = hash_password_for_breach_check("password")

    # Should return uppercase SHA-1 hash split at 5 chars
    full_hash = hashlib.sha1(b"password").hexdigest().upper()
    assert prefix == full_hash[:5]
    assert suffix == full_hash[5:]
    assert len(prefix) == 5
    assert len(suffix) == 35


def test_hash_password_for_breach_check_different_passwords():
    """Test that different passwords produce different hashes."""
    prefix1, suffix1 = hash_password_for_breach_check("password1")
    prefix2, suffix2 = hash_password_for_breach_check("password2")

    # Different passwords should have different hashes
    assert (prefix1 + suffix1) != (prefix2 + suffix2)


def test_check_password_breach_found(temp_breach_cache):
    """Test breach check when password is found."""
    # Mock the API response
    mock_response = Mock()
    mock_response.text = "ABC123:100\nDEF456:200\nGHI789:300"
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        # Check a password that would match DEF456
        with patch.object(
            security_analyzer,
            "hash_password_for_breach_check",
            return_value=("12345", "DEF456"),
        ):
            breached, count = check_password_breach("test_password")

            assert breached is True
            assert count == 200


def test_check_password_breach_not_found(temp_breach_cache):
    """Test breach check when password is not found."""
    mock_response = Mock()
    mock_response.text = "ABC123:100\nDEF456:200"
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        # Check a password that doesn't match any hash
        with patch.object(
            security_analyzer,
            "hash_password_for_breach_check",
            return_value=("12345", "XYZ999"),
        ):
            breached, count = check_password_breach("safe_password")

            assert breached is False
            assert count == 0


def test_check_password_breach_uses_cache(temp_breach_cache):
    """Test that breach check uses cached data."""
    # Populate cache
    cache_data = {"12345": [("ABC123", 100), ("DEF456", 200)]}
    temp_breach_cache.write_text(json.dumps(cache_data), encoding="utf-8")

    with patch.object(
        security_analyzer,
        "hash_password_for_breach_check",
        return_value=("12345", "DEF456"),
    ):
        # Should use cache, not call API
        with patch("requests.get") as mock_get:
            breached, count = check_password_breach("test_password")

            assert breached is True
            assert count == 200
            # Should NOT have called the API
            mock_get.assert_not_called()


def test_check_password_breach_caches_results(temp_breach_cache):
    """Test that breach check caches API results."""
    mock_response = Mock()
    mock_response.text = "ABC123:100\nDEF456:200"
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        with patch.object(
            security_analyzer,
            "hash_password_for_breach_check",
            return_value=("12345", "DEF456"),
        ):
            breached, count = check_password_breach("test_password")

            # Verify cache was created
            assert temp_breach_cache.exists()
            cache_data = json.loads(temp_breach_cache.read_text())
            assert "12345" in cache_data
            assert len(cache_data["12345"]) == 2


def test_check_password_breach_api_error(temp_breach_cache):
    """Test breach check when API call fails."""
    with patch("requests.get", side_effect=requests.RequestException("Network error")):
        breached, count = check_password_breach("test_password")

        # Should assume safe on error
        assert breached is False
        assert count == 0


def test_check_password_breach_invalid_response(temp_breach_cache):
    """Test breach check with invalid API response."""
    mock_response = Mock()
    mock_response.text = "invalid:response:format"
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        # Should handle gracefully
        breached, count = check_password_breach("test_password")

        assert breached is False
        assert count == 0


def test_check_password_breach_corrupted_cache(temp_breach_cache):
    """Test breach check with corrupted cache file."""
    # Write invalid JSON to cache
    temp_breach_cache.write_text("not valid json", encoding="utf-8")

    mock_response = Mock()
    mock_response.text = "ABC123:100"
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        # Should handle corrupted cache and call API
        breached, count = check_password_breach("test_password")

        # Should work despite corrupted cache
        assert breached is False or breached is True


def test_analyze_password_security_comprehensive(temp_breach_cache):
    """Test comprehensive password security analysis."""
    # Mock breach check
    with patch.object(
        security_analyzer, "check_password_breach", return_value=(False, 0)
    ):
        analysis = analyze_password_security("P@ssw0rd123!")

        assert "score" in analysis
        assert "strength" in analysis
        assert "entropy" in analysis
        assert "patterns" in analysis
        assert "suggestions" in analysis
        assert "breached" in analysis
        assert "breach_count" in analysis
        assert "crack_time_seconds" in analysis
        assert "crack_time" in analysis

        assert isinstance(analysis["score"], int)
        assert isinstance(analysis["strength"], str)
        assert isinstance(analysis["entropy"], float)
        assert isinstance(analysis["patterns"], list)
        assert isinstance(analysis["suggestions"], list)
        assert analysis["breached"] is False
        assert analysis["breach_count"] == 0


def test_analyze_password_security_weak_password(temp_breach_cache):
    """Test analysis of a weak password."""
    with patch.object(
        security_analyzer, "check_password_breach", return_value=(False, 0)
    ):
        analysis = analyze_password_security("password")

        assert analysis["score"] <= 2
        assert analysis["strength"] in ["Very Weak", "Weak"]
        assert len(analysis["suggestions"]) > 0


def test_analyze_password_security_strong_password(temp_breach_cache):
    """Test analysis of a strong password."""
    with patch.object(
        security_analyzer, "check_password_breach", return_value=(False, 0)
    ):
        analysis = analyze_password_security("vEry$tr0ng!P@ssw0rd123XYZ")

        assert analysis["score"] >= 4
        assert analysis["entropy"] > 100


def test_analyze_password_security_breached(temp_breach_cache):
    """Test analysis of a breached password."""
    with patch.object(
        security_analyzer, "check_password_breach", return_value=(True, 12345)
    ):
        analysis = analyze_password_security("password")

        assert analysis["breached"] is True
        assert analysis["breach_count"] == 12345


def test_analyze_password_security_crack_time(temp_breach_cache):
    """Test crack time estimation."""
    with patch.object(
        security_analyzer, "check_password_breach", return_value=(False, 0)
    ):
        # Short weak password
        analysis = analyze_password_security("pass")
        assert "crack_time" in analysis
        assert isinstance(analysis["crack_time_seconds"], float)

        # Long strong password
        analysis_strong = analyze_password_security("vEry$tr0ng!P@ssw0rd123XYZ")
        assert analysis_strong["crack_time_seconds"] > analysis["crack_time_seconds"]


def test_format_time_seconds():
    """Test time formatting."""
    from secure_password_manager.utils.security_analyzer import _format_time

    assert "seconds" in _format_time(30)
    assert "minutes" in _format_time(300)
    assert "hours" in _format_time(7200)
    assert "days" in _format_time(172800)
    assert "years" in _format_time(63072000)
    assert "centuries" in _format_time(31536000000)


def test_cache_breach_data_creates_new_cache(temp_breach_cache):
    """Test that caching creates a new cache file."""
    from secure_password_manager.utils.security_analyzer import _cache_breach_data

    hashes = [("ABC123", 100), ("DEF456", 200)]
    _cache_breach_data("12345", hashes)

    assert temp_breach_cache.exists()
    cache_data = json.loads(temp_breach_cache.read_text())
    assert "12345" in cache_data
    # JSON converts tuples to lists
    assert cache_data["12345"] == [list(h) for h in hashes]


def test_cache_breach_data_updates_existing_cache(temp_breach_cache):
    """Test that caching updates existing cache."""
    from secure_password_manager.utils.security_analyzer import _cache_breach_data

    # Create initial cache
    initial_cache = {"99999": [("XYZ999", 50)]}
    temp_breach_cache.write_text(json.dumps(initial_cache), encoding="utf-8")

    # Add new data
    new_hashes = [("ABC123", 100)]
    _cache_breach_data("12345", new_hashes)

    # Verify both old and new data exist
    cache_data = json.loads(temp_breach_cache.read_text())
    assert "99999" in cache_data
    assert "12345" in cache_data


def test_get_cached_breach_data_no_file(temp_breach_cache):
    """Test getting cached data when file doesn't exist."""
    from secure_password_manager.utils.security_analyzer import _get_cached_breach_data

    result = _get_cached_breach_data("12345")
    assert result is None


def test_get_cached_breach_data_corrupted_file(temp_breach_cache):
    """Test getting cached data from corrupted file."""
    from secure_password_manager.utils.security_analyzer import _get_cached_breach_data

    temp_breach_cache.write_text("not valid json", encoding="utf-8")

    result = _get_cached_breach_data("12345")
    assert result is None


def test_analyze_password_security_breach_check_error(temp_breach_cache):
    """Test analysis when breach check fails."""
    with patch.object(
        security_analyzer,
        "check_password_breach",
        side_effect=Exception("Network error"),
    ):
        # Should handle error gracefully
        analysis = analyze_password_security("password")

        # Should default to not breached on error
        assert analysis["breached"] is False
        assert analysis["breach_count"] == 0
