"""Tests for the approval manager system."""

import time

import pytest

from secure_password_manager.utils.approval_manager import (
    ApprovalDecision,
    ApprovalManager,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStore,
    get_approval_manager,
)


@pytest.fixture
def temp_approval_store(tmp_path):
    """Create a temporary approval store for testing."""
    store_path = tmp_path / "approval_store.json"
    return ApprovalStore(store_path)


@pytest.fixture
def approval_manager():
    """Create a fresh approval manager for testing."""
    return ApprovalManager(timeout_seconds=5)


def test_approval_store_remember_and_check(temp_approval_store):
    """Test remembering and checking approval decisions."""
    origin = "https://example.com"
    fingerprint = "abc123def456"

    # Initially not approved
    assert not temp_approval_store.is_approved(origin, fingerprint)

    # Remember approval
    temp_approval_store.remember_approval(origin, fingerprint, approved=True)

    # Now should be approved
    assert temp_approval_store.is_approved(origin, fingerprint)

    # Different origin should not be approved
    assert not temp_approval_store.is_approved("https://other.com", fingerprint)


def test_approval_store_remember_denial(temp_approval_store):
    """Test remembering denial decisions."""
    origin = "https://malicious.com"
    fingerprint = "bad123bad456"

    # Remember denial
    temp_approval_store.remember_approval(origin, fingerprint, approved=False)

    # Should not be approved (approval check returns False for denials)
    assert not temp_approval_store.is_approved(origin, fingerprint)


def test_approval_store_persistence(tmp_path):
    """Test that approval decisions persist across instances."""
    store_path = tmp_path / "approval_store.json"
    origin = "https://persistent.com"
    fingerprint = "persist123"

    # Create first store and remember approval
    store1 = ApprovalStore(store_path)
    store1.remember_approval(origin, fingerprint, approved=True)

    # Create second store with same path
    store2 = ApprovalStore(store_path)

    # Should load the saved approval
    assert store2.is_approved(origin, fingerprint)


def test_approval_store_list_approvals(temp_approval_store):
    """Test listing all remembered approvals."""
    origins = [
        ("https://site1.com", "fp1"),
        ("https://site2.com", "fp2"),
        ("https://site3.com", "fp3"),
    ]

    for origin, fingerprint in origins:
        temp_approval_store.remember_approval(origin, fingerprint, approved=True)

    approvals = temp_approval_store.list_approvals()
    assert len(approvals) == 3

    # Check all origins are present
    approval_origins = {a["origin"] for a in approvals}
    expected_origins = {origin for origin, _ in origins}
    assert approval_origins == expected_origins


def test_approval_store_revoke_approval(temp_approval_store):
    """Test revoking a remembered approval."""
    origin = "https://revoke.com"
    fingerprint = "revoke123"

    # Remember approval
    temp_approval_store.remember_approval(origin, fingerprint, approved=True)
    assert temp_approval_store.is_approved(origin, fingerprint)

    # Revoke
    result = temp_approval_store.revoke_approval(origin, fingerprint)
    assert result is True

    # Should no longer be approved
    assert not temp_approval_store.is_approved(origin, fingerprint)

    # Revoking again should return False
    result = temp_approval_store.revoke_approval(origin, fingerprint)
    assert result is False


def test_approval_store_clear_all(temp_approval_store):
    """Test clearing all approvals."""
    # Add multiple approvals
    for i in range(5):
        temp_approval_store.remember_approval(
            f"https://site{i}.com", f"fp{i}", approved=True
        )

    # Clear all
    count = temp_approval_store.clear_all()
    assert count == 5

    # Should have no approvals
    assert len(temp_approval_store.list_approvals()) == 0


