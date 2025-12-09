"""Tests for security trending and historical analysis."""

import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.security_trending import (
    SecuritySnapshot,
    SecurityTrendTracker,
    get_trend_tracker,
    record_audit_snapshot,
)


@pytest.fixture
def temp_history_file(tmp_path):
    """Create a temporary history file."""
    return tmp_path / "security_history.json"


def test_security_snapshot_creation():
    """Test creating a security snapshot."""
    snapshot = SecuritySnapshot(
        timestamp=1000000,
        score=85,
        total_passwords=50,
        weak_count=5,
        reused_count=3,
        breached_count=1,
        expired_count=2,
        duplicate_count=0,
    )

    assert snapshot.score == 85
    assert snapshot.total_passwords == 50
    assert snapshot.weak_count == 5


def test_security_snapshot_serialization():
    """Test snapshot to/from dict conversion."""
    snapshot = SecuritySnapshot(
        timestamp=1000000,
        score=85,
        total_passwords=50,
        weak_count=5,
        reused_count=3,
        breached_count=1,
        expired_count=2,
        duplicate_count=0,
    )

    # Convert to dict and back
    data = snapshot.to_dict()
    restored = SecuritySnapshot.from_dict(data)

    assert restored.score == snapshot.score
    assert restored.timestamp == snapshot.timestamp
    assert restored.weak_count == snapshot.weak_count


def test_trend_tracker_initialization(temp_history_file):
    """Test trend tracker initialization."""
    tracker = SecurityTrendTracker(temp_history_file)

    assert len(tracker.get_snapshots()) == 0
    assert not temp_history_file.exists()


def test_record_snapshot(temp_history_file):
    """Test recording a security snapshot."""
    tracker = SecurityTrendTracker(temp_history_file)

    snapshot = tracker.record_snapshot(
        score=85,
        total_passwords=50,
        weak_count=5,
        reused_count=3,
        breached_count=1,
        expired_count=2,
        duplicate_count=0,
    )

    assert snapshot.score == 85
    assert len(tracker.get_snapshots()) == 1
    assert temp_history_file.exists()


def test_snapshot_persistence(temp_history_file):
    """Test that snapshots persist across tracker instances."""
    tracker1 = SecurityTrendTracker(temp_history_file)
    tracker1.record_snapshot(
        score=85, total_passwords=50, weak_count=5, reused_count=3,
        breached_count=1, expired_count=2, duplicate_count=0
    )

    # Create new tracker instance
    tracker2 = SecurityTrendTracker(temp_history_file)
    snapshots = tracker2.get_snapshots()

    assert len(snapshots) == 1
    assert snapshots[0].score == 85


def test_get_snapshots_with_days_filter(temp_history_file):
    """Test filtering snapshots by days."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add snapshots at different times
    tracker._snapshots = [
        SecuritySnapshot(now - (10 * 86400), 70, 50, 10, 5, 2, 1, 0),  # 10 days ago
        SecuritySnapshot(now - (5 * 86400), 75, 50, 8, 4, 2, 1, 0),    # 5 days ago
        SecuritySnapshot(now - (1 * 86400), 80, 50, 6, 3, 1, 1, 0),    # 1 day ago
    ]

    # Get last 7 days
    recent = tracker.get_snapshots(days=7)
    assert len(recent) == 2  # Only 5 days and 1 day ago

    # Get last 3 days
    very_recent = tracker.get_snapshots(days=3)
    assert len(very_recent) == 1  # Only 1 day ago


def test_get_snapshots_with_limit(temp_history_file):
    """Test limiting number of snapshots returned."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add 5 snapshots
    for i in range(5):
        tracker._snapshots.append(
            SecuritySnapshot(now - (i * 86400), 70 + i, 50, 10, 5, 2, 1, 0)
        )

    # Get last 3 snapshots
    limited = tracker.get_snapshots(limit=3)
    assert len(limited) == 3
    assert limited[0].score == 72  # 3rd oldest


