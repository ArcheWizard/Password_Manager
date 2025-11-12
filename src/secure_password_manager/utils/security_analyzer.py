"""Enhanced password security analysis."""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from secure_password_manager.utils.paths import get_breach_cache_path

# Cache of breached password hashes (first 5 characters of SHA-1)
BREACH_CACHE_FILE = str(get_breach_cache_path())


def hash_password_for_breach_check(password: str) -> Tuple[str, str]:
    """
    Hash a password with SHA-1 and split into prefix and suffix for
    privacy-preserving breach checking.

    Returns:
        Tuple of (prefix, suffix)
    """
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    return sha1_hash[:5], sha1_hash[5:]


def check_password_breach(password: str) -> Tuple[bool, int]:
    """
    Check if a password has been breached using the HaveIBeenPwned API.
    Uses k-anonymity model for privacy.

    Returns:
        Tuple of (breached, count)
    """
    prefix, suffix = hash_password_for_breach_check(password)

    # Try to use cached data first
    cached_results = _get_cached_breach_data(prefix)
    if cached_results is not None:
        for hash_suffix, count in cached_results:
            if hash_suffix == suffix:
                return True, count
        return False, 0

    # No cache hit, call the API
    try:
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
        response.raise_for_status()

        # Parse the response
        hashes = []
        for line in response.text.splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                hash_suffix = parts[0]
                count = int(parts[1])
                hashes.append((hash_suffix, count))
                if hash_suffix == suffix:
                    # Cache the results
                    _cache_breach_data(prefix, hashes)
                    return True, count

        # Cache the results
        _cache_breach_data(prefix, hashes)
        return False, 0

    except (requests.RequestException, ValueError):
        # If API call fails, assume the password is safe
        return False, 0


def _get_cached_breach_data(prefix: str) -> Optional[List[Tuple[str, int]]]:
    """Get cached breach data for a hash prefix."""
    if not os.path.exists(BREACH_CACHE_FILE):
        return None

    try:
        with open(BREACH_CACHE_FILE) as f:
            cache = json.load(f)

        return cache.get(prefix)
    except (OSError, json.JSONDecodeError):
        return None


def _cache_breach_data(prefix: str, hashes: List[Tuple[str, int]]) -> None:
    """Cache breach data for a hash prefix."""
    cache = {}

    # Load existing cache if available
    if os.path.exists(BREACH_CACHE_FILE):
        try:
            with open(BREACH_CACHE_FILE) as f:
                cache = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Update cache
    cache[prefix] = hashes

    # Save cache
    try:
        with open(BREACH_CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except OSError:
        pass


def analyze_password_security(password: str) -> Dict[str, Any]:
    """
    Comprehensive password security analysis.

    Returns a dictionary with analysis results.
    """
    from utils.password_analysis import (
        calculate_entropy,
        check_common_patterns,
        evaluate_password_strength,
        get_password_improvement_suggestions,
    )

    # Basic strength evaluation
    score, strength = evaluate_password_strength(password)

    # Calculate entropy
    entropy = calculate_entropy(password)

    # Check for common patterns
    patterns = check_common_patterns(password)

    # Get improvement suggestions
    suggestions = get_password_improvement_suggestions(password)

    # Check for breaches (if online)
    try:
        breached, breach_count = check_password_breach(password)
    except:
        breached, breach_count = False, 0

    # Crack time estimation (very rough approximation)
    crack_time_seconds = 0
    char_set_size = 0

    if re.search(r"[a-z]", password):
        char_set_size += 26
    if re.search(r"[A-Z]", password):
        char_set_size += 26
    if re.search(r"[0-9]", password):
        char_set_size += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        char_set_size += 33  # Approximation

    if char_set_size > 0:
        # Very simplified crack time calculation - real world is more complex
        # Assuming 10 billion guesses per second (high-end attacker)
        combinations = char_set_size ** len(password)
        crack_time_seconds = combinations / (10 * 10**9) / 2  # Average case is half

    # Format human-readable crack time
    crack_time = _format_time(crack_time_seconds)

    return {
        "score": score,
        "strength": strength,
        "entropy": entropy,
        "patterns": patterns,
        "suggestions": suggestions,
        "breached": breached,
        "breach_count": breach_count,
        "crack_time_seconds": crack_time_seconds,
        "crack_time": crack_time,
    }


def _format_time(seconds: float) -> str:
    """Format time in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds / 86400:.1f} days"
    elif seconds < 315360000:  # 10 years
        return f"{seconds / 31536000:.1f} years"
    elif seconds < 3153600000:  # 100 years
        return f"{seconds / 31536000:.0f} years"
    else:
        return "centuries"