def test_approval_manager_auto_approve_remembered(approval_manager):
    """Test automatic approval for remembered origins."""
    origin = "https://remembered.com"
    fingerprint = "remembered123"

    # Remember approval
    approval_manager.get_approval_store().remember_approval(
        origin, fingerprint, approved=True
    )

    # Request should be auto-approved
    response = approval_manager.request_approval(
        origin=origin,
        browser="Chrome",
        fingerprint=fingerprint,
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.APPROVED
    assert response.remember is True


def test_approval_manager_timeout_no_handler(approval_manager):
    """Test that requests timeout when no handler is set."""
    response = approval_manager.request_approval(
        origin="https://timeout.com",
        browser="Firefox",
        fingerprint="timeout123",
        entry_count=2,
    )

    assert response.decision == ApprovalDecision.TIMEOUT


def test_approval_manager_with_handler(approval_manager):
    """Test approval with a custom handler."""

    # Set up a handler that always approves
    def auto_approve_handler(request: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            remember=False,
        )

    approval_manager.set_prompt_handler(auto_approve_handler)

    response = approval_manager.request_approval(
        origin="https://handled.com",
        browser="Safari",
        fingerprint="handled123",
        entry_count=3,
    )

    assert response.decision == ApprovalDecision.APPROVED


def test_approval_manager_handler_remembers_decision(approval_manager):
    """Test that handler can remember decisions."""

    # Handler that approves and remembers
    def remember_approve_handler(request: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            remember=True,
        )

    approval_manager.set_prompt_handler(remember_approve_handler)

    origin = "https://remember.com"
    fingerprint = "remember123"

    # First request
    response1 = approval_manager.request_approval(
        origin=origin,
        browser="Chrome",
        fingerprint=fingerprint,
        entry_count=1,
    )

    assert response1.decision == ApprovalDecision.APPROVED
    assert response1.remember is True

    # Remove handler to test auto-approval
    approval_manager.set_prompt_handler(None)

    # Second request should be auto-approved
    response2 = approval_manager.request_approval(
        origin=origin,
        browser="Chrome",
        fingerprint=fingerprint,
        entry_count=1,
    )

    assert response2.decision == ApprovalDecision.APPROVED


def test_approval_manager_handler_denies(approval_manager):
    """Test handler that denies requests."""

    # Handler that denies
    def deny_handler(request: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.DENIED,
            remember=False,
        )

    approval_manager.set_prompt_handler(deny_handler)

    response = approval_manager.request_approval(
        origin="https://denied.com",
        browser="Chrome",
        fingerprint="denied123",
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.DENIED


def test_approval_manager_username_preview(approval_manager):
    """Test that username preview is passed to handler."""
    captured_request = None

    def capture_handler(request: ApprovalRequest) -> ApprovalResponse:
        nonlocal captured_request
        captured_request = request
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            remember=False,
        )

    approval_manager.set_prompt_handler(capture_handler)

    response = approval_manager.request_approval(
        origin="https://test.com",
        browser="Chrome",
        fingerprint="test123",
        entry_count=1,
        username_preview="testuser@example.com",
    )

    assert captured_request is not None
    assert captured_request.username_preview == "testuser@example.com"
    assert captured_request.entry_count == 1
    assert captured_request.origin == "https://test.com"


def test_approval_manager_cleanup_old_responses(approval_manager):
    """Test cleanup of old approval responses."""

    # Set handler that approves
    def approve_handler(request: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            remember=False,
        )

    approval_manager.set_prompt_handler(approve_handler)

    # Make several requests
    for i in range(5):
        approval_manager.request_approval(
            origin=f"https://site{i}.com",
            browser="Chrome",
            fingerprint=f"fp{i}",
            entry_count=1,
        )

    # Responses should be stored
    assert len(approval_manager._responses) == 5

    # Wait a bit
    time.sleep(0.2)

    # Clean up old responses (with short max age)
    removed = approval_manager.cleanup_old_responses(max_age_seconds=0)

    # Should have cleaned up all responses
    assert removed == 5
    assert len(approval_manager._responses) == 0


def test_approval_request_to_dict():
    """Test ApprovalRequest serialization."""
    request = ApprovalRequest(
        request_id="test123",
        origin="https://example.com",
        browser="Chrome",
        fingerprint="fp123",
        timestamp=1234567890.0,
        entry_count=2,
        username_preview="user@example.com",
    )

    data = request.to_dict()

    assert data["request_id"] == "test123"
    assert data["origin"] == "https://example.com"
    assert data["browser"] == "Chrome"
    assert data["fingerprint"] == "fp123"
    assert data["timestamp"] == 1234567890.0
    assert data["entry_count"] == 2
    assert data["username_preview"] == "user@example.com"


def test_get_approval_manager_singleton():
    """Test that get_approval_manager returns a singleton."""
    manager1 = get_approval_manager()
    manager2 = get_approval_manager()

    # Should be the same instance
    assert manager1 is manager2


def test_approval_manager_handler_exception(approval_manager):
    """Test that handler exceptions are caught gracefully."""

    # Handler that raises an exception
    def error_handler(request: ApprovalRequest) -> ApprovalResponse:
        raise ValueError("Handler error")

    approval_manager.set_prompt_handler(error_handler)

    # Should return timeout instead of crashing
    response = approval_manager.request_approval(
        origin="https://error.com",
        browser="Chrome",
        fingerprint="error123",
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.TIMEOUT


def test_approval_store_corrupted_file(tmp_path):
    """Test handling of corrupted approval store file."""
    store_path = tmp_path / "corrupted.json"

    # Write corrupted JSON
    store_path.write_text("{invalid json")

    # Should handle gracefully
    store = ApprovalStore(store_path)

    # Should have empty approvals
    assert len(store.list_approvals()) == 0
