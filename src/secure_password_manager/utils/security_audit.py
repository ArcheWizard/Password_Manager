"""Security audit functionality for the password manager."""

import time
from typing import Any, Dict, List

from secure_password_manager.utils.crypto import decrypt_password
from secure_password_manager.utils.database import get_passwords
from secure_password_manager.utils.logger import log_info
from secure_password_manager.utils.password_analysis import evaluate_password_strength
from secure_password_manager.utils.security_analyzer import analyze_password_security


def audit_password_strength() -> Dict[str, List[Dict[str, Any]]]:
    """
    Audit all passwords for strength issues.

    Returns:
        Dictionary with categorized password issues.
    """
    passwords = get_passwords()

    weak_passwords = []
    duplicate_passwords = []
    reused_passwords = []
    expired_passwords = []
    breached_passwords = []

    # Track password usage for reuse detection
    password_map = {}

    for entry in passwords:
        (
            entry_id,
            website,
            username,
            encrypted,
            category,
            notes,
            created,
            updated,
            expiry,
            favorite,
        ) = entry
        password = decrypt_password(encrypted)

        # Check strength
        score, _ = evaluate_password_strength(password)
        if score <= 2:
            weak_passwords.append(
                {
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "score": score,
                    "category": category,
                }
            )

        # Check for duplicates and reuse
        if password in password_map:
            # This is a reused password
            reused_passwords.append(
                {
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "reused_with": password_map[password],
                }
            )

            # Add to the list of sites using this password
            password_map[password].append(
                {"id": entry_id, "website": website, "username": username}
            )
        else:
            # First time seeing this password
            password_map[password] = [
                {"id": entry_id, "website": website, "username": username}
            ]

        # Check for expired passwords
        current_time = int(time.time())
        if expiry and expiry < current_time:
            expired_passwords.append(
                {
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "expired_days": int((current_time - expiry) / 86400),
                    "category": category,
                }
            )

        # Check for breached passwords (if internet is available)
        try:
            # Use a limited subset to avoid making too many API calls
            if (
                len(breached_passwords) < 10
            ):  # Limit to checking 10 passwords for breaches
                analysis = analyze_password_security(password)
                if analysis["breached"]:
                    breached_passwords.append(
                        {
                            "id": entry_id,
                            "website": website,
                            "username": username,
                            "breach_count": analysis["breach_count"],
                            "category": category,
                        }
                    )
        except:
            # Skip breach checking if it fails
            pass

    # Look for duplicate entries (different IDs but same website/username)
    site_user_map = {}
    for entry in passwords:
        entry_id, website, username = entry[0], entry[1], entry[2]
        site_user_key = f"{website}|{username}"

        if site_user_key in site_user_map:
            # This is a duplicate entry
            duplicate_passwords.append(
                {
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "duplicate_id": site_user_map[site_user_key],
                }
            )
        else:
            site_user_map[site_user_key] = entry_id

    return {
        "weak_passwords": weak_passwords,
        "duplicate_passwords": duplicate_passwords,
        "reused_passwords": reused_passwords,
        "expired_passwords": expired_passwords,
        "breached_passwords": breached_passwords,
    }


def get_security_score() -> int:
    """
    Calculate an overall security score (0-100) based on password health.

    Returns:
        Security score (0-100)
    """
    audit_results = audit_password_strength()
    passwords = get_passwords()

    if not passwords:
        return 100

    total_passwords = len(passwords)

    # Count issues
    weak_count = len(audit_results["weak_passwords"])
    duplicate_count = len(audit_results["duplicate_passwords"])
    reused_count = len(audit_results["reused_passwords"])
    expired_count = len(audit_results["expired_passwords"])
    breached_count = len(audit_results["breached_passwords"])

    # Calculate deductions
    weak_deduction = (weak_count / total_passwords) * 30
    reuse_deduction = (reused_count / total_passwords) * 30
    duplicate_deduction = (duplicate_count / total_passwords) * 10
    expired_deduction = (expired_count / total_passwords) * 15
    breached_deduction = (breached_count / total_passwords) * 15

    # Calculate score (out of 100)
    score = 100 - (
        weak_deduction
        + reuse_deduction
        + duplicate_deduction
        + expired_deduction
        + breached_deduction
    )

    # Ensure score is between 0 and 100
    return max(0, min(100, int(score)))


def fix_security_issues(issues: List[Dict[str, Any]]) -> int:
    """
    Attempt to automatically fix security issues.

    Returns:
        Number of issues fixed
    """
    # Implementation would depend on the specific issue types
    # For example, automatically regenerating weak passwords
    # or fixing duplicate entries

    # This is a more complex implementation that would need to be customized
    # based on specific requirements
    return 0


def run_security_audit() -> Dict[str, Any]:
    """Run a comprehensive security audit."""
    audit_results = audit_password_strength()
    security_score = get_security_score()

    # Log the audit
    log_info(f"Security audit completed. Score: {security_score}")

    return {
        "score": security_score,
        "issues": audit_results,
        "timestamp": int(time.time()),
    }
