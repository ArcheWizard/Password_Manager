"""Security score trending and historical analysis.

This module tracks security scores over time and provides historical analysis
to help users understand how their vault security is improving or degrading.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from secure_password_manager.utils.logger import log_info
from secure_password_manager.utils.paths import get_data_dir


@dataclass
class SecuritySnapshot:
    """A point-in-time snapshot of vault security metrics."""

    timestamp: int
    score: int
    total_passwords: int
    weak_count: int
    reused_count: int
    breached_count: int
    expired_count: int
    duplicate_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecuritySnapshot:
        """Create from dictionary."""
        return cls(**data)


class SecurityTrendTracker:
    """Tracks security scores over time."""

    def __init__(self, history_file: Optional[Path] = None):
        """Initialize the trend tracker.

        Args:
            history_file: Path to history JSON file. Defaults to security_history.json in data dir.
        """
        if history_file is None:
            history_file = get_data_dir() / "security_history.json"

        self.history_file = history_file
        self._snapshots: List[SecuritySnapshot] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load historical snapshots from disk."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, "r") as f:
                data = json.load(f)
                self._snapshots = [
                    SecuritySnapshot.from_dict(snap) for snap in data.get("snapshots", [])
                ]
            log_info(f"Loaded {len(self._snapshots)} security snapshots from history")
        except Exception as e:
            log_info(f"Failed to load security history: {e}")
            self._snapshots = []

    def _save_history(self) -> None:
        """Save historical snapshots to disk."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(
                    {"snapshots": [snap.to_dict() for snap in self._snapshots]},
                    f,
                    indent=2,
                )
        except Exception as e:
            log_info(f"Failed to save security history: {e}")

    def record_snapshot(
        self,
        score: int,
        total_passwords: int,
        weak_count: int,
        reused_count: int,
        breached_count: int,
        expired_count: int,
        duplicate_count: int,
    ) -> SecuritySnapshot:
        """Record a new security snapshot.

        Args:
            score: Security score (0-100)
            total_passwords: Total number of passwords
            weak_count: Number of weak passwords
            reused_count: Number of reused passwords
            breached_count: Number of breached passwords
            expired_count: Number of expired passwords
            duplicate_count: Number of duplicate entries

        Returns:
            The created snapshot
        """
        snapshot = SecuritySnapshot(
            timestamp=int(time.time()),
            score=score,
            total_passwords=total_passwords,
            weak_count=weak_count,
            reused_count=reused_count,
            breached_count=breached_count,
            expired_count=expired_count,
            duplicate_count=duplicate_count,
        )

        self._snapshots.append(snapshot)
        self._save_history()

        log_info(f"Recorded security snapshot: score={score}, total={total_passwords}")
        return snapshot

    def get_snapshots(
        self, days: Optional[int] = None, limit: Optional[int] = None
    ) -> List[SecuritySnapshot]:
        """Get historical snapshots.

        Args:
            days: Only return snapshots from the last N days
            limit: Maximum number of snapshots to return (most recent)

        Returns:
            List of security snapshots
        """
        snapshots = self._snapshots

        # Filter by days
        if days is not None:
            cutoff = int(time.time()) - (days * 86400)
            snapshots = [s for s in snapshots if s.timestamp >= cutoff]

        # Apply limit
        if limit is not None:
            snapshots = snapshots[-limit:]

        return snapshots

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze security trends over a period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing trend analysis
        """
        snapshots = self.get_snapshots(days=days)

        if len(snapshots) < 2:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 2 snapshots in {days} days for trend analysis",
                "snapshot_count": len(snapshots),
            }

        first = snapshots[0]
        last = snapshots[-1]

        # Calculate changes
        score_change = last.score - first.score
        weak_change = last.weak_count - first.weak_count
        reused_change = last.reused_count - first.reused_count
        breached_change = last.breached_count - first.breached_count

        # Determine trend direction
        if score_change > 5:
            trend = "improving"
        elif score_change < -5:
            trend = "declining"
        else:
            trend = "stable"

        # Calculate average score
        avg_score = sum(s.score for s in snapshots) / len(snapshots)

        return {
            "status": "success",
            "period_days": days,
            "snapshot_count": len(snapshots),
            "trend": trend,
            "score_change": score_change,
            "current_score": last.score,
            "previous_score": first.score,
            "average_score": round(avg_score, 1),
            "changes": {
                "weak_passwords": weak_change,
                "reused_passwords": reused_change,
                "breached_passwords": breached_change,
            },
            "first_snapshot": first.to_dict(),
            "last_snapshot": last.to_dict(),
        }

    def get_improvement_rate(self, days: int = 30) -> Optional[float]:
        """Calculate rate of security improvement.

        Args:
            days: Number of days to analyze

        Returns:
            Points per day improvement rate, or None if insufficient data
        """
        snapshots = self.get_snapshots(days=days)

        if len(snapshots) < 2:
            return None

        first = snapshots[0]
        last = snapshots[-1]

        time_diff_days = (last.timestamp - first.timestamp) / 86400
        if time_diff_days < 1:
            return None

        score_diff = last.score - first.score
        return score_diff / time_diff_days

    def clear_history(self) -> None:
        """Clear all historical snapshots."""
        self._snapshots = []
        self._save_history()
        log_info("Cleared security history")


# Global tracker instance
_tracker: Optional[SecurityTrendTracker] = None


def get_trend_tracker() -> SecurityTrendTracker:
    """Get the global security trend tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SecurityTrendTracker()
    return _tracker


def record_audit_snapshot(audit_results: Dict[str, Any]) -> SecuritySnapshot:
    """Record a security audit as a historical snapshot.

    Args:
        audit_results: Results from run_security_audit()

    Returns:
        The created snapshot
    """
    tracker = get_trend_tracker()

    issues = audit_results["issues"]

    return tracker.record_snapshot(
        score=audit_results["score"],
        total_passwords=len(issues.get("weak_passwords", []))
        + len(issues.get("reused_passwords", []))
        + len(issues.get("breached_passwords", [])),
        weak_count=len(issues.get("weak_passwords", [])),
        reused_count=len(issues.get("reused_passwords", [])),
        breached_count=len(issues.get("breached_passwords", [])),
        expired_count=len(issues.get("expired_passwords", [])),
        duplicate_count=len(issues.get("duplicate_passwords", [])),
    )
