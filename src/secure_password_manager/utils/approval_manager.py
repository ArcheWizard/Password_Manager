"""Approval management system for browser bridge credential access.

This module provides a centralized approval system for handling credential
access requests from browser extensions, with support for user prompts,
remembering decisions, and audit logging.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_data_dir


class ApprovalDecision(Enum):
    """Approval decision types."""

    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """Represents a credential access request awaiting approval."""

    request_id: str
    origin: str
    browser: str
    fingerprint: str
    timestamp: float
    entry_count: int
    username_preview: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ApprovalResponse:
    """Represents the response to an approval request."""

    request_id: str
    decision: ApprovalDecision
    remember: bool = False
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ApprovalStore:
    """Manages persistent approval decisions (remembered origins)."""

    def __init__(self, path: Path):
        self.path = path
        self._approvals: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load saved approvals from disk."""
        if not self.path.exists():
            self._approvals = {}
            return

        try:
            with open(self.path, encoding="utf-8") as f:
                self._approvals = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log_warning(f"Failed to load approval store: {e}")
            self._approvals = {}

    def _save(self) -> None:
        """Save approvals to disk."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._approvals, f, indent=2)
        except OSError as e:
            log_warning(f"Failed to save approval store: {e}")

    def is_approved(self, origin: str, fingerprint: str) -> bool:
        """Check if an origin is pre-approved for a fingerprint."""
        key = f"{origin}:{fingerprint}"
        approval = self._approvals.get(key)

        if not approval:
            return False

        # Check if approval has expired (optional: could add expiry logic here)
        return approval.get("approved", False)

    def remember_approval(self, origin: str, fingerprint: str, approved: bool) -> None:
        """Remember an approval decision for an origin."""
        key = f"{origin}:{fingerprint}"
        self._approvals[key] = {
            "approved": approved,
            "timestamp": time.time(),
            "origin": origin,
            "fingerprint": fingerprint,
        }
        self._save()
        log_info(f"Remembered approval for {origin}: {approved}")

    def revoke_approval(self, origin: str, fingerprint: str) -> bool:
        """Revoke a remembered approval."""
        key = f"{origin}:{fingerprint}"
        if key in self._approvals:
            del self._approvals[key]
            self._save()
            log_info(f"Revoked approval for {origin}")
            return True
        return False

    def list_approvals(self) -> List[Dict[str, Any]]:
        """List all remembered approvals."""
        return [
            {
                "origin": approval["origin"],
                "fingerprint": approval["fingerprint"],
                "timestamp": approval["timestamp"],
                "approved": approval["approved"],
            }
            for approval in self._approvals.values()
        ]

    def clear_all(self) -> int:
        """Clear all remembered approvals."""
        count = len(self._approvals)
        self._approvals = {}
        self._save()
        log_info(f"Cleared {count} remembered approvals")
        return count


class ApprovalManager:
    """Manages approval requests and responses with threading support."""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self._store = ApprovalStore(get_data_dir() / "approval_store.json")
        self._pending: Dict[str, ApprovalRequest] = {}
        self._responses: Dict[str, ApprovalResponse] = {}
        self._lock = threading.Lock()
        self._prompt_handler: Optional[
            Callable[[ApprovalRequest], ApprovalResponse]
        ] = None

    def set_prompt_handler(
        self, handler: Callable[[ApprovalRequest], ApprovalResponse]
    ) -> None:
        """Set the function that prompts the user for approval."""
        self._prompt_handler = handler

    def request_approval(
        self,
        origin: str,
        browser: str,
        fingerprint: str,
        entry_count: int,
        username_preview: Optional[str] = None,
    ) -> ApprovalResponse:
        """
        Request approval for credential access.

        Returns immediately with cached decision if origin is remembered,
        otherwise prompts user and waits for response.
        """
        # Check if pre-approved
        if self._store.is_approved(origin, fingerprint):
            log_info(f"Auto-approved credential access for {origin} (remembered)")
            return ApprovalResponse(
                request_id="auto",
                decision=ApprovalDecision.APPROVED,
                remember=True,
            )

        # Create approval request
        request_id = f"{origin}_{int(time.time() * 1000)}"
        request = ApprovalRequest(
            request_id=request_id,
            origin=origin,
            browser=browser,
            fingerprint=fingerprint,
            timestamp=time.time(),
            entry_count=entry_count,
            username_preview=username_preview,
        )

        with self._lock:
            self._pending[request_id] = request

        log_info(f"Approval requested for {origin} from {browser} ({fingerprint})")

        # Prompt user if handler is set
        if self._prompt_handler:
            try:
                response = self._prompt_handler(request)

                # Remember decision if requested
                if response.remember:
                    self._store.remember_approval(
                        origin,
                        fingerprint,
                        response.decision == ApprovalDecision.APPROVED,
                    )

                with self._lock:
                    self._responses[request_id] = response
                    if request_id in self._pending:
                        del self._pending[request_id]

                return response
            except Exception as e:
                log_warning(f"Approval prompt handler failed: {e}")
                # Fall through to timeout

        # No handler or handler failed - return timeout
        response = ApprovalResponse(
            request_id=request_id,
            decision=ApprovalDecision.TIMEOUT,
        )

        with self._lock:
            self._responses[request_id] = response
            if request_id in self._pending:
                del self._pending[request_id]

        return response

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get list of pending approval requests."""
        with self._lock:
            return list(self._pending.values())

    def respond_to_request(
        self,
        request_id: str,
        decision: ApprovalDecision,
        remember: bool = False,
    ) -> bool:
        """Respond to a pending request (used for async approval flows)."""
        with self._lock:
            if request_id not in self._pending:
                return False

            request = self._pending[request_id]
            response = ApprovalResponse(
                request_id=request_id,
                decision=decision,
                remember=remember,
            )

            # Remember decision if requested
            if remember:
                self._store.remember_approval(
                    request.origin,
                    request.fingerprint,
                    decision == ApprovalDecision.APPROVED,
                )

            self._responses[request_id] = response
            del self._pending[request_id]

            log_info(f"Approval {decision.value} for {request.origin}")
            return True

    def get_approval_store(self) -> ApprovalStore:
        """Get the approval store for managing remembered decisions."""
        return self._store

    def cleanup_old_responses(self, max_age_seconds: int = 300) -> int:
        """Remove old responses to prevent memory buildup."""
        cutoff = time.time() - max_age_seconds
        removed = 0

        with self._lock:
            to_remove = [
                rid for rid, resp in self._responses.items() if resp.timestamp < cutoff
            ]
            for rid in to_remove:
                del self._responses[rid]
                removed += 1

        if removed > 0:
            log_info(f"Cleaned up {removed} old approval responses")

        return removed


# Global approval manager instance
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get or create the global approval manager instance."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