def test_trend_analysis_improving(temp_history_file):
    """Test trend analysis with improving scores."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add improving snapshots
    tracker._snapshots = [
        SecuritySnapshot(now - (30 * 86400), 60, 50, 15, 8, 3, 2, 1),
        SecuritySnapshot(now - (20 * 86400), 70, 50, 10, 6, 2, 1, 0),
        SecuritySnapshot(now - (10 * 86400), 80, 50, 5, 3, 1, 0, 0),
        SecuritySnapshot(now, 90, 50, 2, 1, 0, 0, 0),
    ]

    analysis = tracker.get_trend_analysis(days=30)

    assert analysis["status"] == "success"
    assert analysis["trend"] == "improving"
    assert analysis["score_change"] == 30  # 90 - 60
    assert analysis["current_score"] == 90
    assert analysis["previous_score"] == 60


def test_trend_analysis_declining(temp_history_file):
    """Test trend analysis with declining scores."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add declining snapshots
    tracker._snapshots = [
        SecuritySnapshot(now - (30 * 86400), 90, 50, 2, 1, 0, 0, 0),
        SecuritySnapshot(now - (20 * 86400), 80, 50, 5, 3, 1, 0, 0),
        SecuritySnapshot(now - (10 * 86400), 70, 50, 10, 6, 2, 1, 0),
        SecuritySnapshot(now, 60, 50, 15, 8, 3, 2, 1),
    ]

    analysis = tracker.get_trend_analysis(days=30)

    assert analysis["status"] == "success"
    assert analysis["trend"] == "declining"
    assert analysis["score_change"] == -30  # 60 - 90


def test_trend_analysis_stable(temp_history_file):
    """Test trend analysis with stable scores."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add stable snapshots
    tracker._snapshots = [
        SecuritySnapshot(now - (30 * 86400), 80, 50, 5, 3, 1, 0, 0),
        SecuritySnapshot(now, 82, 50, 5, 3, 1, 0, 0),
    ]

    analysis = tracker.get_trend_analysis(days=30)

    assert analysis["status"] == "success"
    assert analysis["trend"] == "stable"
    assert -5 <= analysis["score_change"] <= 5


def test_trend_analysis_insufficient_data(temp_history_file):
    """Test trend analysis with insufficient data."""
    tracker = SecurityTrendTracker(temp_history_file)

    # Only one snapshot
    tracker._snapshots = [
        SecuritySnapshot(int(time.time()), 80, 50, 5, 3, 1, 0, 0),
    ]

    analysis = tracker.get_trend_analysis(days=30)

    assert analysis["status"] == "insufficient_data"
    assert analysis["snapshot_count"] == 1


def test_improvement_rate(temp_history_file):
    """Test calculating improvement rate."""
    tracker = SecurityTrendTracker(temp_history_file)

    now = int(time.time())

    # Add snapshots 30 days apart with 30 point improvement
    tracker._snapshots = [
        SecuritySnapshot(now - (30 * 86400), 60, 50, 15, 8, 3, 2, 1),
        SecuritySnapshot(now, 90, 50, 2, 1, 0, 0, 0),
    ]

    rate = tracker.get_improvement_rate(days=30)

    # Should be approximately 1 point per day
    assert rate is not None
    assert 0.9 <= rate <= 1.1


def test_improvement_rate_insufficient_data(temp_history_file):
    """Test improvement rate with insufficient data."""
    tracker = SecurityTrendTracker(temp_history_file)

    # No snapshots
    rate = tracker.get_improvement_rate(days=30)
    assert rate is None


def test_clear_history(temp_history_file):
    """Test clearing historical data."""
    tracker = SecurityTrendTracker(temp_history_file)

    # Add some snapshots
    tracker.record_snapshot(85, 50, 5, 3, 1, 2, 0)
    tracker.record_snapshot(90, 50, 3, 2, 0, 1, 0)

    assert len(tracker.get_snapshots()) == 2

    # Clear history
    tracker.clear_history()

    assert len(tracker.get_snapshots()) == 0
    assert temp_history_file.exists()  # File still exists, just empty


def test_get_trend_tracker_singleton():
    """Test that get_trend_tracker returns singleton."""
    tracker1 = get_trend_tracker()
    tracker2 = get_trend_tracker()

    assert tracker1 is tracker2


def test_record_audit_snapshot():
    """Test recording audit results as snapshot."""
    audit_results = {
        "score": 85,
        "timestamp": int(time.time()),
        "issues": {
            "weak_passwords": [{"id": 1}, {"id": 2}],
            "reused_passwords": [{"id": 3}],
            "breached_passwords": [{"id": 4}],
            "expired_passwords": [{"id": 5}],
            "duplicate_passwords": [],
        },
    }

    snapshot = record_audit_snapshot(audit_results)

    assert snapshot.score == 85
    assert snapshot.weak_count == 2
    assert snapshot.reused_count == 1
    assert snapshot.breached_count == 1
    assert snapshot.expired_count == 1
    assert snapshot.duplicate_count == 0
