"""Integration tests for browser bridge approval system."""

import pytest

from secure_password_manager.utils.approval_manager import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResponse,
    get_approval_manager,
)
from secure_password_manager.utils.database import add_password, init_db
from secure_password_manager.utils.crypto import encrypt_password


@pytest.fixture
def setup_test_credentials():
    """Set up test credentials in the database."""
    init_db()

    # Add a test credential
    encrypted = encrypt_password("TestPassword123!")
    add_password(
        website="https://example.com/login",
        username="testuser",
        encrypted_password=encrypted,
        category="Test",
        notes="Integration test credential",
    )


def test_approval_manager_approves_credential_access(setup_test_credentials):
    """Test that approval manager correctly approves credential access."""
    approval_manager = get_approval_manager()

    # Set handler that approves
    def auto_approve_handler(request: ApprovalRequest) -> ApprovalResponse:
        assert request.origin == "example.com"
        assert request.browser == "Chrome"
        assert request.entry_count == 1
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            remember=False,
        )

    approval_manager.set_prompt_handler(auto_approve_handler)

    # Request approval
    response = approval_manager.request_approval(
        origin="example.com",
        browser="Chrome",
        fingerprint="test-fp-123",
        entry_count=1,
        username_preview="testuser",
    )

    assert response.decision == ApprovalDecision.APPROVED
    assert response.remember is False


def test_approval_manager_denies_credential_access(setup_test_credentials):
    """Test that approval manager correctly denies credential access."""
    approval_manager = get_approval_manager()

    # Set handler that denies
    def deny_handler(request: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.DENIED,
            remember=True,
        )

    approval_manager.set_prompt_handler(deny_handler)

    # Request approval
    response = approval_manager.request_approval(
        origin="malicious.com",
        browser="Chrome",
        fingerprint="test-fp-456",
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.DENIED
    assert response.remember is True


def test_remembered_approval_bypasses_prompt(setup_test_credentials):
    """Test that remembered approvals auto-approve without prompting."""
    approval_manager = get_approval_manager()

    # Remember approval
    approval_manager.get_approval_store().remember_approval(
        origin="trusted.com",
        fingerprint="trusted-fp-789",
        approved=True
    )

    # Clear handler to ensure prompt isn't called
    approval_manager.set_prompt_handler(None)

    # Request approval - should auto-approve
    response = approval_manager.request_approval(
        origin="trusted.com",
        browser="Chrome",
        fingerprint="trusted-fp-789",
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.APPROVED
    assert response.remember is True


def test_timeout_when_no_handler(setup_test_credentials):
    """Test that requests timeout when no handler is set."""
    approval_manager = get_approval_manager()
    approval_manager.set_prompt_handler(None)

    # Request approval without handler
    response = approval_manager.request_approval(
        origin="nohandler.com",
        browser="Firefox",
        fingerprint="nohandler-fp",
        entry_count=1,
    )

    assert response.decision == ApprovalDecision.TIMEOUT
