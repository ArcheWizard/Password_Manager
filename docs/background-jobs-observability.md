# Background Jobs & Observability

Blueprint for scheduled tasks, telemetry, and diagnostics in Secure Password Manager.

**Implementation Status**: This document outlines planned features for future releases. As of v1.10.0, background job scheduling is not yet implemented; the application focuses on interactive CLI/GUI workflows with browser extension integration.

## Objectives

- Automate maintenance (breach cache refresh, rotation reminders, backup verification).
- Provide actionable metrics/logs for both users and operators.
- Keep sensitive data out of telemetry streams.

## Job Runner Design

- Embedded scheduler within the desktop app (initial) with cron-like configuration.
- Future standalone daemon/service for headless environments.
- Jobs defined as Python callables registered in a job registry.

### Default Jobs

| Job | Frequency | Description |
| --- | --- | --- |
| `breach_cache_refresh` | Every 6 hours | Refresh HIBP prefix cache; respect API rate limits. |
| `expiring_password_digest` | Daily | Summarize upcoming expirations and display notification. |
| `backup_integrity_check` | Weekly | Run `PRAGMA integrity_check`, verify latest backups’ hashes. |
| `log_rotation` | Weekly | Rotate `password_manager.log`, compress archives. |
| `browser_bridge_health` (planned) | Hourly | Ensure IPC server is reachable from extensions. |

### Job Lifecycle

1. Scheduler loads jobs + cron expressions from `settings.json` (planned).
2. Each job runs in a worker thread with a timeout.
3. Results recorded in `logs/jobs.log` and optionally surfaced in the UI.
4. Failures trigger notifications and optional retries (exponential backoff).

## Metrics & Logging

- **Structured Logging**: JSON lines with fields (`ts`, `level`, `component`, `event`, `entry_id_hash`).
- **Metrics Sink** (planned): optional Prometheus exporter or statsd client publishing counts and durations.
- **Event Tracing**: unique correlation IDs per user action to trace across logs.

## Observability Dashboard (Planned)

- GUI tab summarizing job status, next run, last result.
- CLI command `password-manager --jobs status` to dump JSON.
- Status badges: OK, WARN, FAIL.

## Alerting Hooks

- Integrate with system notifications for job failures.
- Webhook plugin interface (future) to notify Slack/Teams/email.
- Configurable thresholds (e.g., backup job fails twice ⇒ escalate).

## Diagnostics Toolkit

1. `password-manager --doctor`
   - Runs environment checks (Python version, dependencies, Qt plugins).
   - Validates file permissions and disk space.
   - Summarizes latest job results.
2. `password-manager --logs bundle`
   - Zips logs, manifests, and recent config for support attachments.

## Data Retention

- Keep job logs for 30 days by default.
- Compress archives older than 7 days.
- Provide `password-manager --logs purge --days 30` command (planned).

## Privacy Considerations

- Metrics/logs never include plaintext secrets or master password hints.
- Identifiers hashed with SHA-256 and truncated to preserve anonymity while allowing correlation.
- Opt-in toggle for telemetry modules that leave the local machine.

## Future Enhancements

- Distributed scheduler for multi-device sync scenarios.
- Adaptive scheduling that shortens intervals when risk increases (e.g., new breach report).
- Integration with the browser extension to display job outcomes inside the extension UI.
