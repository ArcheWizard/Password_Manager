"""Parallelized security checks for improved performance.

This module provides parallel execution of security checks like breach detection,
allowing multiple passwords to be checked simultaneously for better performance.
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, Dict, List, Tuple

from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.security_analyzer import check_password_breach


def check_breaches_parallel(
    passwords: List[Tuple[int, str]],
    max_workers: int = 10,
    timeout: int = 30,
) -> Dict[int, Tuple[bool, int]]:
    """Check multiple passwords for breaches in parallel.

    Args:
        passwords: List of (entry_id, password) tuples to check
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each check

    Returns:
        Dictionary mapping entry_id to (breached, count) tuple
    """
    results = {}

    if not passwords:
        return results

    log_info(f"Starting parallel breach check for {len(passwords)} passwords with {max_workers} workers...")

    def check_single(entry_data: Tuple[int, str]) -> Tuple[int, bool, int]:
        """Check a single password and return (entry_id, breached, count)."""
        entry_id, password = entry_data
        try:
            breached, count = check_password_breach(password)
            return (entry_id, breached, count)
        except Exception as e:
            log_warning(f"Breach check failed for entry {entry_id}: {e}")
            return (entry_id, False, 0)

    # Use ThreadPoolExecutor for I/O-bound API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_entry = {
            executor.submit(check_single, pwd_data): pwd_data[0]
            for pwd_data in passwords
        }

        # Collect results as they complete
        completed = 0
        for future in concurrent.futures.as_completed(future_to_entry, timeout=timeout * len(passwords)):
            try:
                entry_id, breached, count = future.result()
                results[entry_id] = (breached, count)
                completed += 1

                if completed % 10 == 0:
                    log_info(f"Breach check progress: {completed}/{len(passwords)}")

            except concurrent.futures.TimeoutError:
                entry_id = future_to_entry[future]
                log_warning(f"Breach check timed out for entry {entry_id}")
                results[entry_id] = (False, 0)
            except Exception as e:
                entry_id = future_to_entry[future]
                log_warning(f"Breach check error for entry {entry_id}: {e}")
                results[entry_id] = (False, 0)

    log_info(f"Completed breach check: {completed}/{len(passwords)} successful")
    return results


def analyze_passwords_parallel(
    passwords: List[Tuple[int, str]],
    check_breaches: bool = True,
    max_workers: int = 10,
) -> Dict[int, Dict[str, Any]]:
    """Analyze multiple passwords in parallel.

    Args:
        passwords: List of (entry_id, password) tuples to analyze
        check_breaches: Whether to check for breaches
        max_workers: Maximum number of concurrent workers

    Returns:
        Dictionary mapping entry_id to analysis results
    """
    from secure_password_manager.utils.password_analysis import evaluate_password_strength
    from secure_password_manager.utils.security_analyzer import analyze_password_security

    results = {}

    if not passwords:
        return results

    log_info(f"Starting parallel password analysis for {len(passwords)} passwords...")

    def analyze_single(entry_data: Tuple[int, str]) -> Tuple[int, Dict[str, Any]]:
        """Analyze a single password."""
        entry_id, password = entry_data
        try:
            # Get basic strength analysis
            score, strength = evaluate_password_strength(password)

            # Get detailed security analysis (includes breach check if enabled)
            if check_breaches:
                security_info = analyze_password_security(password)
            else:
                security_info = {
                    "length": len(password),
                    "breached": False,
                    "breach_count": 0,
                }

            return (entry_id, {
                "score": score,
                "strength": strength,
                **security_info,
            })
        except Exception as e:
            log_warning(f"Password analysis failed for entry {entry_id}: {e}")
            return (entry_id, {
                "score": 0,
                "strength": "Unknown",
                "error": str(e),
            })

    # Use ThreadPoolExecutor for parallel analysis
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(analyze_single, pwd_data): pwd_data[0]
            for pwd_data in passwords
        }

        completed = 0
        for future in concurrent.futures.as_completed(future_to_entry):
            try:
                entry_id, analysis = future.result()
                results[entry_id] = analysis
                completed += 1

                if completed % 10 == 0:
                    log_info(f"Analysis progress: {completed}/{len(passwords)}")

            except Exception as e:
                entry_id = future_to_entry[future]
                log_warning(f"Analysis error for entry {entry_id}: {e}")
                results[entry_id] = {"error": str(e)}

    log_info(f"Completed password analysis: {completed}/{len(passwords)} successful")
    return results


def batch_process_entries(
    entries: List[Tuple],
    batch_size: int = 50,
    max_workers: int = 10,
    check_breaches: bool = True,
) -> Dict[int, Dict[str, Any]]:
    """Process password entries in batches for memory efficiency.

    Args:
        entries: List of password entry tuples from database
        batch_size: Number of entries to process in each batch
        max_workers: Maximum number of concurrent workers per batch
        check_breaches: Whether to check for breaches

    Returns:
        Dictionary mapping entry_id to analysis results
    """
    from secure_password_manager.utils.crypto import decrypt_password

    all_results = {}
    total_entries = len(entries)

    log_info(f"Processing {total_entries} entries in batches of {batch_size}...")

    # Process in batches
    for batch_start in range(0, total_entries, batch_size):
        batch_end = min(batch_start + batch_size, total_entries)
        batch_entries = entries[batch_start:batch_end]

        log_info(f"Processing batch {batch_start//batch_size + 1}: entries {batch_start+1}-{batch_end}")

        # Decrypt passwords in this batch
        passwords_to_check = []
        for entry in batch_entries:
            entry_id = entry[0]
            encrypted_password = entry[3]

            try:
                decrypted = decrypt_password(encrypted_password)
                passwords_to_check.append((entry_id, decrypted))
            except Exception as e:
                log_warning(f"Failed to decrypt password for entry {entry_id}: {e}")
                all_results[entry_id] = {"error": "Decryption failed"}

        # Analyze this batch in parallel
        batch_results = analyze_passwords_parallel(
            passwords_to_check,
            check_breaches=check_breaches,
            max_workers=max_workers
        )

        all_results.update(batch_results)

    log_info(f"Batch processing complete: {len(all_results)}/{total_entries} entries processed")
    return all_results
