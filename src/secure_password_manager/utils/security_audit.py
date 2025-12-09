"""Security audit functionality for the password manager."""

import time
from typing import Any, Dict, List

from secure_password_manager.utils.crypto import decrypt_password
from secure_password_manager.utils.database import get_passwords
from secure_password_manager.utils.logger import log_info
from secure_password_manager.utils.password_analysis import evaluate_password_strength
from secure_password_manager.utils.parallel_security import batch_process_entries
from secure_password_manager.utils.security_trending import record_audit_snapshot


def audit_password_strength(
    use_parallel: bool = True, check_breaches: bool = True, max_workers: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Audit all passwords for strength issues.

    Args:
        use_parallel: Whether to use parallel processing for breach checks
        check_breaches: Whether to check passwords against breach database
        max_workers: Maximum number of parallel workers for breach checking

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

    # If parallel processing is enabled, perform batch analysis
    if use_parallel and check_breaches:
        analysis_results = batch_process_entries(
            passwords, batch_size=50, max_workers=max_workers, check_breaches=True
        )
    else:
        analysis_results = {}

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

        # Use parallel analysis results if available, otherwise calculate inline
        if entry_id in analysis_results:
            analysis = analysis_results[entry_id]
            score = analysis.get("score", 3)
            breached = analysis.get("breached", False)
            breach_count = analysis.get("breach_count", 0)
        else:
            score, _ = evaluate_password_strength(password)
            breached = False
            breach_count = 0

        # Check strength
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

        # Check for breached passwords
        if breached:
            breached_passwords.append(
                {
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "breach_count": breach_count,
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


def fix_security_issues(
    issues: List[Dict[str, Any]],
    issue_type: str,
    auto_generate: bool = False,
    password_length: int = 16,
) -> int:
    """
    Attempt to automatically fix security issues.

    Args:
        issues: List of password issues to fix
        issue_type: Type of issue ('weak', 'breached', 'reused', 'duplicate')
        auto_generate: Whether to auto-generate new passwords
        password_length: Length for auto-generated passwords

    Returns:
        Number of issues fixed
    """
    from secure_password_manager.utils.crypto import encrypt_password
    from secure_password_manager.utils.database import delete_password, update_password
    from secure_password_manager.utils.password_generator import (
        PasswordOptions,
        PasswordStyle,
        generate_password,
    )

    fixed_count = 0

    for issue in issues:
        entry_id = issue["id"]

        try:
            if issue_type in ["weak", "breached", "reused"] and auto_generate:
                # Generate a new strong password
                options = PasswordOptions(
                    length=password_length,
                    include_uppercase=True,
                    include_lowercase=True,
                    include_digits=True,
                    include_special=True,
                    min_uppercase=2,
                    min_lowercase=2,
                    min_digits=2,
                    min_special=2,
                )

                new_password = generate_password(
                    style=PasswordStyle.RANDOM, options=options
                )
                encrypted = encrypt_password(new_password)

                # Update the password
                update_password(entry_id, encrypted_password=encrypted)
                fixed_count += 1

            elif issue_type == "duplicate":
                # Delete duplicate entries (keep the first one)
                if "duplicate_id" in issue:
                    delete_password(entry_id)
                    fixed_count += 1

        except Exception as e:
            # Log error but continue with other fixes
            log_info(f"Failed to fix issue for entry {entry_id}: {str(e)}")
            continue

    return fixed_count


def run_security_audit(
    use_parallel: bool = True, check_breaches: bool = True, max_workers: int = 10,
    record_history: bool = True
) -> Dict[str, Any]:
    """
    Run a comprehensive security audit.

    Args:
        use_parallel: Whether to use parallel processing for breach checks
        check_breaches: Whether to check passwords against breach database
        max_workers: Maximum number of parallel workers for breach checking
        record_history: Whether to record this audit in security history

    Returns:
        Dictionary containing security score, issues, and timestamp
    """
    audit_results = audit_password_strength(
        use_parallel=use_parallel, check_breaches=check_breaches, max_workers=max_workers
    )
    security_score = get_security_score()

    # Log the audit
    log_info(f"Security audit completed. Score: {security_score}")

    result = {
        "score": security_score,
        "issues": audit_results,
        "timestamp": int(time.time()),
    }

    # Record in history for trending
    if record_history:
        record_audit_snapshot(result)

    return result
